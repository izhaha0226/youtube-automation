"""Assemble B-roll images + narration audio → final .mp4 using ffmpeg.

Strategy:
- Each image is held for its corresponding narration segment duration
- Ken Burns zoom effect per image for dynamic feel
- Crossfade transitions between images
- Subtitle burn-in (optional, from SRT file)
- Audio: narration mp3, no background music (added in post)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.logging import get_logger
from app.schemas import NarrationOutput, VideoOutput

log = get_logger(__name__)

THUMB_W, THUMB_H = 1280, 720
CROSSFADE_SEC = 0.5
MIN_SLIDE_SEC = 3.0


def assemble_video(
    run_id: str,
    narration: NarrationOutput,
    broll_paths: list[str],
    out_dir: Path,
    subtitle_path: str | None = None,
) -> VideoOutput:
    if not shutil.which("ffmpeg"):
        log.warning("video.ffmpeg.missing")
        return VideoOutput(video_path=None, duration_sec=0, slide_count=0)

    if not narration.audio_path or not Path(narration.audio_path).exists():
        log.warning("video.no_audio")
        return VideoOutput(video_path=None, duration_sec=0, slide_count=0)

    if not broll_paths:
        log.warning("video.no_broll")
        return VideoOutput(video_path=None, duration_sec=0, slide_count=0)

    out_dir.mkdir(parents=True, exist_ok=True)
    durations = _compute_durations(narration.timeline, len(broll_paths))
    total_sec = sum(durations)

    # Build ffmpeg concat + filter complex
    raw_path = out_dir / "video_raw.mp4"
    _build_slideshow(broll_paths, durations, narration.audio_path, raw_path)

    # Optionally burn subtitles
    final_path = out_dir / "video_final.mp4"
    if subtitle_path and Path(subtitle_path).exists():
        _burn_subtitles(raw_path, subtitle_path, final_path)
        raw_path.unlink(missing_ok=True)
    else:
        raw_path.rename(final_path)

    log.info("video.assembled", path=str(final_path), duration=total_sec, slides=len(broll_paths))
    return VideoOutput(
        video_path=str(final_path),
        duration_sec=round(total_sec, 1),
        slide_count=len(broll_paths),
    )


def _compute_durations(timeline: list[dict], n_slides: int) -> list[float]:
    if not timeline or n_slides == 0:
        return [10.0] * n_slides

    total_ms = max(e.get("end_ms", 0) for e in timeline) if timeline else 0
    total_sec = total_ms / 1000 or n_slides * 10.0

    # Distribute proportionally, minimum MIN_SLIDE_SEC per slide
    base = total_sec / n_slides
    durations = [max(MIN_SLIDE_SEC, base)] * n_slides

    # Re-normalize so total matches audio length
    factor = total_sec / sum(durations)
    durations = [d * factor for d in durations]
    return durations


def _build_slideshow(
    images: list[str],
    durations: list[float],
    audio_path: str,
    out_path: Path,
) -> None:
    n = len(images)

    # Write concat demuxer file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        concat_file = f.name
        for img, dur in zip(images, durations):
            f.write(f"file '{img}'\n")
            f.write(f"duration {dur:.3f}\n")
        # ffmpeg concat needs the last file listed again without duration
        f.write(f"file '{images[-1]}'\n")

    # Scale + Ken Burns filter per image
    filter_parts: list[str] = []
    for i, dur in enumerate(durations):
        frames = max(1, int(dur * 25))
        # Alternating zoom in / zoom out
        if i % 2 == 0:
            zoom_expr = f"'min(zoom+0.0004,1.05)'"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        else:
            zoom_expr = f"'if(eq(on,1),1.05,max(1,zoom-0.0004))'"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        filter_parts.append(
            f"[{i}:v]scale={THUMB_W}:{THUMB_H}:force_original_aspect_ratio=increase,"
            f"crop={THUMB_W}:{THUMB_H},"
            f"zoompan=z={zoom_expr}:x={x_expr}:y={y_expr}:d={frames}:s={THUMB_W}x{THUMB_H}:fps=25,"
            f"setsar=1[v{i}]"
        )

    # Crossfade chain
    if n == 1:
        video_chain = "[v0]"
    else:
        xfade_parts: list[str] = []
        offset = durations[0] - CROSSFADE_SEC
        xfade_parts.append(f"[v0][v1]xfade=transition=fade:duration={CROSSFADE_SEC}:offset={offset:.3f}[xf0]")
        for i in range(2, n):
            offset += durations[i - 1] - CROSSFADE_SEC
            prev = f"[xf{i - 2}]"
            xfade_parts.append(
                f"{prev}[v{i}]xfade=transition=fade:duration={CROSSFADE_SEC}:offset={offset:.3f}[xf{i - 1}]"
            )
        filter_parts.extend(xfade_parts)
        video_chain = f"[xf{n - 2}]"

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", video_chain,
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(out_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("video.ffmpeg.error", stderr=result.stderr[-500:])
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-200:]}")


def _burn_subtitles(video_path: Path, srt_path: str, out_path: Path) -> None:
    srt_escaped = srt_path.replace(":", "\\:").replace("'", "\\'")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", (
            f"subtitles='{srt_escaped}':force_style="
            "'FontName=Apple SD Gothic Neo,FontSize=20,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,Outline=2,Alignment=2'"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.warning("video.subtitle_burn.failed", stderr=result.stderr[-300:])
        # fallback: just copy without subtitles
        shutil.copy2(str(video_path), str(out_path))
