#!/usr/bin/env python3
"""CLI entry point for autonomous E2E pipeline.

Usage:
  python scripts/run_pipeline.py --intent "금리 변화가 집값에 주는 영향" --auto
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.db import init_db  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.modules.pipeline import run_full_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", required=True, help="한 줄 의도")
    parser.add_argument("--avoid", nargs="*", default=[], help="피할 키워드")
    parser.add_argument("--must", nargs="*", default=[], help="반드시 포함")
    parser.add_argument("--auto", action="store_true", help="YouTube 자동 업로드")
    args = parser.parse_args()

    configure_logging()
    init_db()
    log = get_logger("cli")
    log.info("cli.start", intent=args.intent, auto=args.auto)

    result = run_full_pipeline(
        intent=args.intent,
        avoid_keywords=args.avoid,
        must_include=args.must,
        auto_upload=args.auto,
    )
    print(json.dumps({"run_id": result["run_id"], "topic": result["topic"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
