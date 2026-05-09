from __future__ import annotations

import json
import re
from collections.abc import Iterable
from urllib.parse import quote_plus

import httpx

from app.core.logging import get_logger

log = get_logger(__name__)

YOUTUBE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.6,en;q=0.5",
}

WARNING_WORDS = ["폭락", "위기", "위험", "주의", "반드시", "충격", "붕괴", "경고"]
QUESTION_WORDS = ["될까", "어떻게", "왜", "뭘", "무엇", "가능", "살까", "팔까", "맞나", "인가"]
OPPORTUNITY_WORDS = ["기회", "저평가", "급매", "반등", "수혜", "줍줍", "오른다"]
AUTHORITY_WORDS = ["전문가", "공개", "데이터", "분석", "팩트", "보고서", "통계"]
CHECKLIST_WORDS = ["체크", "신호", "방법", "전략", "공식", "원칙", "시나리오"]


def analyze_creative(title: str) -> dict:
    """Return lightweight title/creative pattern analysis for YouTube reference videos."""
    patterns: list[str] = []
    hook_type = "informational"

    if any(word in title for word in WARNING_WORDS):
        hook_type = "warning"
        patterns.append("risk_warning")
    if "?" in title or any(word in title for word in QUESTION_WORDS):
        hook_type = "question" if hook_type == "informational" else hook_type
        patterns.append("question_hook")
    if any(word in title for word in OPPORTUNITY_WORDS):
        hook_type = "opportunity" if hook_type == "informational" else hook_type
        patterns.append("opportunity_signal")
    if re.search(r"\d+|[0-9]+가지|첫째|둘째|셋째", title):
        patterns.append("numbered")
    if any(word in title for word in AUTHORITY_WORDS):
        patterns.append("expert_authority")
    if any(word in title for word in CHECKLIST_WORDS):
        patterns.append("checklist")
    if len(title) <= 24:
        patterns.append("short_title")
    if any(mark in title for mark in ["!", "…", "ㄷㄷ"]):
        patterns.append("emotional_punctuation")

    score = min(10, len(set(patterns)) + (2 if hook_type in {"warning", "question", "opportunity"} else 0))
    return {
        "hook_type": hook_type,
        "patterns": sorted(set(patterns)),
        "score": score,
        "title_length": len(title),
    }


def _extract_initial_data(html: str) -> dict:
    marker = "ytInitialData"
    idx = html.find(marker)
    if idx < 0:
        return {}
    start = html.find("{", idx)
    if start < 0:
        return {}

    depth = 0
    in_string = False
    escape = False
    for pos in range(start, len(html)):
        ch = html[pos]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                raw = html[start : pos + 1]
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {}
    return {}


def _walk(obj) -> Iterable[dict]:
    if isinstance(obj, dict):
        if "videoRenderer" in obj and isinstance(obj["videoRenderer"], dict):
            yield obj["videoRenderer"]
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk(value)


def _text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("simpleText"), str):
            return value["simpleText"]
        runs = value.get("runs")
        if isinstance(runs, list):
            return "".join(run.get("text", "") for run in runs if isinstance(run, dict))
    return ""


def _parse_korean_views(text: str) -> int:
    if not text:
        return 0
    compact = text.replace(",", "").replace("조회수", "").replace("회", "").strip()
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([만천]?)", compact)
    if not match:
        return 0
    number = float(match.group(1))
    unit = match.group(2)
    if unit == "만":
        number *= 10000
    elif unit == "천":
        number *= 1000
    return int(number)


def _video_from_renderer(renderer: dict, query: str) -> dict | None:
    video_id = renderer.get("videoId")
    title = _text(renderer.get("title"))
    if not video_id or not title:
        return None
    channel = _text(renderer.get("ownerText") or renderer.get("shortBylineText"))
    published = _text(renderer.get("publishedTimeText"))
    view_text = _text(renderer.get("viewCountText") or renderer.get("shortViewCountText"))
    thumbs = renderer.get("thumbnail", {}).get("thumbnails", []) if isinstance(renderer.get("thumbnail"), dict) else []
    thumbnail_url = ""
    if thumbs and isinstance(thumbs[-1], dict):
        thumbnail_url = thumbs[-1].get("url", "")
    return {
        "title": title,
        "channel": channel,
        "query": query,
        "published": published,
        "video_id": video_id,
        "url": f"https://youtube.com/watch?v={video_id}",
        "thumbnail_url": thumbnail_url,
        "views": _parse_korean_views(view_text),
        "likes": 0,
        "source": "youtube_fallback",
        "creative_analysis": analyze_creative(title),
    }


def parse_youtube_initial_data(html: str, query: str = "") -> list[dict]:
    data = _extract_initial_data(html)
    if not data:
        return []
    seen: set[str] = set()
    items: list[dict] = []
    for renderer in _walk(data):
        item = _video_from_renderer(renderer, query)
        if not item or item["video_id"] in seen:
            continue
        seen.add(item["video_id"])
        items.append(item)
    return items


def fetch_youtube_search_fallback(query: str, max_results: int = 10) -> list[dict]:
    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}&sp=CAI%253D"
    try:
        with httpx.Client(timeout=12, follow_redirects=True, headers=YOUTUBE_HEADERS) as client:
            resp = client.get(url)
            resp.raise_for_status()
        items = parse_youtube_initial_data(resp.text, query=query)[:max_results]
        log.info("youtube_fallback.search.done", query=query, total=len(items))
        return items
    except Exception as e:
        log.warning("youtube_fallback.search.error", query=query, error=str(e))
        return []


def fetch_youtube_channel_fallback(channel_id: str, channel_name: str, max_results: int = 10) -> list[dict]:
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    try:
        with httpx.Client(timeout=12, follow_redirects=True, headers=YOUTUBE_HEADERS) as client:
            resp = client.get(url)
            resp.raise_for_status()
        items = parse_youtube_initial_data(resp.text, query=channel_name)[:max_results]
        if not items and channel_name:
            items = fetch_youtube_search_fallback(channel_name, max_results=max_results)
        for item in items:
            item["channel"] = item.get("channel") or channel_name
        log.info("youtube_fallback.channel.done", channel=channel_name, total=len(items))
        return items
    except Exception as e:
        log.warning("youtube_fallback.channel.error", channel=channel_name, error=str(e))
        return []
