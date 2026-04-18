from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.core.paths import workspace_dir

log = get_logger(__name__)


def upload_to_youtube(run_id: str, dry_run: bool = False) -> dict:
    pkg = workspace_dir(run_id, "packages")
    meta_path = pkg / "upload_meta.json"
    thumb_path = pkg / "bundle" / "thumbnails" / "final.png"
    if not meta_path.exists():
        return {"ok": False, "error": "upload_meta missing"}
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    if dry_run or not (
        settings.youtube_client_id
        and settings.youtube_client_secret
        and settings.youtube_refresh_token
    ):
        log.info("upload.youtube.skip", reason="dry_run or missing OAuth")
        return {"ok": False, "reason": "package-only", "meta": meta}

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = Credentials(
            token=None,
            refresh_token=settings.youtube_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.youtube_client_id,
            client_secret=settings.youtube_client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )
        creds.refresh(Request())
        yt = build("youtube", "v3", credentials=creds)

        # Find assembled video — check both possible locations
        video_candidates = [
            pkg / "bundle" / "videos" / "video_final.mp4",
            pkg / "bundle" / "video.mp4",
        ]
        video = next((p for p in video_candidates if p.exists()), None)
        if not video:
            log.info("upload.youtube.skip", reason="no rendered video found")
            return {"ok": False, "reason": "no video rendered", "meta": meta}

        body = {
            "snippet": {
                "title": meta["title"],
                "description": meta["description"],
                "tags": meta["tags"],
                "categoryId": "25",  # News & Politics / economy fits 22/25
            },
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False},
        }
        media = MediaFileUpload(str(video), chunksize=-1, resumable=True, mimetype="video/mp4")
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = req.execute()
        video_id = resp["id"]

        # Thumbnail
        if thumb_path.exists():
            yt.thumbnails().set(
                videoId=video_id, media_body=MediaFileUpload(str(thumb_path))
            ).execute()

        # Captions
        subs_dir = pkg / "bundle" / "subtitles"
        for lang in ("ko", "en", "ja", "zh"):
            srt = subs_dir / f"subtitles_{lang}.srt"
            if not srt.exists():
                continue
            yt.captions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "language": lang,
                        "name": lang,
                        "isDraft": False,
                    }
                },
                media_body=MediaFileUpload(str(srt)),
            ).execute()

        url = f"https://youtu.be/{video_id}"
        log.info("upload.youtube.done", video_id=video_id, url=url)
        return {"ok": True, "video_id": video_id, "url": url}
    except Exception as e:
        log.warning("upload.youtube.error", error=str(e))
        return {"ok": False, "error": str(e)}
