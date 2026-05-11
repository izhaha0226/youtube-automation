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
    selected_videos: list[dict] = Field(default_factory=list)


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
    discovery_hypothesis: str = ""
    strategy_hypothesis: str = ""
    tactical_hypothesis: str = ""
    verification_signals: list[str] = Field(default_factory=list)
    failure_criteria: list[str] = Field(default_factory=list)
    decision_label: Literal["scale", "iterate", "stop", "data_missing"] = "data_missing"
    next_loop: str = ""
    hypothesis_payload: dict = Field(default_factory=dict)


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


class ScenarioBodySection(BaseModel):
    heading: str = ""
    summary: str = ""
    script: str = ""
    narration: str = ""
    reference_type: str = ""
    reference_hint: str = ""
    viewer_takeaway: str = ""


class ScenarioOutput(BaseModel):
    hook: str
    hook_30s: str = ""
    bridge_3min: str = ""
    archetype: ContentArchetype = "판단형"
    body: list[str]
    body_sections: list[ScenarioBodySection] = Field(default_factory=list)
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
    creative_analysis: dict = Field(default_factory=dict)
    selected: bool = False


class ResearchSessionCreate(BaseModel):
    mode: Literal["url", "category", "trend"]
    category: str | None = None
    url: str | None = None
    selected_articles: list[str] = Field(default_factory=list)
    trend_keywords: list[str] = Field(default_factory=list)


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


# --- Trend-based Richgo Content Strategy OS ---


class StrategySessionCreate(BaseModel):
    channel: str = "리치고"
    selected_issue_title: str | None = None
    context: dict = Field(default_factory=dict)


class StrategySessionResponse(BaseModel):
    session_id: str
    channel: str
    status: str
    selected_issue_id: str | None = None
    selected_topic_id: str | None = None
    context: dict = Field(default_factory=dict)


class TrendIssueCreate(BaseModel):
    title: str
    summary: str = ""
    category: str = ""
    source: str = "manual"
    keywords: list[str] = Field(default_factory=list)
    urgency_score: int = Field(default=0, ge=0, le=100)
    richgo_fit_score: int = Field(default=0, ge=0, le=100)
    evidence: dict = Field(default_factory=dict)


class TrendIssueResponse(TrendIssueCreate):
    id: str
    session_id: str
    selected: bool = False


class StrategyHexagonScore(BaseModel):
    trend_fit: int = Field(ge=0, le=100)
    view_potential: int = Field(ge=0, le=100)
    hook_power: int = Field(ge=0, le=100)
    target_clarity: int = Field(ge=0, le=100)
    richgo_philosophy_fit: int = Field(ge=0, le=100)
    production_ease: int = Field(ge=0, le=100)


class TopicRecommendationCreate(BaseModel):
    issue_id: str | None = None
    title: str
    angle: str = ""
    score_hexagon: StrategyHexagonScore
    richgo_value: str = "시청자가 시장을 감정이 아니라 데이터와 원칙으로 보게 만든다."
    discovery_hypothesis: str = ""
    strategy_hypothesis: str = ""
    tactical_hypothesis: str = ""
    verification_signals: list[str] = Field(default_factory=list)
    failure_criteria: list[str] = Field(default_factory=list)
    decision_label: Literal["scale", "iterate", "stop", "data_missing"] = "data_missing"
    next_loop: str = ""
    hypothesis_payload: dict = Field(default_factory=dict)


class TopicRecommendationResponse(BaseModel):
    id: str
    session_id: str
    issue_id: str | None = None
    title: str
    angle: str
    score_hexagon: dict
    total_score: int
    richgo_value: str
    discovery_hypothesis: str = ""
    strategy_hypothesis: str = ""
    tactical_hypothesis: str = ""
    verification_signals: list[str] = Field(default_factory=list)
    failure_criteria: list[str] = Field(default_factory=list)
    decision_label: Literal["scale", "iterate", "stop", "data_missing"] = "data_missing"
    next_loop: str = ""
    hypothesis_payload: dict = Field(default_factory=dict)
    selected: bool = False


class TrendValidationCreate(BaseModel):
    issue_id: str
    provider: Literal["naver", "google", "news", "youtube"]
    keyword: str = ""
    score: float = Field(default=0, ge=0)
    basis: str = ""
    payload: dict = Field(default_factory=dict)


class TrendValidationResponse(TrendValidationCreate):
    id: str


class NewsArticleCreate(BaseModel):
    issue_id: str
    title: str
    source: str = ""
    url: str = ""
    published_at: str | None = None
    stance: Literal["positive", "negative", "neutral", "mixed"] = "neutral"
    summary: str = ""
    payload: dict = Field(default_factory=dict)


class NewsArticleResponse(NewsArticleCreate):
    id: str


class YouTubeBenchmarkCreate(BaseModel):
    issue_id: str
    youtube_video_id: str | None = None
    title: str
    channel: str = ""
    url: str = ""
    views: int = Field(default=0, ge=0)
    published_at: str | None = None
    hook_pattern: str = ""
    success_factors: list[str] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)


class YouTubeBenchmarkResponse(YouTubeBenchmarkCreate):
    id: str


class ScenarioVersionCreate(BaseModel):
    topic_id: str
    version: int = Field(default=1, ge=1)
    title: str
    script_markdown: str = ""
    opening_30s: str = ""
    payload: dict = Field(default_factory=dict)


class ScenarioVersionResponse(ScenarioVersionCreate):
    id: str


class StrategyCommandCenterResponse(BaseModel):
    session: StrategySessionResponse
    layout: dict
    left_layer: dict
    main_layer: dict
    issues: list[TrendIssueResponse] = Field(default_factory=list)
    validations: list[TrendValidationResponse] = Field(default_factory=list)
    news_articles: list[NewsArticleResponse] = Field(default_factory=list)
    youtube_benchmarks: list[YouTubeBenchmarkResponse] = Field(default_factory=list)
    topic_recommendations: list[TopicRecommendationResponse] = Field(default_factory=list)
    scenario_versions: list[ScenarioVersionResponse] = Field(default_factory=list)


class StrategySchemaResponse(BaseModel):
    storage_target: str
    tables: list[dict]
    api_contracts: list[dict]
    pc_layout: dict
