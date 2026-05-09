"""YouTube benchmark channel analyzer.

Fetches top-performing videos from competitor channels to identify
what topics/formats are getting the most views.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.trend.youtube_fallback import analyze_creative, fetch_youtube_channel_fallback

log = get_logger(__name__)


def fetch_channel_top_videos(channel_id: str, channel_name: str, max_results: int = 10) -> list[dict]:
    api_key = settings.effective_youtube_api_key
    if not api_key or not channel_id:
        return fetch_youtube_channel_fallback(channel_id, channel_name, max_results=max_results) if channel_id else []
    try:
        from googleapiclient.discovery import build

        yt = build("youtube", "v3", developerKey=api_key)

        search_resp = yt.search().list(
            channelId=channel_id,
            part="snippet",
            type="video",
            order="viewCount",
            maxResults=max_results,
            regionCode="KR",
        ).execute()

        video_ids = [item["id"]["videoId"] for item in search_resp.get("items", []) if item["id"].get("videoId")]
        if not video_ids:
            return []

        stats_resp = yt.videos().list(
            id=",".join(video_ids),
            part="snippet,statistics",
        ).execute()

        results = []
        for item in stats_resp.get("items", []):
            sn = item.get("snippet", {})
            st = item.get("statistics", {})
            title = sn.get("title", "")
            results.append({
                "video_id": item["id"],
                "title": title,
                "channel": channel_name,
                "published": sn.get("publishedAt", ""),
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
                "url": f"https://youtube.com/watch?v={item['id']}",
                "thumbnail_url": (sn.get("thumbnails", {}).get("high") or sn.get("thumbnails", {}).get("default") or {}).get("url", ""),
                "source": "youtube_api",
                "creative_analysis": analyze_creative(title),
            })
        results.sort(key=lambda x: x["views"], reverse=True)
        return results
    except Exception as e:
        log.warning("benchmark.error", channel=channel_name, error=str(e))
        return fetch_youtube_channel_fallback(channel_id, channel_name, max_results=max_results)


def fetch_all_benchmarks() -> list[dict]:
    cfg = settings.project_config
    channels = cfg.get("benchmark_channels", [])
    all_videos: list[dict] = []
    for ch in channels:
        cid = ch.get("channel_id", "")
        cname = ch.get("name", "")
        if cid:
            videos = fetch_channel_top_videos(cid, cname, max_results=8)
            all_videos.extend(videos)
    all_videos.sort(key=lambda x: x["views"], reverse=True)
    log.info("benchmark.done", total=len(all_videos))
    return all_videos
