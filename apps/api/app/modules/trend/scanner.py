"""Trend and issue scanner. Sources: YouTube, Naver news, community, Google trends (fallback), internal performance.

Aims for best-effort: if credentials are missing, returns empty lists without raising.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.trend.youtube_fallback import analyze_creative, fetch_youtube_search_fallback

log = get_logger(__name__)

ECON_QUERIES = [
    "금리",
    "집값",
    "부동산",
    "전세",
    "매매",
    "대출",
    "서울 아파트",
    "미국 금리",
    "환율",
    "경기침체",
]


@dataclass
class TrendSnapshot:
    youtube: list[dict] = field(default_factory=list)
    news: list[dict] = field(default_factory=list)
    community: list[dict] = field(default_factory=list)
    internal: list[dict] = field(default_factory=list)

    def keywords(self) -> list[str]:
        items = (
            [x.get("title", "") for x in self.youtube]
            + [x.get("title", "") for x in self.news]
            + [x.get("title", "") for x in self.community]
        )
        bag = {}
        for t in items:
            for w in [w.strip() for w in t.split() if len(w) >= 2]:
                bag[w] = bag.get(w, 0) + 1
        return [w for w, _ in sorted(bag.items(), key=lambda kv: -kv[1])[:30]]

    def as_current_issues(self) -> list[str]:
        top = []
        top.extend([f"[YT] {x['title']}" for x in self.youtube[:8]])
        top.extend([f"[N] {x['title']}" for x in self.news[:8]])
        top.extend([f"[C] {x['title']}" for x in self.community[:4]])
        return top


def _fetch_youtube_fallback_for_queries(queries: list[str], per_query: int = 5) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for query in queries:
        for item in fetch_youtube_search_fallback(query, max_results=per_query):
            key = item.get("video_id") or item.get("url") or item.get("title")
            if not key or key in seen:
                continue
            seen.add(key)
            items.append(item)
    items.sort(key=lambda x: (x.get("views", 0), x.get("creative_analysis", {}).get("score", 0)), reverse=True)
    return items


def fetch_youtube_trending(channel_id: str | None = None) -> list[dict]:
    api_key = settings.effective_youtube_api_key
    queries = ECON_QUERIES[:5]
    if not api_key:
        log.info("trend.youtube.fallback", reason="no GOOGLE_API_KEY or YOUTUBE_API_KEY")
        return _fetch_youtube_fallback_for_queries(queries)
    try:
        from googleapiclient.discovery import build

        yt = build("youtube", "v3", developerKey=api_key)
        items: list[dict] = []
        video_ids: list[str] = []
        id_to_item: dict[str, dict] = {}

        for q in queries:
            resp = (
                yt.search()
                .list(q=q, part="snippet", type="video", maxResults=5, regionCode="KR")
                .execute()
            )
            for it in resp.get("items", []):
                sn = it.get("snippet", {})
                vid = it.get("id", {}).get("videoId", "")
                title = sn.get("title", "")
                item = {
                    "title": title,
                    "channel": sn.get("channelTitle", ""),
                    "query": q,
                    "published": sn.get("publishedAt", ""),
                    "video_id": vid,
                    "url": f"https://youtube.com/watch?v={vid}" if vid else "",
                    "thumbnail_url": (sn.get("thumbnails", {}).get("high") or sn.get("thumbnails", {}).get("default") or {}).get("url", ""),
                    "views": 0,
                    "likes": 0,
                    "source": "youtube_api",
                    "creative_analysis": analyze_creative(title),
                }
                items.append(item)
                if vid:
                    video_ids.append(vid)
                    id_to_item[vid] = item

        if video_ids:
            try:
                for i in range(0, len(video_ids), 50):
                    batch = video_ids[i:i + 50]
                    stats = yt.videos().list(id=",".join(batch), part="statistics").execute()
                    for v in stats.get("items", []):
                        st = v.get("statistics", {})
                        if v["id"] in id_to_item:
                            id_to_item[v["id"]]["views"] = int(st.get("viewCount", 0))
                            id_to_item[v["id"]]["likes"] = int(st.get("likeCount", 0))
            except Exception:
                pass

        items.sort(key=lambda x: x.get("views", 0), reverse=True)
        return items
    except Exception as e:
        log.warning("trend.youtube.error", error=str(e))
        return _fetch_youtube_fallback_for_queries(queries)


def fetch_news() -> list[dict]:
    """Fetch Naver News when configured and always add Google News RSS.

    The source-separated UI needs an independent Google section even when
    Naver credentials are present.  Previously this function returned early
    after Naver, so the Google source looked uncollected.
    """
    items: list[dict] = []
    if settings.naver_client_id and settings.naver_client_secret:
        headers = {
            "X-Naver-Client-Id": settings.naver_client_id,
            "X-Naver-Client-Secret": settings.naver_client_secret,
        }
        try:
            with httpx.Client(timeout=10) as client:
                for q in ["부동산", "금리", "집값"]:
                    r = client.get(
                        "https://openapi.naver.com/v1/search/news.json",
                        headers=headers,
                        params={"query": q, "display": 10, "sort": "date"},
                    )
                    if r.status_code == 200:
                        for it in r.json().get("items", []):
                            link = it.get("originallink") or it.get("link", "")
                            source = ""
                            try:
                                source = link.split("/")[2].replace("www.", "")
                            except (IndexError, AttributeError):
                                pass
                            items.append(
                                {
                                    "title": _strip(it.get("title", "")),
                                    "link": link,
                                    "desc": _strip(it.get("description", "")),
                                    "pub": it.get("pubDate", ""),
                                    "source": source,
                                    "provider": "naver",
                                    "query": q,
                                }
                            )
        except Exception as e:
            log.warning("trend.naver.error", error=str(e))

    # Google News RSS signal: keep this independent, not just a fallback.
    try:
        for q in ["부동산", "금리", "집값"]:
            feed = feedparser.parse(
                f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
            )
            for entry in feed.entries[:10]:
                title = getattr(entry, "title", "")
                source_name = getattr(entry, "source", {})
                if isinstance(source_name, dict):
                    source_name = source_name.get("title", "")
                elif hasattr(source_name, "title"):
                    source_name = source_name.title
                else:
                    source_name = ""
                if " - " in title and not source_name:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source_name = parts[1].strip()
                items.append(
                    {
                        "title": title,
                        "link": getattr(entry, "link", ""),
                        "pub": getattr(entry, "published", ""),
                        "source": source_name,
                        "provider": "google",
                        "query": q,
                    }
                )
    except Exception as e:
        log.warning("trend.rss.error", error=str(e))

    seen: set[tuple[str, str]] = set()
    deduped: list[dict] = []
    for item in items:
        key = (item.get("title", "")[:60], item.get("provider", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def fetch_community() -> list[dict]:
    """Scrape trending keywords from real-estate communities and RSS feeds.

    Sources:
      1. Naver 부동산 카페 인기글 (부동산스터디, 부동산114 등)
      2. 부동산 뉴스 RSS (한국경제 부동산, 매일경제 부동산)
    """
    items: list[dict] = []

    # --- 1. Naver cafe popular articles (mobile page, no login needed) ---
    cafe_targets = [
        {"name": "부동산스터디", "cafe_id": "jaegebal"},
        {"name": "부동산114", "cafe_id": "land114"},
        {"name": "월급쟁이부자들", "cafe_id": "wecando7"},
    ]
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13; SM-S908B) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Mobile Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }
    try:
        with httpx.Client(timeout=12, follow_redirects=True) as client:
            for cafe in cafe_targets:
                try:
                    url = f"https://m.cafe.naver.com/ca-fe/cafes/{cafe['cafe_id']}/articles?page=1&boardType=L"
                    resp = client.get(url, headers=headers)
                    if resp.status_code != 200:
                        log.debug("community.cafe.skip", cafe=cafe["name"], status=resp.status_code)
                        continue
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Mobile cafe list items
                    for tag in soup.select("a.tit, a.article_title, h3.title_text, a[class*='article']"):
                        title = tag.get_text(strip=True)
                        if len(title) < 4:
                            continue
                        link = tag.get("href", "")
                        if link and not link.startswith("http"):
                            link = f"https://m.cafe.naver.com{link}"
                        items.append({
                            "title": title,
                            "source": cafe["name"],
                            "link": link,
                            "type": "cafe",
                        })
                except Exception as e:
                    log.debug("community.cafe.error", cafe=cafe["name"], error=str(e))
    except Exception as e:
        log.warning("community.cafe.client_error", error=str(e))

    # --- 2. Real-estate news RSS feeds ---
    rss_feeds = [
        {"name": "한국경제 부동산", "url": "https://www.hankyung.com/feed/land"},
        {"name": "매일경제 부동산", "url": "https://www.mk.co.kr/rss/realestate/"},
        {"name": "조선비즈 부동산", "url": "https://biz.chosun.com/nsearch/rss/realestate.xml"},
    ]
    for feed_info in rss_feeds:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:15]:
                title = getattr(entry, "title", "")
                if not title or len(title) < 4:
                    continue
                items.append({
                    "title": _strip(title),
                    "source": feed_info["name"],
                    "link": getattr(entry, "link", ""),
                    "pub": getattr(entry, "published", ""),
                    "type": "rss",
                })
        except Exception as e:
            log.debug("community.rss.error", feed=feed_info["name"], error=str(e))

    # --- 3. Deduplicate by title similarity ---
    seen: set[str] = set()
    deduped: list[dict] = []
    for item in items:
        key = item["title"][:20]
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    log.info("community.done", total=len(deduped), cafe=len([i for i in deduped if i.get("type") == "cafe"]), rss=len([i for i in deduped if i.get("type") == "rss"]))
    return deduped


def fetch_internal_performance() -> list[dict]:
    """Pull recent top-performing past videos for recurrence signals."""
    from sqlmodel import Session, select

    from app.core.db import engine
    from app.models import PerformanceRecord

    out: list[dict] = []
    try:
        with Session(engine) as s:
            rows = s.exec(
                select(PerformanceRecord).order_by(PerformanceRecord.measured_at.desc()).limit(20)
            ).all()
            for r in rows:
                out.append(
                    {
                        "title": r.payload.get("title", ""),
                        "views": r.views,
                        "ctr": r.ctr,
                    }
                )
    except Exception as e:
        log.info("trend.internal.skip", error=str(e))
    return out


def scan() -> TrendSnapshot:
    snap = TrendSnapshot(
        youtube=fetch_youtube_trending(),
        news=fetch_news(),
        community=fetch_community(),
        internal=fetch_internal_performance(),
    )
    log.info(
        "trend.scan.done",
        yt=len(snap.youtube),
        news=len(snap.news),
        community=len(snap.community),
        internal=len(snap.internal),
    )
    return snap


def _strip(s: str) -> str:
    return (
        s.replace("<b>", "")
        .replace("</b>", "")
        .replace("&quot;", '"')
        .replace("&amp;", "&")
        .strip()
    )
