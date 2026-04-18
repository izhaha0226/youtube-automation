#!/usr/bin/env python3
"""Obsidian <-> Workspace 동기화 CLI.

Usage:
  python scripts/sync_obsidian.py --run-id <id>
  python scripts/sync_obsidian.py --all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.config import settings  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.modules.sync.obsidian import mirror_to_workspace  # noqa: E402

log = get_logger(__name__)


def sync_run(run_id: str) -> None:
    obsidian_base = Path(settings.obsidian_vault) / "notes" / "auto"
    workspace_base = ROOT / "data"

    for sub in ("scenarios", "narrations", "subtitles", "thumbnails", "packages"):
        src_dir = obsidian_base / sub
        if not src_dir.exists():
            continue
        for f in src_dir.iterdir():
            if run_id in f.name:
                dst = workspace_base / sub / f.name
                mirror_to_workspace(f, dst)


def sync_all() -> None:
    obsidian_base = Path(settings.obsidian_vault) / "notes" / "auto"
    workspace_base = ROOT / "data"

    for sub in ("scenarios", "narrations", "subtitles", "thumbnails", "packages"):
        src_dir = obsidian_base / sub
        if not src_dir.exists():
            continue
        for f in src_dir.iterdir():
            if f.is_file():
                dst = workspace_base / sub / f.name
                mirror_to_workspace(f, dst)


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Obsidian <-> Workspace sync")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-id", help="특정 run ID 동기화")
    group.add_argument("--all", action="store_true", help="전체 동기화")
    args = parser.parse_args()

    if args.all:
        sync_all()
    else:
        sync_run(args.run_id)

    log.info("sync complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
