"""Scoring threshold tests — validates scoring.yaml rules and selector filtering logic."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.config import settings
from app.schemas import ScenarioInput, TopicCandidate, TopicInput, TopicScore


# ── scoring.yaml 값 검증 ────────────────────────────────────────────────


class TestScoringConfig:
    def test_thresholds_exist(self):
        rules = settings.scoring_rules
        assert "thresholds" in rules
        assert "strong_recommend" in rules["thresholds"]
        assert "recommend" in rules["thresholds"]
        assert "hold" in rules["thresholds"]

    def test_threshold_values(self):
        rules = settings.scoring_rules
        assert rules["thresholds"]["strong_recommend"] == 24
        assert rules["thresholds"]["recommend"] == 18
        assert rules["thresholds"]["hold"] == 17

    def test_top_k(self):
        assert settings.scoring_rules["top_k"] == 3

    def test_axes_count(self):
        axes = settings.scoring_rules.get("axes", {})
        assert len(axes) == 6

    def test_axes_range(self):
        """All scoring axes should have range [0, 5]."""
        axes = settings.scoring_rules.get("axes", {})
        for axis_key, axis in axes.items():
            assert axis["range"] == [0, 5], f"{axis_key} has unexpected range"

    def test_threshold_ordering(self):
        """strong_recommend > recommend > hold."""
        t = settings.scoring_rules["thresholds"]
        assert t["strong_recommend"] > t["recommend"] > t["hold"]


# ── TopicScore 임계값 분류 ──────────────────────────────────────────────


class TestScoreClassification:
    """Test score values against the threshold levels from scoring.yaml."""

    def _classify(self, total: int) -> str:
        rules = settings.scoring_rules
        t = rules["thresholds"]
        if total >= t["strong_recommend"]:
            return "strong_recommend"
        if total >= t["recommend"]:
            return "recommend"
        if total >= t["hold"]:
            return "hold"
        return "reject"

    def test_strong_recommend(self):
        score = TopicScore(
            popularity=5, economy=5, realestate=5,
            virality=4, richgo_fit=3, discussion=3,
        )
        assert score.total() == 25
        assert self._classify(score.total()) == "strong_recommend"

    def test_exactly_strong_recommend_boundary(self):
        score = TopicScore(
            popularity=4, economy=4, realestate=4,
            virality=4, richgo_fit=4, discussion=4,
        )
        assert score.total() == 24
        assert self._classify(score.total()) == "strong_recommend"

    def test_recommend(self):
        score = TopicScore(
            popularity=4, economy=3, realestate=3,
            virality=3, richgo_fit=3, discussion=3,
        )
        assert score.total() == 19
        assert self._classify(score.total()) == "recommend"

    def test_exactly_recommend_boundary(self):
        score = TopicScore(
            popularity=3, economy=3, realestate=3,
            virality=3, richgo_fit=3, discussion=3,
        )
        assert score.total() == 18
        assert self._classify(score.total()) == "recommend"

    def test_hold(self):
        score = TopicScore(
            popularity=3, economy=3, realestate=3,
            virality=3, richgo_fit=3, discussion=2,
        )
        assert score.total() == 17
        assert self._classify(score.total()) == "hold"

    def test_reject(self):
        score = TopicScore(
            popularity=2, economy=2, realestate=3,
            virality=3, richgo_fit=3, discussion=3,
        )
        assert score.total() == 16
        assert self._classify(score.total()) == "reject"

    def test_zero_score(self):
        score = TopicScore()
        assert self._classify(score.total()) == "reject"

    def test_max_score(self):
        score = TopicScore(
            popularity=5, economy=5, realestate=5,
            virality=5, richgo_fit=5, discussion=5,
        )
        assert score.total() == 30
        assert self._classify(score.total()) == "strong_recommend"


# ── selector의 필터링 로직 직접 테스트 ──────────────────────────────────


class TestSelectorFiltering:
    """Test the select_topic function's filtering and sorting logic with mocked LLM."""

    @patch("app.modules.topic.selector.llm")
    def test_filters_below_recommend_threshold(self, mock_llm_factory):
        from app.modules.topic.selector import select_topic

        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "recommended_topics": [
                {
                    "title": "고점수",
                    "reason": "좋음",
                    "score": {
                        "popularity": 5, "economy": 4, "realestate": 4,
                        "virality": 3, "richgo_fit": 4, "discussion": 3,
                    },
                },
                {
                    "title": "저점수",
                    "reason": "별로",
                    "score": {
                        "popularity": 1, "economy": 1, "realestate": 1,
                        "virality": 1, "richgo_fit": 1, "discussion": 1,
                    },
                },
            ],
            "selected_topic": "고점수",
            "selected_reason": "최고 점수",
        }
        mock_llm_factory.return_value = mock_client

        payload = TopicInput(
            current_issues=["이슈"], trend_keywords=["키워드"],
        )
        result = select_topic(payload)

        titles = [c.title for c in result.recommended_topics]
        assert "고점수" in titles
        assert "저점수" not in titles

    @patch("app.modules.topic.selector.llm")
    def test_sorts_by_total_descending(self, mock_llm_factory):
        from app.modules.topic.selector import select_topic

        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "recommended_topics": [
                {
                    "title": "중간",
                    "reason": "중간",
                    "score": {
                        "popularity": 4, "economy": 3, "realestate": 3,
                        "virality": 3, "richgo_fit": 3, "discussion": 3,
                    },
                },
                {
                    "title": "최고",
                    "reason": "최고",
                    "score": {
                        "popularity": 5, "economy": 5, "realestate": 5,
                        "virality": 5, "richgo_fit": 5, "discussion": 5,
                    },
                },
            ],
            "selected_topic": "최고",
            "selected_reason": "최고 점수",
        }
        mock_llm_factory.return_value = mock_client

        payload = TopicInput(
            current_issues=["이슈"], trend_keywords=["키워드"],
        )
        result = select_topic(payload)

        assert result.recommended_topics[0].title == "최고"

    @patch("app.modules.topic.selector.llm")
    def test_top_k_limit(self, mock_llm_factory):
        """At most top_k (3) candidates should be returned."""
        from app.modules.topic.selector import select_topic

        mock_client = MagicMock()
        topics = []
        for i in range(5):
            topics.append({
                "title": f"주제{i}",
                "reason": f"이유{i}",
                "score": {
                    "popularity": 5, "economy": 4, "realestate": 4,
                    "virality": 3, "richgo_fit": 4, "discussion": 3,
                },
            })
        mock_client.generate_json.return_value = {
            "recommended_topics": topics,
            "selected_topic": "주제0",
            "selected_reason": "최고",
        }
        mock_llm_factory.return_value = mock_client

        payload = TopicInput(
            current_issues=["이슈"], trend_keywords=["키워드"],
        )
        result = select_topic(payload)

        assert len(result.recommended_topics) <= 3

    @patch("app.modules.topic.selector.llm")
    def test_all_filtered_out(self, mock_llm_factory):
        """When all candidates score below threshold, result is empty list."""
        from app.modules.topic.selector import select_topic

        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "recommended_topics": [
                {
                    "title": "낮은점수",
                    "reason": "이유",
                    "score": {
                        "popularity": 1, "economy": 1, "realestate": 1,
                        "virality": 1, "richgo_fit": 1, "discussion": 1,
                    },
                },
            ],
            "selected_topic": "",
            "selected_reason": "",
        }
        mock_llm_factory.return_value = mock_client

        payload = TopicInput(
            current_issues=["이슈"], trend_keywords=["키워드"],
        )
        result = select_topic(payload)

        assert result.recommended_topics == []
        assert result.selected_topic == ""

    @patch("app.modules.topic.selector.llm")
    def test_topic_prompt_includes_richgo_context(self, mock_llm_factory):
        from app.modules.topic.selector import select_topic

        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "recommended_topics": [
                {
                    "title": "금리보다 무서운 신호",
                    "reason": "실수요 판단에 직접 연결됩니다",
                    "score": {
                        "popularity": 5, "economy": 4, "realestate": 4,
                        "virality": 4, "richgo_fit": 5, "discussion": 3,
                    },
                },
                {
                    "title": "전세가 먼저 오르는 이유",
                    "reason": "부동산 연결성이 큽니다",
                    "score": {
                        "popularity": 4, "economy": 4, "realestate": 5,
                        "virality": 3, "richgo_fit": 5, "discussion": 3,
                    },
                },
                {
                    "title": "서울만 버틴다는 착각",
                    "reason": "지역별 온도차 해석에 맞습니다",
                    "score": {
                        "popularity": 4, "economy": 3, "realestate": 5,
                        "virality": 4, "richgo_fit": 5, "discussion": 3,
                    },
                },
            ],
            "selected_topic": "금리보다 무서운 신호",
            "selected_reason": "오늘 바로 촬영 가능한 해석형 주제입니다",
        }
        mock_llm_factory.return_value = mock_client

        select_topic(
            TopicInput(
                user_intent="오늘 찍을 경제/부동산 주제",
                avoid_keywords=["정치"],
                must_include=["실수요"],
                current_issues=["기준금리 동결", "서울 거래량 둔화"],
                trend_keywords=["금리", "거래량", "실수요"],
            )
        )

        user_prompt = mock_client.generate_json.call_args.kwargs["user"]
        assert "소스 모드: research-backed" in user_prompt
        assert "우선 속도: 오늘 바로 촬영 가능한 주제를 우선" in user_prompt
        assert "그래서 내 돈, 내 집, 내 지역에 무슨 영향" in user_prompt
        assert "- 꼭 포함할 관점: 실수요" in user_prompt
        assert "실수요" in user_prompt


class TestScenarioPromptRendering:
    @patch("app.modules.scenario.generator.llm")
    def test_scenario_prompt_includes_selected_references_and_duration(self, mock_llm_factory):
        from app.modules.scenario.generator import generate_scenario

        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "hook": "훅",
            "hook_30s": "30초 훅",
            "bridge_3min": "3분 브릿지",
            "body": ["본문1", "본문2", "본문3", "본문4"],
            "body_sections": [{"heading": "핵심", "script": "설명"}],
            "conclusion": "결론",
            "action_takeaways": ["체크 1", "체크 2", "체크 3"],
            "cta": "댓글 남겨주세요",
            "title_candidates": ["제목1", "제목2", "제목3", "제목4", "제목5"],
            "thumbnail_candidates": ["문구1", "문구2", "문구3"],
            "opening": "오프닝",
            "opening_title": "설명형 제목",
            "estimated_duration_min": 11,
        }
        mock_llm_factory.return_value = mock_client

        payload = ScenarioInput(
            topic="금리보다 무서운 신호",
            keywords=["금리", "거래량"],
            reference_points=["거래량 둔화", "대출 규제"],
            selected_articles=[{"title": "기사1", "summary": "요약1"}],
            selected_videos=[{"title": "영상1", "channel": "채널A"}],
            target_duration_min=10,
            target_duration_max=12,
            session_id="sess-123",
        )

        generate_scenario(payload)

        user_prompt = mock_client.generate_json.call_args.kwargs["user"]
        assert "선택 기사(JSON):" in user_prompt
        assert '"title": "기사1"' in user_prompt
        assert "선택 유튜브(JSON):" in user_prompt
        assert '"channel": "채널A"' in user_prompt
        assert "목표 길이: 10~12분" in user_prompt
        assert "세션 ID: sess-123" in user_prompt
