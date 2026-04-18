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
