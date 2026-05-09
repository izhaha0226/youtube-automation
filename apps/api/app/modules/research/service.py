from __future__ import annotations

import re
import uuid
from collections import Counter
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from app.core.db import engine
from app.core.logging import get_logger
from app.models import ArticleRecord, ResearchSession, VideoReferenceRecord
from app.modules.trend.scanner import fetch_news, fetch_youtube_trending
from app.schemas import (
    ArticleCandidate,
    ResearchSessionResponse,
    ResearchSource,
    VideoCandidate,
)

log = get_logger(__name__)


def _extract_keywords(text: str, limit: int = 8) -> list[str]:
    bag: Counter[str] = Counter()
    for token in re.findall(r"[가-힣A-Za-z0-9]{2,}", text):
        if len(token) < 2:
            continue
        bag[token] += 1
    return [w for w, _ in bag.most_common(limit)]


def _best_effort_extract(url: str) -> ResearchSource:
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
        paragraphs = [p.get_text(" ", strip=True) for p in soup.select("p")[:8]]
        summary = " ".join(p for p in paragraphs if p)[:600]
        source_type = "video" if ("youtube.com" in url or "youtu.be" in url) else "article"
        return ResearchSource(
            type=source_type,
            title=title,
            url=url,
            summary=summary,
            keywords=_extract_keywords(f"{title} {summary}"),
        )
    except Exception as e:
        log.warning("research.extract.error", url=url, error=str(e))
        return ResearchSource(type="unknown", url=url, keywords=[])


def _article_score(item: dict, keywords: list[str]) -> float:
    text = f"{item.get('title', '')} {item.get('desc', '')}"
    overlap = sum(1 for kw in keywords if kw and kw in text)
    return float(overlap)


def _video_score(item: dict, keywords: list[str]) -> float:
    text = f"{item.get('title', '')} {item.get('channel', '')}"
    overlap = sum(1 for kw in keywords if kw and kw in text)
    views = item.get("views", 0) or 0
    return float(overlap * 2 + min(views / 100000, 10))


def _persist_session(mode: str, category: str | None, source: ResearchSource) -> str:
    session_id = str(uuid.uuid4())
    with Session(engine) as s:
        s.add(
            ResearchSession(
                id=session_id,
                mode=mode,
                category=category,
                source_url=source.url,
                source_title=source.title,
                source_summary=source.summary,
                source_keywords=source.keywords,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        s.commit()
    return session_id


def _replace_candidates(session_id: str, articles: list[ArticleCandidate], videos: list[VideoCandidate]) -> None:
    with Session(engine) as s:
        for row in s.exec(select(ArticleRecord).where(ArticleRecord.session_id == session_id)).all():
            s.delete(row)
        for row in s.exec(select(VideoReferenceRecord).where(VideoReferenceRecord.session_id == session_id)).all():
            s.delete(row)
        for article in articles:
            s.add(
                ArticleRecord(
                    id=article.id,
                    session_id=session_id,
                    title=article.title,
                    source=article.source,
                    url=article.url,
                    published_at=article.published_at,
                    summary=article.summary,
                    keywords=article.keywords,
                    related_score=article.related_score,
                    selected=article.selected,
                )
            )
        for video in videos:
            s.add(
                VideoReferenceRecord(
                    id=video.id,
                    session_id=session_id,
                    youtube_video_id=video.youtube_video_id,
                    title=video.title,
                    channel=video.channel,
                    url=video.url,
                    views=video.views,
                    published_at=video.published_at,
                    relevance_score=video.relevance_score,
                    payload={"creative_analysis": video.creative_analysis},
                    selected=video.selected,
                )
            )
        s.commit()


def create_from_url(url: str, category: str | None = None) -> ResearchSessionResponse:
    source = _best_effort_extract(url)
    keywords = source.keywords[:8]
    raw_articles = fetch_news()
    raw_videos = fetch_youtube_trending()
    scored_articles = sorted(raw_articles, key=lambda x: _article_score(x, keywords), reverse=True)[:12]
    scored_videos = sorted(raw_videos, key=lambda x: _video_score(x, keywords), reverse=True)[:12]
    articles = [
        ArticleCandidate(
            id=str(uuid.uuid4()),
            title=item.get("title", ""),
            source=item.get("source", ""),
            url=item.get("link", ""),
            published_at=item.get("pub"),
            summary=item.get("desc", ""),
            keywords=_extract_keywords(f"{item.get('title', '')} {item.get('desc', '')}"),
            related_score=_article_score(item, keywords),
        )
        for item in scored_articles
    ]
    videos = [
        VideoCandidate(
            id=str(uuid.uuid4()),
            youtube_video_id=item.get("video_id"),
            title=item.get("title", ""),
            channel=item.get("channel", ""),
            url=item.get("url", ""),
            views=item.get("views", 0),
            published_at=item.get("published"),
            relevance_score=_video_score(item, keywords),
            creative_analysis=item.get("creative_analysis", {}),
        )
        for item in scored_videos
    ]
    session_id = _persist_session("url", category, source)
    _replace_candidates(session_id, articles, videos)
    return ResearchSessionResponse(session_id=session_id, mode="url", category=category, source=source, articles=articles, videos=videos)


def create_from_category(category: str) -> ResearchSessionResponse:
    source = ResearchSource(
        type="article",
        title=f"{category} 최신 이슈",
        summary=f"{category} 카테고리 최신 기사/영상 탐색 세션",
        keywords=[category],
    )
    raw_articles = [a for a in fetch_news() if category in (a.get("query", "") + a.get("title", "") + a.get("desc", ""))]
    raw_videos = [v for v in fetch_youtube_trending() if category in (v.get("query", "") + v.get("title", ""))]
    articles = [
        ArticleCandidate(
            id=str(uuid.uuid4()),
            title=item.get("title", ""),
            source=item.get("source", ""),
            url=item.get("link", ""),
            published_at=item.get("pub"),
            summary=item.get("desc", ""),
            keywords=_extract_keywords(f"{item.get('title', '')} {item.get('desc', '')}"),
            related_score=1.0,
        )
        for item in raw_articles[:20]
    ]
    videos = [
        VideoCandidate(
            id=str(uuid.uuid4()),
            youtube_video_id=item.get("video_id"),
            title=item.get("title", ""),
            channel=item.get("channel", ""),
            url=item.get("url", ""),
            views=item.get("views", 0),
            published_at=item.get("published"),
            relevance_score=1.0,
            creative_analysis=item.get("creative_analysis", {}),
        )
        for item in raw_videos[:10]
    ]
    session_id = _persist_session("category", category, source)
    _replace_candidates(session_id, articles, videos)
    return ResearchSessionResponse(session_id=session_id, mode="category", category=category, source=source, articles=articles, videos=videos)


def expand_session(session_id: str, article_ids: list[str], video_ids: list[str]) -> ResearchSessionResponse:
    with Session(engine) as s:
        sess = s.get(ResearchSession, session_id)
        if not sess:
            raise ValueError("Research session not found")
        article_rows = s.exec(select(ArticleRecord).where(ArticleRecord.session_id == session_id)).all()
        video_rows = s.exec(select(VideoReferenceRecord).where(VideoReferenceRecord.session_id == session_id)).all()
        selected_articles = [a for a in article_rows if a.id in article_ids]
        selected_videos = [v for v in video_rows if v.id in video_ids]
        keywords = list(sess.source_keywords)
        for row in selected_articles:
            keywords.extend(row.keywords)
            row.selected = True
        for row in selected_videos:
            keywords.extend(_extract_keywords(row.title))
            row.selected = True
        sess.selected_article_ids = article_ids
        sess.selected_video_ids = video_ids
        sess.updated_at = datetime.utcnow()
        s.add(sess)
        s.commit()
        source = ResearchSource(
            type="article" if sess.mode == "category" else "unknown",
            title=sess.source_title or "",
            url=sess.source_url or "",
            summary=sess.source_summary or "",
            keywords=sess.source_keywords,
        )
    keywords = [kw for kw, _ in Counter(keywords).most_common(10)]
    raw_articles = sorted(fetch_news(), key=lambda x: _article_score(x, keywords), reverse=True)[:15]
    raw_videos = sorted(fetch_youtube_trending(), key=lambda x: _video_score(x, keywords), reverse=True)[:15]
    articles = [
        ArticleCandidate(
            id=str(uuid.uuid4()),
            title=item.get("title", ""),
            source=item.get("source", ""),
            url=item.get("link", ""),
            published_at=item.get("pub"),
            summary=item.get("desc", ""),
            keywords=_extract_keywords(f"{item.get('title', '')} {item.get('desc', '')}"),
            related_score=_article_score(item, keywords),
        )
        for item in raw_articles
    ]
    videos = [
        VideoCandidate(
            id=str(uuid.uuid4()),
            youtube_video_id=item.get("video_id"),
            title=item.get("title", ""),
            channel=item.get("channel", ""),
            url=item.get("url", ""),
            views=item.get("views", 0),
            published_at=item.get("published"),
            relevance_score=_video_score(item, keywords),
            creative_analysis=item.get("creative_analysis", {}),
        )
        for item in raw_videos
    ]
    _replace_candidates(session_id, articles, videos)
    return ResearchSessionResponse(session_id=session_id, mode=sess.mode, category=sess.category, source=source, articles=articles, videos=videos)
