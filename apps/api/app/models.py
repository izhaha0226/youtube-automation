from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class PipelineRun(SQLModel, table=True):
    id: str = Field(primary_key=True)
    channel: str = "리치고"
    intent: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    meta: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class TopicRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(index=True)
    title: str
    reason: str
    score: int
    risk: str
    selected: bool = False
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScenarioRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(index=True)
    title: str
    hook: str
    body: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    conclusion: str
    cta: str
    title_candidates: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    thumbnail_candidates: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(index=True)
    passed: bool
    issues: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    fix_suggestions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AssetRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(index=True)
    kind: str  # narration | subtitle_en | subtitle_ja | subtitle_zh | thumbnail | package
    path: str
    meta: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UploadRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(index=True)
    video_id: str | None = None
    url: str | None = None
    status: str = "pending"
    log: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PerformanceRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    video_id: str = Field(index=True)
    measured_at: datetime = Field(default_factory=datetime.utcnow)
    views: int = 0
    ctr: float = 0.0
    avg_view_duration_sec: float = 0.0
    likes: int = 0
    comments: int = 0
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class ResearchSession(SQLModel, table=True):
    id: str = Field(primary_key=True)
    mode: str = Field(index=True)  # url | category
    category: str | None = None
    source_url: str | None = None
    source_title: str | None = None
    source_summary: str | None = None
    source_keywords: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    selected_article_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    selected_video_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ArticleRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    title: str
    source: str = ""
    url: str = ""
    published_at: str | None = None
    summary: str = ""
    keywords: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    related_score: float = 0.0
    selected: bool = False
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VideoReferenceRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    youtube_video_id: str | None = None
    title: str
    channel: str = ""
    url: str = ""
    views: int = 0
    published_at: str | None = None
    relevance_score: float = 0.0
    selected: bool = False
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VideoAnalysisCache(SQLModel, table=True):
    cache_key: str = Field(primary_key=True)
    youtube_video_id: str | None = Field(default=None, index=True)
    url: str = Field(default="", index=True)
    title: str = Field(default="", index=True)
    channel: str = ""
    analysis: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    source_snapshot: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScenarioWorkspace(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    selected_topic: str
    target_duration_min: int = 10
    target_duration_max: int = 12
    hook_30s: str = ""
    bridge_3min: str = ""
    body_sections: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    full_script_markdown: str = ""
    title_candidates: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    thumbnail_candidates: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    references_snapshot: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Trend-based Richgo Content Strategy OS ---


class ChannelStats(SQLModel, table=True):
    id: str = Field(primary_key=True)
    channel: str = Field(default="리치고", index=True)
    measured_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    subscriber_count: int | None = None
    audience: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    topic_patterns: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    top_videos: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StrategySession(SQLModel, table=True):
    id: str = Field(primary_key=True)
    channel: str = Field(default="리치고", index=True)
    status: str = Field(default="draft", index=True)
    selected_issue_id: str | None = Field(default=None, index=True)
    selected_topic_id: str | None = Field(default=None, index=True)
    context: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TrendIssue(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    title: str
    summary: str = ""
    category: str = ""
    source: str = "manual"
    keywords: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    urgency_score: int = 0
    richgo_fit_score: int = 0
    evidence: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    selected: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TrendValidation(SQLModel, table=True):
    id: str = Field(primary_key=True)
    issue_id: str = Field(index=True)
    provider: str = Field(index=True)  # naver | google | news | youtube
    keyword: str = ""
    score: float = 0.0
    basis: str = ""
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NewsArticle(SQLModel, table=True):
    id: str = Field(primary_key=True)
    issue_id: str = Field(index=True)
    title: str
    source: str = ""
    url: str = ""
    published_at: str | None = None
    stance: str = "neutral"
    summary: str = ""
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class YouTubeBenchmark(SQLModel, table=True):
    id: str = Field(primary_key=True)
    issue_id: str = Field(index=True)
    youtube_video_id: str | None = None
    title: str
    channel: str = ""
    url: str = ""
    views: int = 0
    published_at: str | None = None
    hook_pattern: str = ""
    success_factors: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TopicRecommendation(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    issue_id: str | None = Field(default=None, index=True)
    title: str
    angle: str = ""
    score_hexagon: dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON))
    total_score: int = 0
    richgo_value: str = ""
    discovery_hypothesis: str = ""
    strategy_hypothesis: str = ""
    tactical_hypothesis: str = ""
    verification_signals: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    failure_criteria: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    decision_label: str = Field(default="data_missing", index=True)
    next_loop: str = ""
    hypothesis_payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    selected: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScenarioVersion(SQLModel, table=True):
    id: str = Field(primary_key=True)
    topic_id: str = Field(index=True)
    version: int = 1
    title: str
    script_markdown: str = ""
    opening_30s: str = ""
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserSelection(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    target_type: str = Field(index=True)  # issue | article | benchmark | topic | scenario
    target_id: str = Field(index=True)
    action: str = "select"
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
