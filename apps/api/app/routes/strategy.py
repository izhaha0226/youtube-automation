from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models import StrategySession, TopicRecommendation, TrendIssue, UserSelection
from app.schemas import (
    StrategyCommandCenterResponse,
    StrategySchemaResponse,
    StrategySessionCreate,
    StrategySessionResponse,
    TopicRecommendationCreate,
    TopicRecommendationResponse,
    TrendIssueCreate,
    TrendIssueResponse,
)

router = APIRouter()

SCORE_KEYS = [
    "trend_fit",
    "view_potential",
    "hook_power",
    "target_clarity",
    "richgo_philosophy_fit",
    "production_ease",
]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def session_to_response(session: StrategySession) -> StrategySessionResponse:
    return StrategySessionResponse(
        session_id=session.id,
        channel=session.channel,
        status=session.status,
        selected_issue_id=session.selected_issue_id,
        selected_topic_id=session.selected_topic_id,
        context=session.context,
    )


def issue_to_response(issue: TrendIssue) -> TrendIssueResponse:
    return TrendIssueResponse(
        id=issue.id,
        session_id=issue.session_id,
        title=issue.title,
        summary=issue.summary,
        category=issue.category,
        source=issue.source,
        keywords=issue.keywords,
        urgency_score=issue.urgency_score,
        richgo_fit_score=issue.richgo_fit_score,
        evidence=issue.evidence,
        selected=issue.selected,
    )


def topic_to_response(topic: TopicRecommendation) -> TopicRecommendationResponse:
    return TopicRecommendationResponse(
        id=topic.id,
        session_id=topic.session_id,
        issue_id=topic.issue_id,
        title=topic.title,
        angle=topic.angle,
        score_hexagon=topic.score_hexagon,
        total_score=topic.total_score,
        richgo_value=topic.richgo_value,
        selected=topic.selected,
    )


def build_default_context(payload: StrategySessionCreate) -> dict:
    context = dict(payload.context)
    context.setdefault("product_mode", "trend_based_richgo_content_strategy_os")
    context.setdefault("pc_layout", "left_context_workflow_layer + center_main_decision_layer")
    context.setdefault("right_panel", "disabled")
    context.setdefault("storage_target", "supabase_compatible_sqlmodel_schema")
    return context


@router.get("/schema", response_model=StrategySchemaResponse)
def strategy_schema() -> StrategySchemaResponse:
    """Supabase 전환 기준이 되는 저장 테이블/API 계약을 노출한다."""
    tables = [
        {"name": "channel_stats", "purpose": "리치고 채널 DNA, 타겟, 성별/연령, 주제 패턴 저장"},
        {"name": "strategy_session", "purpose": "한 번의 트렌드 리서치→주제선택→시나리오 생성 흐름"},
        {"name": "trend_issue", "purpose": "오늘 다룰 후보 이슈와 핵심 근거"},
        {"name": "trend_validation", "purpose": "네이버/구글/뉴스/유튜브 검증 점수"},
        {"name": "news_article", "purpose": "관련 기사 리스트와 관점/요약"},
        {"name": "you_tube_benchmark", "purpose": "관련 유튜브 벤치마크와 성공요인"},
        {"name": "topic_recommendation", "purpose": "리치고 철학 기반 3개 주제와 6각형 점수"},
        {"name": "scenario_version", "purpose": "선택 주제의 시나리오 버전 기록"},
        {"name": "user_selection", "purpose": "사용자 선택/판단 audit log"},
    ]
    api_contracts = [
        {"method": "POST", "path": "/strategy/sessions", "purpose": "전략 세션 생성"},
        {"method": "GET", "path": "/strategy/sessions/{session_id}/command-center", "purpose": "PC 2열 Command Center 데이터"},
        {"method": "POST", "path": "/strategy/sessions/{session_id}/issues", "purpose": "트렌드 이슈 저장"},
        {"method": "POST", "path": "/strategy/sessions/{session_id}/topics", "purpose": "6각형 점수 주제 저장"},
        {"method": "POST", "path": "/strategy/sessions/{session_id}/select", "purpose": "이슈/주제/시나리오 선택 기록"},
    ]
    return StrategySchemaResponse(
        storage_target="Supabase PostgreSQL compatible; local SQLite works for dev verification",
        tables=tables,
        api_contracts=api_contracts,
        pc_layout={
            "columns": 2,
            "left": "Context / Workflow Layer",
            "center": "Main Decision Layer",
            "right": None,
        },
    )


@router.post("/sessions", response_model=StrategySessionResponse)
def create_strategy_session(payload: StrategySessionCreate, db: Session = Depends(get_session)) -> StrategySessionResponse:
    session = StrategySession(id=new_id("strat"), channel=payload.channel, context=build_default_context(payload))
    db.add(session)
    db.commit()
    db.refresh(session)

    if payload.selected_issue_title:
        issue = TrendIssue(
            id=new_id("issue"),
            session_id=session.id,
            title=payload.selected_issue_title,
            source="user_seed",
            keywords=[payload.selected_issue_title],
            urgency_score=70,
            richgo_fit_score=75,
            selected=True,
        )
        session.selected_issue_id = issue.id
        session.updated_at = datetime.utcnow()
        db.add(issue)
        db.add(session)
        db.commit()
        db.refresh(session)

    return session_to_response(session)


@router.get("/sessions/{session_id}/command-center", response_model=StrategyCommandCenterResponse)
def command_center(session_id: str, db: Session = Depends(get_session)) -> StrategyCommandCenterResponse:
    session = db.get(StrategySession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="strategy session not found")

    issues = list(db.exec(select(TrendIssue).where(TrendIssue.session_id == session_id)).all())
    topics = list(db.exec(select(TopicRecommendation).where(TopicRecommendation.session_id == session_id)).all())
    return StrategyCommandCenterResponse(
        session=session_to_response(session),
        layout={"columns": 2, "left": "Context / Workflow", "center": "Main Decision", "right": None},
        left_layer={
            "channel_dna": session.channel,
            "workflow_steps": ["채널 DNA", "트렌드/언론", "유튜브 벤치마크", "주제 3개", "시나리오"],
            "current_selection": {"issue_id": session.selected_issue_id, "topic_id": session.selected_topic_id},
            "evidence_mode": "accordion_in_left_layer_or_center_drawer",
        },
        main_layer={
            "screen": "Command Center",
            "primary_jobs": ["이슈 비교", "검증 근거 확인", "주제 선택", "시나리오 생성 준비"],
        },
        issues=[issue_to_response(issue) for issue in issues],
        topic_recommendations=[topic_to_response(topic) for topic in topics],
    )


@router.post("/sessions/{session_id}/issues", response_model=TrendIssueResponse)
def add_issue(session_id: str, payload: TrendIssueCreate, db: Session = Depends(get_session)) -> TrendIssueResponse:
    session = db.get(StrategySession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="strategy session not found")
    issue = TrendIssue(id=new_id("issue"), session_id=session_id, **payload.model_dump())
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue_to_response(issue)


@router.post("/sessions/{session_id}/topics", response_model=TopicRecommendationResponse)
def add_topic(session_id: str, payload: TopicRecommendationCreate, db: Session = Depends(get_session)) -> TopicRecommendationResponse:
    session = db.get(StrategySession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="strategy session not found")
    score_hexagon = payload.score_hexagon.model_dump()
    topic = TopicRecommendation(
        id=new_id("topic"),
        session_id=session_id,
        issue_id=payload.issue_id,
        title=payload.title,
        angle=payload.angle,
        score_hexagon=score_hexagon,
        total_score=sum(score_hexagon[key] for key in SCORE_KEYS),
        richgo_value=payload.richgo_value,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic_to_response(topic)


@router.post("/sessions/{session_id}/select")
def select_target(session_id: str, target_type: str, target_id: str, db: Session = Depends(get_session)) -> dict:
    session = db.get(StrategySession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="strategy session not found")

    if target_type == "issue":
        issue = db.get(TrendIssue, target_id)
        if not issue or issue.session_id != session_id:
            raise HTTPException(status_code=404, detail="issue not found")
        issue.selected = True
        session.selected_issue_id = target_id
        db.add(issue)
    elif target_type == "topic":
        topic = db.get(TopicRecommendation, target_id)
        if not topic or topic.session_id != session_id:
            raise HTTPException(status_code=404, detail="topic not found")
        topic.selected = True
        session.selected_topic_id = target_id
        db.add(topic)
    else:
        raise HTTPException(status_code=400, detail="target_type must be issue or topic")

    session.updated_at = datetime.utcnow()
    selection = UserSelection(id=new_id("sel"), session_id=session_id, target_type=target_type, target_id=target_id)
    db.add(selection)
    db.add(session)
    db.commit()
    return {"ok": True, "session_id": session_id, "target_type": target_type, "target_id": target_id}
