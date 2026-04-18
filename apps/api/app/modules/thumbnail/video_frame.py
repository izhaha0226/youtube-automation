"""Capture candidate thumbnail frames from a rendered video via ffmpeg.

Strategy:
- Sample frames evenly across the video (excluding first/last 5%)
- Score each by brightness + saturation + edge density (all simple numpy)
- Return top-K as candidate thumbnails
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from app.core.logging import get_logger

log = get_logger(__name__)


def capture_candidates(video_path: str, out_dir: Path, count: int = 5) -> list[str]:
    if not shutil.which("ffmpeg"):
        log.warning("video.ffmpeg.missing")
        return []
    video = Path(video_path)
    if not video.exists():
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    dur = _duration(video)
    if dur <= 0:
        return []

    # Sample timestamps: skip first/last 5%
    start = dur * 0.05
    end = dur * 0.95
    sample_count = max(count * 3, 9)
    step = (end - start) / sample_count
    stamps = [start + step * i for i in range(sample_count)]

    raw_frames: list[Path] = []
    for i, t in enumerate(stamps):
        out = out_dir / f"frame_{i:02d}.jpg"
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{t:.3f}",
            "-i",
            str(video),
            "-vframes",
            "1",
            "-q:v",
            "2",
            "-vf",
            "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
            "-loglevel",
            "error",
            str(out),
        ]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0 and out.exists():
            raw_frames.append(out)

    # Score and pick top-K
    scored = [(_score(p), p) for p in raw_frames]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [str(p) for _, p in scored[:count]]
    log.info("video.frames.captured", total=len(raw_frames), kept=len(top))
    return top


def _duration(path: Path) -> float:
    try:
        r = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
        return float(json.loads(r.stdout).get("format", {}).get("duration", 0))
    except Exception:
        return 0


def _score(p: Path) -> float:
    try:
        img = Image.open(p).convert("RGB")
        px = list(img.resize((160, 90)).getdata())
        n = len(px)
        brightness = sum(sum(c) / 3 for c in px) / n / 255
        sat = sum((max(c) - min(c)) for c in px) / n / 255
        # penalize too dark or too washed
        dark_pen = 1 - abs(brightness - 0.55) * 2
        return max(0.0, dark_pen) + sat * 1.2
    except Exception:
        return 0
