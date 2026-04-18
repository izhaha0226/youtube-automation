"""Schema validation tests — Pydantic models, field defaults, computed properties."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.schemas import (
    ArticleCandidate,
    NarrationInput,
    NarrationOutput,
    PackageManifest,
    PerformanceSnapshot,
    ResearchExpandRequest,
    ResearchSessionCreate,
    ResearchSessionResponse,
    ResearchSource,
    ReviewInput,
    ReviewOutput,
    ScenarioInput,
    ScenarioOutput,
    SubtitleOutput,
    ThumbnailInput,
    ThumbnailOutput,
    TopicCandidate,
    TopicInput,
    TopicResult,
    TopicScore,
    UploadMeta,
    VideoCandidate,
    VideoOutput,
)


# ── TopicScore ──────────────────────────────────────────────────────────


class TestTopicScore:
    def test_total_all_zeros(self):
        score = TopicScore()
        assert score.total() == 0

    def test_total_sum(self):
        score = TopicScore(
            popularity=5, economy=4, realestate=3,
            virality=2, richgo_fit=1, discussion=0,
        )
        assert score.total() == 15

    def test_total_max(self):
        score = TopicScore(
            popularity=5, economy=5, realestate=5,
            virality=5, richgo_fit=5, discussion=5,
        )
        assert score.total() == 30

    def test_partial_fields(self):
        score = TopicScore(popularity=3, economy=2)
        assert score.total() == 5
        assert score.realestate == 0


# ── TopicInput ──────────────────────────────────────────────────────────


class TestTopicInput:
    def test_defaults(self):
        inp = TopicInput()
        assert inp.channel == "리치고"
        assert inp.user_intent == ""
        assert inp.avoid_keywords == []
        assert inp.must_include == []
        assert inp.current_issues == []
        assert inp.trend_keywords == []

    def test_custom_fields(self):
        inp = TopicInput(
            channel="테스트",
            user_intent="금리 인하",
            avoid_keywords=["정치"],
            must_include=["부동산"],
        )
        assert inp.channel == "테스트"
        assert inp.user_intent == "금리 인하"
        assert inp.avoid_keywords == ["정치"]
        assert inp.must_include == ["부동산"]


# ── TopicCandidate ──────────────────────────────────────────────────────


class TestTopicCandidate:
    def test_required_fields(self):
        with pytest.raises(ValidationError):
            TopicCandidate()  # title, reason are required

    def test_minimal(self):
        c = TopicCandidate(title="테스트", reason="이유", score=TopicScore())
        assert c.title == "테스트"
        assert c.risk == ""
        assert c.keywords == []

    def test_with_score(self):
        score = TopicScore(popularity=5, economy=4)
        c = TopicCandidate(title="주제", reason="이유", score=score, keywords=["a", "b"])
        assert c.score.total() == 9
        assert len(c.keywords) == 2


# ── TopicResult ─────────────────────────────────────────────────────────


class TestTopicResult:
    def test_next_step_literal(self):
        result = TopicResult(
            recommended_topics=[], selected_topic="t", selected_reason="r"
        )
        assert result.next_step == "scenario"

    def test_invalid_next_step(self):
        with pytest.raises(ValidationError):
            TopicResult(
                recommended_topics=[], selected_topic="t",
                selected_reason="r", next_step="invalid",
            )


# ── ScenarioInput / Output ──────────────────────────────────────────────


class TestScenarioSchemas:
    def test_scenario_input_defaults(self):
        inp = ScenarioInput(topic="금리")
        assert inp.channel == "리치고"
        assert inp.tone == "경제/부동산 해설형"
        assert inp.reference_points == []
        assert inp.keywords == []
        assert inp.selected_articles == []
        assert inp.selected_videos == []
        assert inp.target_duration_min == 10
        assert inp.target_duration_max == 12

    def test_scenario_input_required_topic(self):
        with pytest.raises(ValidationError):
            ScenarioInput()

    def test_scenario_output_required(self):
        with pytest.raises(ValidationError):
            ScenarioOutput()

    def test_scenario_output_full(self):
        out = ScenarioOutput(
            hook="훅",
            hook_30s="30초 훅",
            bridge_3min="3분 브릿지",
            body=["단락1", "단락2"],
            body_sections=[{"heading": "이슈", "script": "설명"}],
            conclusion="결론",
            action_takeaways=["포인트1"],
            cta="구독",
            title_candidates=["제목1"],
            thumbnail_candidates=["썸네일1"],
            opening="오프닝",
            opening_title="설명형 제목",
            estimated_duration_min=11,
        )
        assert len(out.body) == 2
        assert out.opening == "오프닝"
        assert out.bridge_3min == "3분 브릿지"
        assert out.estimated_duration_min == 11


class TestResearchSchemas:
    def test_research_session_create_url(self):
        payload = ResearchSessionCreate(mode="url", url="https://example.com")
        assert payload.mode == "url"

    def test_research_source_defaults(self):
        src = ResearchSource()
        assert src.type == "unknown"
        assert src.keywords == []

    def test_research_session_response(self):
        resp = ResearchSessionResponse(
            session_id="s1",
            mode="url",
            source=ResearchSource(type="article", title="기사"),
            articles=[ArticleCandidate(id="a1", title="기사1")],
            videos=[VideoCandidate(id="v1", title="영상1")],
        )
        assert resp.session_id == "s1"
        assert len(resp.articles) == 1
        assert len(resp.videos) == 1

    def test_research_expand_request_defaults(self):
        req = ResearchExpandRequest(session_id="s1")
        assert req.article_ids == []
        assert req.video_ids == []


# ── ReviewInput / Output ────────────────────────────────────────────────


class TestReviewSchemas:
    def test_review_input_requires_scenario(self):
        with pytest.raises(ValidationError):
            ReviewInput(topic="금리")

    def test_review_output_defaults(self):
        out = ReviewOutput(passed=True)
        assert out.issues == []
        assert out.fix_suggestions == []

    def test_review_output_with_issues(self):
        out = ReviewOutput(passed=False, issues=["이슈1"], fix_suggestions=["수정1"])
        assert not out.passed
        assert len(out.issues) == 1


# ── NarrationInput / Output ─────────────────────────────────────────────


class TestNarrationSchemas:
    def test_narration_input_defaults(self):
        scenario = ScenarioOutput(
            hook="h", body=["b"], conclusion="c", cta="cta",
            title_candidates=[], thumbnail_candidates=[],
        )
        inp = NarrationInput(scenario=scenario)
        assert inp.tone == "리치고"
        assert inp.expected_length_sec == 480

    def test_narration_output_defaults(self):
        out = NarrationOutput(text_ko="텍스트", sentences=["문장1"])
        assert out.audio_path is None
        assert out.timeline == []


# ── SubtitleOutput ───────────────────────────────────────────────────────


class TestSubtitleOutput:
    def test_valid_lang(self):
        out = SubtitleOutput(lang="ko", srt_path="/a.srt", json_path="/a.json")
        assert out.lang == "ko"

    def test_invalid_lang(self):
        with pytest.raises(ValidationError):
            SubtitleOutput(lang="fr", srt_path="/a.srt", json_path="/a.json")


# ── ThumbnailInput / Output ─────────────────────────────────────────────


class TestThumbnailSchemas:
    def test_defaults(self):
        inp = ThumbnailInput(title="제목", thumbnail_text="텍스트")
        assert inp.style == "clean premium"
        assert inp.source_tool == "Fal.ai"
        assert inp.profile_image is None


# ── VideoOutput ──────────────────────────────────────────────────────────


class TestVideoOutput:
    def test_defaults(self):
        out = VideoOutput()
        assert out.video_path is None
        assert out.duration_sec == 0
        assert out.slide_count == 0


# ── UploadMeta ───────────────────────────────────────────────────────────


class TestUploadMeta:
    def test_required_fields(self):
        with pytest.raises(ValidationError):
            UploadMeta()

    def test_full(self):
        meta = UploadMeta(
            title="제목", description="설명",
            tags=["태그"], hashtags=["#해시"], pinned_comment="고정댓글",
        )
        assert meta.title == "제목"


# ── PackageManifest ──────────────────────────────────────────────────────


class TestPackageManifest:
    def test_required(self):
        with pytest.raises(ValidationError):
            PackageManifest()

    def test_video_path_optional(self):
        m = PackageManifest(
            run_id="r1", topic="t", scenario_path="s",
            narration_path="n", subtitles={}, thumbnail_path="th",
            upload_meta_path="u", review_path="rv",
        )
        assert m.video_path is None


# ── PerformanceSnapshot ─────────────────────────────────────────────────


class TestPerformanceSnapshot:
    def test_title_optional(self):
        snap = PerformanceSnapshot(
            video_id="v1", views=100, ctr=5.2,
            avg_view_duration_sec=120.0, likes=10, comments=3,
        )
        assert snap.title is None
