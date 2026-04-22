from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.schemas import ScenarioInput, TopicCandidate, TopicResult, TopicScore
from app.modules.scenario.generator import generate_scenario
from app.modules.topic.selector import select_topic
from app.schemas import TopicInput


class TestArchetypeSchemas:
    def test_topic_candidate_archetype_required_in_result_shape(self):
        candidate = TopicCandidate(
            title="금리보다 무서운 신호",
            reason="실수요 판단에 직접 연결됩니다",
            score=TopicScore(popularity=5),
            archetype="경고형",
        )
        assert candidate.archetype == "경고형"

    def test_topic_result_selected_archetype_exists(self):
        result = TopicResult(
            recommended_topics=[],
            selected_topic="금리보다 무서운 신호",
            selected_reason="오늘 바로 찍을 가치가 큼",
            selected_archetype="경고형",
        )
        assert result.selected_archetype == "경고형"

    def test_scenario_input_defaults_to_judgment_archetype(self):
        payload = ScenarioInput(topic="금리")
        assert payload.archetype == "판단형"


class TestArchetypePromptFlow:
    @patch("app.modules.topic.selector.llm")
    def test_topic_selector_returns_selected_archetype(self, mock_llm_factory):
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "recommended_topics": [
                {
                    "title": "금리보다 무서운 신호",
                    "reason": "실수요 판단에 직접 연결됩니다",
                    "score": {
                        "popularity": 5,
                        "economy": 4,
                        "realestate": 4,
                        "virality": 4,
                        "richgo_fit": 5,
                        "discussion": 3,
                    },
                    "archetype": "경고형",
                }
            ],
            "selected_topic": "금리보다 무서운 신호",
            "selected_reason": "오늘 바로 촬영 가능한 해석형 주제입니다",
            "selected_archetype": "경고형",
        }
        mock_llm_factory.return_value = mock_client

        result = select_topic(
            TopicInput(
                current_issues=["기준금리 동결"],
                trend_keywords=["금리", "실수요"],
            )
        )

        assert result.selected_archetype == "경고형"
        assert result.recommended_topics[0].archetype == "경고형"
        user_prompt = mock_client.generate_json.call_args.kwargs["user"]
        assert "Content Archetype" in user_prompt
        assert "경고형" in user_prompt
        assert "판단형" in user_prompt

    @patch("app.modules.scenario.generator.llm")
    def test_scenario_prompt_includes_archetype(self, mock_llm_factory):
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "hook": "금리 인하의 진짜 의미",
            "hook_30s": "30초 안에 판단 끝냅니다",
            "bridge_3min": "3분 안에 시장 영향까지 연결합니다",
            "body": ["본론 1: 시장 반응"],
            "body_sections": [{"heading": "시장 반응", "script": "시장 반응 설명"}],
            "conclusion": "정리하면 이렇습니다",
            "action_takeaways": ["체크포인트 1"],
            "cta": "구독과 좋아요 부탁드립니다",
            "title_candidates": ["금리 인하, 집값은?"],
            "thumbnail_candidates": ["금리↓ 집값↑?"],
            "opening": "안녕하세요 리치고입니다",
            "opening_title": "오늘의 핵심 해설",
            "estimated_duration_min": 11,
            "archetype": "경고형",
        }
        mock_llm_factory.return_value = mock_client

        out = generate_scenario(ScenarioInput(topic="금리 인하 시그널", keywords=["금리"], archetype="경고형", session_id="sess-1"))

        user_prompt = mock_client.generate_json.call_args.kwargs["user"]
        assert "콘텐츠 archetype: 경고형" in user_prompt
        assert out.archetype == "경고형"
