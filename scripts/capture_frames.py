#!/usr/bin/env python3
"""CLI: capture thumbnail-candidate frames from a video.

Usage:
  python scripts/capture_frames.py <video.mp4> --out data/thumbnails/<run>/frames --count 5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.modules.thumbnail.video_frame import capture_candidates  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", default="data/thumbnails/frames")
    ap.add_argument("--count", type=int, default=5)
    args = ap.parse_args()

    frames = capture_candidates(args.video, Path(args.out), count=args.count)
    for f in frames:
        print(f)
    return 0 if frames else 1


if __name__ == "__main__":
    raise SystemExit(main())
