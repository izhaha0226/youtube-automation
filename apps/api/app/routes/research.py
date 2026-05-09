from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from app.core.db import engine
from app.models import ArticleRecord, ResearchSession, VideoReferenceRecord
from app.modules.research.service import create_from_category, create_from_url, expand_session
from app.schemas import ResearchExpandRequest, ResearchSessionCreate, ResearchSessionResponse, ResearchSource

router = APIRouter()


@router.post("/sessions", response_model=ResearchSessionResponse)
def research_create(payload: ResearchSessionCreate) -> ResearchSessionResponse:
    if payload.mode == "url":
        if not payload.url:
            raise HTTPException(422, "url is required for url mode")
        return create_from_url(payload.url, payload.category)
    if not payload.category:
        raise HTTPException(422, "category is required for category mode")
    return create_from_category(payload.category)


@router.post("/sessions/expand", response_model=ResearchSessionResponse)
def research_expand(payload: ResearchExpandRequest) -> ResearchSessionResponse:
    try:
        return expand_session(payload.session_id, payload.article_ids, payload.video_ids)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/sessions/{session_id}", response_model=ResearchSessionResponse)
def research_get(session_id: str) -> ResearchSessionResponse:
    with Session(engine) as s:
        sess = s.get(ResearchSession, session_id)
        if not sess:
            raise HTTPException(404, "Research session not found")
        article_rows = s.exec(select(ArticleRecord).where(ArticleRecord.session_id == session_id)).all()
        video_rows = s.exec(select(VideoReferenceRecord).where(VideoReferenceRecord.session_id == session_id)).all()
    return ResearchSessionResponse(
        session_id=sess.id,
        mode=sess.mode,
        category=sess.category,
        source=ResearchSource(
            type="article" if sess.mode == "category" else "unknown",
            title=sess.source_title or "",
            url=sess.source_url or "",
            summary=sess.source_summary or "",
            keywords=sess.source_keywords,
        ),
        articles=[
            {
                "id": a.id,
                "title": a.title,
                "source": a.source,
                "url": a.url,
                "published_at": a.published_at,
                "summary": a.summary,
                "keywords": a.keywords,
                "related_score": a.related_score,
                "selected": a.selected,
            }
            for a in article_rows
        ],
        videos=[
            {
                "id": v.id,
                "youtube_video_id": v.youtube_video_id,
                "title": v.title,
                "channel": v.channel,
                "url": v.url,
                "views": v.views,
                "published_at": v.published_at,
                "relevance_score": v.relevance_score,
                "creative_analysis": (v.payload or {}).get("creative_analysis", {}),
                "selected": v.selected,
            }
            for v in video_rows
        ],
    )
