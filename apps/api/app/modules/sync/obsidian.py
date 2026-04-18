from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


def write_obsidian(sub: str, filename: str, content: str) -> Path:
    """Obsidian first, then Workspace sync handled by caller."""
    base = Path(settings.obsidian_vault) / "notes" / "auto" / sub
    base.mkdir(parents=True, exist_ok=True)
    p = base / filename
    p.write_text(content, encoding="utf-8")
    log.info("sync.obsidian", path=str(p))
    return p


def write_obsidian_json(sub: str, filename: str, data: dict) -> Path:
    return write_obsidian(sub, filename, json.dumps(data, ensure_ascii=False, indent=2))


def mirror_to_workspace(obsidian_path: Path, workspace_path: Path) -> None:
    workspace_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(obsidian_path, workspace_path)
    log.info("sync.mirror", src=str(obsidian_path), dst=str(workspace_path))
