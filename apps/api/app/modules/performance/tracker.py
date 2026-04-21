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
    api_key = settings.effective_youtube_api_key
    if not api_key or not settings.youtube_channel_id:
        return {"ok": False, "reason": "missing api key or channel id"}
    try:
        from googleapiclient.discovery import build

        yt = build("youtube", "v3", developerKey=api_key)
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
    """Generate a weekly performance report with LLM-driven insights."""
    cutoff = datetime.utcnow() - timedelta(days=7)
    with Session(engine) as s:
        rows = s.exec(
            select(PerformanceRecord).where(PerformanceRecord.measured_at >= cutoff)
        ).all()

    if not rows:
        return {
            "window_days": 7,
            "total_videos": 0,
            "videos": [],
            "aggregated": {},
            "insight": {"summary": "데이터 부족", "suggestions": []},
        }

    by_video: dict[str, list[PerformanceRecord]] = {}
    for r in rows:
        by_video.setdefault(r.video_id, []).append(r)

    video_stats = []
    for vid, recs in by_video.items():
        latest = max(recs, key=lambda r: r.measured_at)
        earliest = min(recs, key=lambda r: r.measured_at)
        view_growth = latest.views - earliest.views if len(recs) > 1 else 0
        engagement_rate = (
            (latest.likes + latest.comments) / latest.views * 100
            if latest.views > 0
            else 0.0
        )
        video_stats.append(
            {
                "video_id": vid,
                "title": latest.payload.get("title", ""),
                "published": latest.payload.get("published", ""),
                "views": latest.views,
                "likes": latest.likes,
                "comments": latest.comments,
                "ctr": round(latest.ctr, 2),
                "avg_view_duration_sec": round(latest.avg_view_duration_sec, 1),
                "view_growth": view_growth,
                "engagement_rate": round(engagement_rate, 2),
            }
        )
    video_stats.sort(key=lambda x: x["views"], reverse=True)

    aggregated = _aggregate(video_stats)
    insight = _generate_insight(video_stats, aggregated)

    return {
        "window_days": 7,
        "total_videos": len(video_stats),
        "videos": video_stats,
        "aggregated": aggregated,
        "insight": insight,
    }


def _aggregate(video_stats: list[dict]) -> dict:
    """Compute channel-level aggregated metrics from per-video stats."""
    total_views = sum(v["views"] for v in video_stats)
    total_likes = sum(v["likes"] for v in video_stats)
    total_comments = sum(v["comments"] for v in video_stats)
    total_growth = sum(v["view_growth"] for v in video_stats)
    n = len(video_stats)

    ctr_values = [v["ctr"] for v in video_stats if v["ctr"] > 0]
    dur_values = [v["avg_view_duration_sec"] for v in video_stats if v["avg_view_duration_sec"] > 0]

    return {
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_view_growth": total_growth,
        "avg_views": round(total_views / n, 1) if n else 0,
        "avg_ctr": round(sum(ctr_values) / len(ctr_values), 2) if ctr_values else 0.0,
        "avg_view_duration_sec": round(sum(dur_values) / len(dur_values), 1) if dur_values else 0.0,
        "avg_engagement_rate": round(
            (total_likes + total_comments) / total_views * 100, 2
        ) if total_views > 0 else 0.0,
    }


def _generate_insight(video_stats: list[dict], aggregated: dict) -> dict:
    """Use LLM to produce actionable insights from performance data."""
    if not video_stats:
        return {"summary": "데이터 부족", "suggestions": []}

    top_10 = video_stats[:10]
    stats_block = "\n".join(
        f"- {v['title']} | views={v['views']} growth={v['view_growth']} "
        f"likes={v['likes']} comments={v['comments']} "
        f"ctr={v['ctr']}% duration={v['avg_view_duration_sec']}s "
        f"engagement={v['engagement_rate']}%"
        for v in top_10
    )

    system = (
        "You are a YouTube analytics expert for the channel 리치고 (economy/real-estate). "
        "Analyze performance data and produce actionable insights. Respond in JSON only."
    )
    user = (
        f"=== Channel aggregated (last 7 days) ===\n"
        f"Total views: {aggregated['total_views']}, "
        f"Total view growth: {aggregated['total_view_growth']}, "
        f"Avg CTR: {aggregated['avg_ctr']}%, "
        f"Avg watch duration: {aggregated['avg_view_duration_sec']}s, "
        f"Avg engagement rate: {aggregated['avg_engagement_rate']}%\n\n"
        f"=== Top videos ===\n{stats_block}\n\n"
        f"Produce a JSON object with these keys:\n"
        f"- summary: 2-3 sentence Korean overview of this week's performance\n"
        f"- patterns: list of observed content patterns (Korean, max 5)\n"
        f"- strengths: list of what worked well (Korean, max 3)\n"
        f"- improvements: list of areas to improve (Korean, max 3)\n"
        f"- suggested_topics: list of 3 next video topic ideas (Korean, with reason)\n"
        f"- ctr_analysis: brief CTR trend note (Korean)\n"
        f"- retention_analysis: brief watch-time/retention note (Korean)"
    )

    try:
        return llm(temperature=0.3).generate_json(system=system, user=user)
    except Exception as e:
        log.warning("perf.insight.error", error=str(e))
        return {"summary": "LLM insight skipped", "suggestions": [], "error": str(e)}
