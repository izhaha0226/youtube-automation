from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from app.core.config import settings


def slugify(text: str, limit: int = 40) -> str:
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"[^\w\-가-힣]", "", text)
    return text[:limit] or "untitled"


def run_id(topic: str) -> str:
    return f"{datetime.now().strftime('%Y%m%d-%H%M')}_{slugify(topic)}"


def workspace_dir(run: str, kind: str) -> Path:
    d = settings.data_dir / kind / run
    d.mkdir(parents=True, exist_ok=True)
    return d


def obsidian_dir(sub: str) -> Path:
    root = Path(settings.obsidian_vault) / "notes" / "auto"
    d = root / sub
    d.mkdir(parents=True, exist_ok=True)
    return d
