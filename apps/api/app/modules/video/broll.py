"""B-roll image generation for each scenario section using Fal.ai."""
from __future__ import annotations

import os
from pathlib import Path

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas import ScenarioOutput

log = get_logger(__name__)

# Section → visual concept mapping for Korean economy/real-estate content
_VISUAL_PROMPTS = {
    "hook": (
        "dramatic cinematic wide shot, Seoul city skyline at golden hour, "
        "dramatic storm clouds gathering, high contrast, moody atmosphere, "
        "editorial photography, 16:9, photorealistic 8k"
    ),
    "body": (
        "Korean apartment complex aerial view, modern highrise buildings, "
        "warm cinematic lighting, data visualization overlay aesthetic, "
        "editorial documentary style, 16:9, photorealistic 8k"
    ),
    "chart": (
        "minimalist financial chart on dark background, glowing red and blue lines, "
        "interest rate graph, sharp focus, premium editorial, 16:9, 8k"
    ),
    "conclusion": (
        "Korean family looking at apartment, warm sunset backlight, hopeful mood, "
        "editorial lifestyle photography, 16:9, photorealistic 8k"
    ),
}

_NEGATIVE = (
    "cartoon, illustration, 3d render, flat, low quality, blurry, "
    "text, watermark, logo, ugly, deformed"
)

_MODEL = "fal-ai/flux-pro/v1.1-ultra"


def generate_broll(
    run_id: str,
    scenario: ScenarioOutput,
    out_dir: Path,
) -> list[str]:
    if not settings.fal_key:
        log.warning("broll.skip", reason="no fal_key")
        return []

    os.environ["FAL_KEY"] = settings.fal_key
    import fal_client

    sections = _build_sections(scenario)
    paths: list[str] = []

    for idx, (label, prompt) in enumerate(sections):
        out_path = out_dir / f"broll_{idx:02d}_{label}.png"
        try:
            res = fal_client.subscribe(
                _MODEL,
                arguments={
                    "prompt": prompt,
                    "negative_prompt": _NEGATIVE,
                    "image_size": {"width": 1280, "height": 720},
                    "num_images": 1,
                    "enable_safety_checker": True,
                },
            )
            imgs = res.get("images") or []
            if not imgs:
                continue
            url = imgs[0].get("url")
            if not url:
                continue
            data = httpx.get(url, timeout=60).content
            out_path.write_bytes(data)
            paths.append(str(out_path))
            log.info("broll.done", idx=idx, label=label)
        except Exception as e:
            log.warning("broll.error", idx=idx, label=label, error=str(e))

    return paths


def _build_sections(scenario: ScenarioOutput) -> list[tuple[str, str]]:
    """Return (label, enriched_prompt) pairs for each video section."""
    sections: list[tuple[str, str]] = []

    # Hook
    sections.append(("hook", _enrich(_VISUAL_PROMPTS["hook"], scenario.hook)))

    # Body — one image per 2 body items
    for i in range(0, len(scenario.body), 2):
        chunk = " ".join(scenario.body[i : i + 2])
        base = _VISUAL_PROMPTS["chart"] if i % 4 == 2 else _VISUAL_PROMPTS["body"]
        sections.append((f"body_{i // 2}", _enrich(base, chunk)))

    # Conclusion
    sections.append(("conclusion", _enrich(_VISUAL_PROMPTS["conclusion"], scenario.conclusion)))

    return sections


def _enrich(base_prompt: str, context: str) -> str:
    # Keep context short — just enough to guide visual mood
    snippet = context[:80].replace("\n", " ")
    return f"{base_prompt}. Context: {snippet}"
