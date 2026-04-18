from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.core.llm import llm
from app.core.logging import get_logger
from app.models import PerformanceRecord, UploadRecord

log = get_logger(__name__)


def fetch_latest() -> dict:
    """Fetch recent video stats via YouTube Data API v3 (public statistics)."""
    if not settings.google_api_key or not settings.youtube_channel_id:
        return {"ok": False, "reason": "missing api key or channel id"}
    try:
        from googleapiclient.discovery import build

        yt = build("youtube", "v3", developerKey=settings.google_api_key)
        search = (
            yt.search()
            .list(
                channelId=settings.youtube_channel_id,
                part="id,snippet",
                order="date",
                maxResults=20,
                type="video",
            )
            .execute()
        )
        ids = [it["id"]["videoId"] for it in search.get("items", []) if "videoId" in it["id"]]
        snippet_by_id = {
            it["id"]["videoId"]: it["snippet"]
            for it in search.get("items", [])
            if "videoId" in it["id"]
        }
        stats = (
            yt.videos()
            .list(id=",".join(ids), part="statistics,contentDetails")
            .execute()
        )
        snapshots = []
        with Session(engine) as s:
            for it in stats.get("items", []):
                vid = it["id"]
                st = it.get("statistics", {})
                sn = snippet_by_id.get(vid, {})
                rec = PerformanceRecord(
                    id=str(uuid.uuid4()),
                    video_id=vid,
                    measured_at=datetime.utcnow(),
                    views=int(st.get("viewCount", 0)),
                    likes=int(st.get("likeCount", 0)),
                    comments=int(st.get("commentCount", 0)),
                    ctr=0.0,  # needs YouTube Analytics API (OAuth)
                    avg_view_duration_sec=0.0,
                    payload={"title": sn.get("title", ""), "published": sn.get("publishedAt", "")},
                )
                s.add(rec)
                snapshots.append({"video_id": vid, "views": rec.views, "title": sn.get("title", "")})
            s.commit()
        return {"ok": True, "count": len(snapshots), "snapshots": snapshots}
    except Exception as e:
        log.warning("perf.fetch.error", error=str(e))
        return {"ok": False, "error": str(e)}


def weekly_report() -> dict:
    cutoff = datetime.utcnow() - timedelta(days=7)
    with Session(engine) as s:
        rows = s.exec(
            select(PerformanceRecord).where(PerformanceRecord.measured_at >= cutoff)
        ).all()
    by_video: dict[str, list[PerformanceRecord]] = {}
    for r in rows:
        by_video.setdefault(r.video_id, []).append(r)

    top = []
    for vid, recs in by_video.items():
        latest = max(recs, key=lambda r: r.measured_at)
        top.append(
            {
                "video_id": vid,
                "title": latest.payload.get("title", ""),
                "views": latest.views,
                "likes": latest.likes,
                "comments": latest.comments,
            }
        )
    top.sort(key=lambda x: x["views"], reverse=True)

    insight = _insight(top)
    return {"window_days": 7, "videos": top, "insight": insight}


def _insight(top: list[dict]) -> dict:
    if not top:
        return {"summary": "데이터 부족", "suggestions": []}
    try:
        system = "You analyze YouTube channel performance for 리치고 and suggest next topics. JSON only."
        user = (
            "지난 7일간 상위 영상 성과:\n"
            + "\n".join(f"- {x['title']} | views={x['views']} likes={x['likes']}" for x in top[:10])
            + "\n\n출력 JSON: {summary, patterns, suggested_topics(list of 3)}"
        )
        return llm(temperature=0.3).generate_json(system=system, user=user)
    except Exception as e:
        log.warning("perf.insight.error", error=str(e))
        return {"summary": "LLM insight skipped", "suggestions": [], "error": str(e)}
