from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.core.paths import workspace_dir
from app.schemas import PackageManifest

log = get_logger(__name__)


def build_package(run_id: str, video_path: str | None = None) -> PackageManifest:
    pkg_dir = workspace_dir(run_id, "packages")
    bundle = pkg_dir / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)

    # collect — exclude "packages" itself to avoid recursive nesting
    for kind in ("topics", "scenarios", "narrations", "subtitles", "thumbnails", "videos"):
        src = settings.data_dir / kind / run_id
        if not src.exists():
            continue
        dst = bundle / kind
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    # copy upload_meta.json into bundle too
    meta_src = pkg_dir / "upload_meta.json"
    if meta_src.exists():
        shutil.copy2(meta_src, bundle / "upload_meta.json")

    subtitles = {
        lang: str(bundle / "subtitles" / f"subtitles_{lang}.srt")
        for lang in ("ko", "en", "ja", "zh")
        if (bundle / "subtitles" / f"subtitles_{lang}.srt").exists()
    }

    # resolve video path relative to bundle if available
    resolved_video: str | None = None
    if video_path:
        vp = Path(video_path)
        bundle_video = bundle / "videos" / vp.name
        resolved_video = str(bundle_video) if bundle_video.exists() else video_path

    manifest = PackageManifest(
        run_id=run_id,
        topic=_read_json(pkg_dir / "upload_meta.json").get("title", ""),
        scenario_path=str(bundle / "scenarios" / "scenario.json"),
        narration_path=str(bundle / "narrations" / "narration_ko.mp3"),
        subtitles=subtitles,
        thumbnail_path=str(bundle / "thumbnails" / "final.png"),
        upload_meta_path=str(pkg_dir / "upload_meta.json"),
        review_path=str(bundle / "scenarios" / "review.json"),
        video_path=resolved_video,
    )
    (pkg_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    # zip
    archive = pkg_dir / f"{run_id}.zip"
    if archive.exists():
        archive.unlink()
    shutil.make_archive(str(archive.with_suffix("")), "zip", bundle)
    log.info("package.done", archive=str(archive))
    return manifest


def _read_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))
