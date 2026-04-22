from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ContentArchetype = Literal["경고형", "판단형", "기회형", "구조해설형", "원칙형"]

# --- Topic ---


class TopicInput(BaseModel):
    channel: str = "리치고"
    user_intent: str = ""
    avoid_keywords: list[str] = Field(default_factory=list)
    must_include: list[str] = Field(default_factory=list)
    current_issues: list[str] = Field(default_factory=list)
    trend_keywords: list[str] = Field(default_factory=list)


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
    archetype: ContentArchetype = "판단형"
    risk: str = ""
    keywords: list[str] = Field(default_factory=list)


class TopicResult(BaseModel):
    recommended_topics: list[TopicCandidate]
    selected_topic: str
    selected_reason: str
    selected_archetype: ContentArchetype = "판단형"
    next_step: Literal["scenario"] = "scenario"


# --- Scenario ---


class ScenarioInput(BaseModel):
    topic: str
    channel: str = "리치고"
    archetype: ContentArchetype = "판단형"
    reference_points: list[str] = Field(default_factory=list)
    tone: str = "경제/부동산 해설형"
    keywords: list[str] = Field(default_factory=list)
    selected_articles: list[dict] = Field(default_factory=list)
    selected_videos: list[dict] = Field(default_factory=list)
    target_duration_min: int = 10
    target_duration_max: int = 12
    session_id: str | None = None


class ScenarioOutput(BaseModel):
    hook: str
    hook_30s: str = ""
    bridge_3min: str = ""
    archetype: ContentArchetype = "판단형"
    body: list[str]
    body_sections: list[dict] = Field(default_factory=list)
    conclusion: str
    action_takeaways: list[str] = Field(default_factory=list)
    cta: str
    title_candidates: list[str]
    thumbnail_candidates: list[str]
    opening: str = ""
    opening_title: str = ""
    estimated_duration_min: int = 10


# --- Research ---


class ResearchSource(BaseModel):
    type: Literal["article", "video", "unknown"] = "unknown"
    title: str = ""
    url: str = ""
    summary: str = ""
    keywords: list[str] = Field(default_factory=list)


class ArticleCandidate(BaseModel):
    id: str
    title: str
    source: str = ""
    url: str = ""
    published_at: str | None = None
    summary: str = ""
    keywords: list[str] = Field(default_factory=list)
    related_score: float = 0.0
    selected: bool = False


class VideoCandidate(BaseModel):
    id: str
    youtube_video_id: str | None = None
    title: str
    channel: str = ""
    url: str = ""
    views: int = 0
    published_at: str | None = None
    relevance_score: float = 0.0
    selected: bool = False


class ResearchSessionCreate(BaseModel):
    mode: Literal["url", "category"]
    category: str | None = None
    url: str | None = None


class ResearchSessionResponse(BaseModel):
    session_id: str
    mode: str
    category: str | None = None
    source: ResearchSource
    articles: list[ArticleCandidate] = Field(default_factory=list)
    videos: list[VideoCandidate] = Field(default_factory=list)


class ResearchExpandRequest(BaseModel):
    session_id: str
    article_ids: list[str] = Field(default_factory=list)
    video_ids: list[str] = Field(default_factory=list)


# --- Review ---


class ReviewInput(BaseModel):
    scenario: ScenarioOutput
    topic: str
    channel: str = "리치고"
    reference_points: list[str] = Field(default_factory=list)


class ReviewOutput(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)
    fix_suggestions: list[str] = Field(default_factory=list)


# --- Narration / Subtitle ---


class NarrationInput(BaseModel):
    scenario: ScenarioOutput
    tone: str = "리치고"
    expected_length_sec: int = 480


class NarrationOutput(BaseModel):
    text_ko: str
    sentences: list[str]
    audio_path: str | None = None
    timeline: list[dict] = Field(default_factory=list)


class SubtitleOutput(BaseModel):
    lang: Literal["ko", "en", "ja", "zh"]
    srt_path: str
    json_path: str


# --- Thumbnail ---


class ThumbnailInput(BaseModel):
    title: str
    thumbnail_text: str
    profile_image: str | None = None
    style: str = "clean premium"
    source_tool: str = "Fal.ai"


class ThumbnailOutput(BaseModel):
    draft_images: list[str]
    final_image: str
    overlay_used: bool
    save_path: str


# --- Video ---


class VideoOutput(BaseModel):
    video_path: str | None = None
    duration_sec: float = 0
    slide_count: int = 0


# --- Upload Meta / Package ---


class UploadMeta(BaseModel):
    title: str
    description: str
    tags: list[str]
    hashtags: list[str]
    pinned_comment: str


class PackageManifest(BaseModel):
    run_id: str
    topic: str
    scenario_path: str
    narration_path: str
    subtitles: dict[str, str]
    thumbnail_path: str
    upload_meta_path: str
    review_path: str
    video_path: str | None = None


# --- Performance ---


class PerformanceSnapshot(BaseModel):
    video_id: str
    views: int
    ctr: float
    avg_view_duration_sec: float
    likes: int
    comments: int
    title: str | None = None
