from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared schemas – 프론트엔드·백엔드 공용 핵심 IO 타입
# 백엔드 app/schemas.py 의 전체를 복제하지 않고,
# 외부(프론트엔드/CLI/워커)에서 참조해야 하는 타입만 정의한다.
# ---------------------------------------------------------------------------

# --- Topic ---


class TopicScore(BaseModel):
    popularity: int = 0
    economy: int = 0
    realestate: int = 0
    virality: int = 0
    richgo_fit: int = 0
    discussion: int = 0

    def total(self) -> int:
        return (
            self.popularity
            + self.economy
            + self.realestate
            + self.virality
            + self.richgo_fit
            + self.discussion
        )


class TopicCandidate(BaseModel):
    title: str
    reason: str
    score: TopicScore
    risk: str = ""
    keywords: list[str] = Field(default_factory=list)


class TopicResult(BaseModel):
    recommended_topics: list[TopicCandidate]
    selected_topic: str
    selected_reason: str
    next_step: Literal["scenario"] = "scenario"


# --- Scenario ---


class ScenarioOutput(BaseModel):
    hook: str
    body: list[str]
    conclusion: str
    cta: str
    title_candidates: list[str]
    thumbnail_candidates: list[str]
    opening: str = ""


# --- Review ---


class ReviewResult(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)
    fix_suggestions: list[str] = Field(default_factory=list)


# --- Pipeline Status ---


PipelineStage = Literal[
    "topic",
    "scenario",
    "review",
    "narration",
    "subtitle",
    "thumbnail",
    "package",
    "upload",
    "performance",
]


class PipelineStatus(BaseModel):
    run_id: str
    stage: PipelineStage
    status: Literal["pending", "running", "done", "error"] = "pending"
    message: str = ""


# --- Performance ---


class PerformanceSnapshot(BaseModel):
    video_id: str
    views: int
    ctr: float
    avg_view_duration_sec: float
    likes: int
    comments: int
    title: str | None = None


__all__ = [
    "TopicScore",
    "TopicCandidate",
    "TopicResult",
    "ScenarioOutput",
    "ReviewResult",
    "PipelineStage",
    "PipelineStatus",
    "PerformanceSnapshot",
]
