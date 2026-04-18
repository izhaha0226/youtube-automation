from __future__ import annotations

import json
from pathlib import Path

from app.core.llm import llm
from app.core.logging import get_logger
from app.core.paths import workspace_dir
from app.core.prompts import load_prompt, render
from app.schemas import NarrationOutput, SubtitleOutput

log = get_logger(__name__)

LANG_NAME = {"ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese (Simplified)"}


def generate_subtitles(run_id: str, narration: NarrationOutput) -> list[SubtitleOutput]:
    out_dir = workspace_dir(run_id, "subtitles")
    results: list[SubtitleOutput] = []

    # KO base from timeline
    ko_srt = _build_srt(narration.sentences, narration.timeline)
    ko_srt_path = out_dir / "subtitles_ko.srt"
    ko_srt_path.write_text(ko_srt, encoding="utf-8")
    ko_json_path = out_dir / "subtitles_ko.json"
    ko_json_path.write_text(
        json.dumps({"lang": "ko", "sentences": narration.sentences}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    results.append(SubtitleOutput(lang="ko", srt_path=str(ko_srt_path), json_path=str(ko_json_path)))

    for lang in ("en", "ja", "zh"):
        translated = _translate(narration.sentences, lang)
        srt = _build_srt(translated, narration.timeline)
        srt_path = out_dir / f"subtitles_{lang}.srt"
        srt_path.write_text(srt, encoding="utf-8")
        json_path = out_dir / f"subtitles_{lang}.json"
        json_path.write_text(
            json.dumps({"lang": lang, "sentences": translated}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        results.append(SubtitleOutput(lang=lang, srt_path=str(srt_path), json_path=str(json_path)))

    log.info("subtitle.done", count=len(results))
    return results


def _translate(sentences: list[str], lang: str) -> list[str]:
    system = "You are a professional localization subtitle translator. JSON only."
    user = render(
        load_prompt("subtitle_translate"),
        target_lang_name=LANG_NAME[lang],
        lang_code=lang,
        sentences_json=json.dumps(sentences, ensure_ascii=False),
    )
    data = llm(temperature=0.3).generate_json(system=system, user=user)
    out = data.get("sentences", [])
    if len(out) != len(sentences):
        # best effort pad/truncate to keep timeline alignment
        out = (out + [""] * len(sentences))[: len(sentences)]
    return out


def _build_srt(sentences: list[str], timeline: list[dict]) -> str:
    lines = []
    for i, (s, t) in enumerate(zip(sentences, timeline), start=1):
        lines.append(str(i))
        lines.append(f"{_ts(t['start_ms'])} --> {_ts(t['end_ms'])}")
        lines.append(s)
        lines.append("")
    return "\n".join(lines)


def _ts(ms: int) -> str:
    h = ms // 3_600_000
    m = (ms % 3_600_000) // 60_000
    s = (ms % 60_000) // 1000
    rem = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{rem:03d}"
