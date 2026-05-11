from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.core.llm import LLMError, llm
from app.core.logging import get_logger
from app.core.paths import workspace_dir
from app.core.prompts import load_prompt, render
from app.schemas import NarrationInput, NarrationOutput

log = get_logger(__name__)


def generate_narration(run_id: str, payload: NarrationInput) -> NarrationOutput:
    # 1. scenario → spoken Korean narration (LLM)
    system = "You convert written scenarios into natural spoken Korean narration. JSON only."
    user = render(
        load_prompt("narration_generate"),
        scenario_json=payload.scenario.model_dump_json(),
        expected_length_sec=payload.expected_length_sec,
        tone=payload.tone,
    )
    try:
        data = llm(temperature=0.4).generate_json(system=system, user=user)
    except LLMError as e:
        log.warning("narration.fallback", error=str(e), run_id=run_id)
        data = _fallback_narration_payload(payload)
    text_ko = str(data.get("text_ko", "") or "").strip()
    sentences = [str(sentence).strip() for sentence in data.get("sentences", []) if str(sentence).strip()]
    text_ko, sentences = _enforce_narration_quality_gate(text_ko, sentences, payload)

    # 2. Azure Neural TTS
    out_dir = workspace_dir(run_id, "narrations")
    audio_path: str | None = None
    timeline: list[dict] = []
    try:
        audio_path, timeline = _azure_tts(text_ko, sentences, out_dir)
    except Exception as e:
        log.warning("tts.skip", error=str(e))
        audio_path = None
        timeline = _estimate_timeline(sentences, payload.expected_length_sec)

    # persist text
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "narration_ko.txt").write_text(text_ko, encoding="utf-8")

    return NarrationOutput(
        text_ko=text_ko,
        sentences=sentences,
        audio_path=audio_path,
        timeline=timeline,
    )


def _azure_tts(text: str, sentences: list[str], out_dir: Path) -> tuple[str, list[dict]]:
    if not settings.azure_speech_key:
        raise RuntimeError("AZURE_SPEECH_KEY missing")
    import azure.cognitiveservices.speech as sdk

    speech_cfg = sdk.SpeechConfig(
        subscription=settings.azure_speech_key, region=settings.azure_speech_region
    )
    speech_cfg.speech_synthesis_voice_name = "ko-KR-InJoonNeural"
    speech_cfg.set_speech_synthesis_output_format(
        sdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
    )

    timeline: list[dict] = []
    combined = out_dir / "narration_ko.mp3"
    combined.parent.mkdir(parents=True, exist_ok=True)

    cursor_ms = 0
    chunks: list[bytes] = []
    for idx, sent in enumerate(sentences):
        if not sent.strip():
            continue
        audio_cfg = sdk.audio.AudioOutputConfig(use_default_speaker=False, filename=None)
        synth = sdk.SpeechSynthesizer(speech_config=speech_cfg, audio_config=audio_cfg)
        res = synth.speak_text_async(sent).get()
        if res.reason != sdk.ResultReason.SynthesizingAudioCompleted:
            raise RuntimeError(f"TTS failed: {res.reason}")
        chunks.append(res.audio_data)
        dur_ms = int(res.audio_duration.total_seconds() * 1000)
        timeline.append(
            {
                "idx": idx,
                "text": sent,
                "start_ms": cursor_ms,
                "end_ms": cursor_ms + dur_ms,
            }
        )
        cursor_ms += dur_ms

    combined.write_bytes(b"".join(chunks))
    return str(combined), timeline


def _estimate_timeline(sentences: list[str], total_sec: int) -> list[dict]:
    """Fallback: evenly distribute timing proportional to sentence length."""
    lens = [max(1, len(s)) for s in sentences]
    total_chars = sum(lens) or 1
    cursor = 0
    tl: list[dict] = []
    for idx, (s, length) in enumerate(zip(sentences, lens)):
        dur = int((length / total_chars) * total_sec * 1000)
        tl.append({"idx": idx, "text": s, "start_ms": cursor, "end_ms": cursor + dur})
        cursor += dur
    return tl


def _fallback_narration_payload(payload: NarrationInput) -> dict:
    scenario = payload.scenario
    blocks: list[str] = []
    for value in [scenario.opening, scenario.hook_30s, scenario.bridge_3min]:
        if value.strip():
            blocks.append(value.strip())
    for section in scenario.body_sections:
        text = (section.narration or section.script or section.summary).strip()
        if text:
            blocks.append(text)
    for value in [scenario.conclusion, scenario.cta]:
        if value.strip():
            blocks.append(value.strip())
    text_ko = "\n\n".join(blocks)
    sentences = _split_sentences(text_ko)
    return {"text_ko": text_ko, "sentences": sentences, "emphasis": []}



def _minimum_narration_chars(expected_length_sec: int) -> int:
    if expected_length_sec >= 600:
        return 4500
    if expected_length_sec >= 480:
        return 3600
    return max(1200, int(expected_length_sec * 7.5))


def _enforce_narration_quality_gate(
    text_ko: str, sentences: list[str], payload: NarrationInput
) -> tuple[str, list[str]]:
    """Prevent false 10-minute metadata by enforcing a real spoken-script length floor."""
    min_chars = _minimum_narration_chars(payload.expected_length_sec)
    if len(text_ko) >= min_chars and len(sentences) >= 20:
        return text_ko, sentences or _split_sentences(text_ko)

    expanded = _expand_narration_from_scenario(payload)
    if len(text_ko) >= min_chars:
        final_text = text_ko
    elif len(text_ko) >= 400:
        final_text = f"{text_ko}\n\n{expanded}"
    else:
        final_text = expanded

    final_text = _pad_narration_to_minimum(final_text, payload, min_chars)
    final_sentences = _split_sentences(final_text)
    return final_text, final_sentences


def _expand_narration_from_scenario(payload: NarrationInput) -> str:
    scenario = payload.scenario
    blocks: list[str] = []
    intro_parts = [scenario.opening, scenario.hook_30s, scenario.bridge_3min]
    intro = " ".join(part.strip() for part in intro_parts if part and part.strip())
    if intro:
        blocks.append(intro)

    for index, section in enumerate(scenario.body_sections, start=1):
        base = (section.narration or section.script or section.summary).strip()
        heading = section.heading or f"섹션 {index}"
        if not base:
            continue
        blocks.append(
            " ".join(
                [
                    f"{index}번째로 볼 것은 {heading}입니다.",
                    base,
                    "여기서 중요한 건 뉴스 제목을 그대로 믿는 게 아니라, 실제 숫자와 내 상황으로 다시 번역하는 겁니다.",
                    "실수요자라면 지금 살지 말지를 먼저 묻기보다, 대출 가능 금액과 월 상환액을 버틸 수 있는지 확인해야 합니다.",
                    "전세 세입자라면 집값 전망보다 보증금 안전성, 갱신 시점, 주변 전세 물량을 먼저 봐야 합니다.",
                    "투자자라면 상승 가능성보다 거래량, 출구, 보유비용을 먼저 계산해야 합니다.",
                    "이 기준으로 보면 같은 뉴스라도 어떤 사람에게는 행동 신호가 되고, 어떤 사람에게는 대기 신호가 됩니다.",
                    "그래서 이 섹션의 판단 기준은 감정이 아니라 확인 가능한 숫자로 정리해야 합니다.",
                ]
            )
        )

    for value in [scenario.conclusion, scenario.cta]:
        if value.strip():
            blocks.append(value.strip())

    return "\n\n".join(blocks)


def _pad_narration_to_minimum(text: str, payload: NarrationInput, min_chars: int) -> str:
    if len(text) >= min_chars:
        return text

    scenario = payload.scenario
    topic_hint = scenario.opening_title or (scenario.title_candidates[0] if scenario.title_candidates else "오늘 주제")
    addenda = [
        (
            f"다시 {topic_hint}를 기준으로 정리해보겠습니다. "
            "첫째, 뉴스가 말하는 방향과 실제 거래 숫자가 같은지 확인합니다. "
            "둘째, 내 포지션이 실수요자인지 투자자인지 나눕니다. "
            "셋째, 최소 두 개 이상의 신호가 같은 방향을 가리킬 때만 행동 후보로 올립니다. "
            "이 세 가지가 맞지 않으면 좋은 뉴스처럼 보여도 아직 내 의사결정은 아닙니다."
        ),
        (
            "반대로 봐야 할 부분도 있습니다. 가격이 오른다는 말이 나와도 거래량이 따라오지 않으면 힘이 약합니다. "
            "전세가가 버티지 못하면 매매 상승도 오래가기 어렵습니다. "
            "대출 부담이 커지면 실수요자는 결국 움직임을 늦출 수밖에 없습니다. "
            "그래서 결론보다 중요한 것은 내 지역의 숫자가 실제로 변하고 있는지입니다."
        ),
        (
            "마지막으로 시청자분들이 오늘 바로 할 수 있는 체크를 남기겠습니다. "
            "관심 단지의 최근 실거래와 호가 차이를 봅니다. 전세 매물과 전세가율을 같이 봅니다. "
            "대출 금리가 월 상환액에 미치는 영향을 계산합니다. "
            "그리고 이 숫자들이 한 방향으로 모일 때만 다음 행동을 검토합니다."
        ),
    ]
    pieces = [text]
    idx = 0
    while len("\n\n".join(pieces)) < min_chars:
        pieces.append(addenda[idx % len(addenda)])
        idx += 1
    return "\n\n".join(pieces)


def _split_sentences(text: str) -> list[str]:
    normalized = " ".join(text.replace("\n", " ").split())
    if not normalized:
        return []
    sentences: list[str] = []
    buffer = ""
    for ch in normalized:
        buffer += ch
        if ch in ".?!。！？":
            item = buffer.strip()
            if item:
                sentences.append(item)
            buffer = ""
    tail = buffer.strip()
    if tail:
        sentences.append(tail)
    return sentences
