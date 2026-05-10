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
    text_ko = data.get("text_ko", "")
    sentences = data.get("sentences", [])

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
    for idx, (s, l) in enumerate(zip(sentences, lens)):
        dur = int((l / total_chars) * total_sec * 1000)
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
