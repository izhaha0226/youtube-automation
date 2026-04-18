from __future__ import annotations

from pathlib import Path

from app.core.config import ROOT

PROMPT_DIR = ROOT / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPT_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def render(template: str, **vars) -> str:
    out = template
    for k, v in vars.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out
