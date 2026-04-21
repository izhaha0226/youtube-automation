from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.models import ScenarioWorkspace
from app.modules.review.reviewer import review_scenario
from app.modules.scenario.generator import generate_scenario
from app.modules.topic.selector import select_topic
from app.schemas import ReviewInput, ScenarioInput, ScenarioOutput, TopicInput


class TestEditorialContext:
    @patch("app.modules.topic.selector.llm")
    def test_topic_prompt_includes_kim_kiwon_editorial_context(self, mock_llm_factory):
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "recommended_topics": [
                {
                    "title": "금리 인하 시그널",
                    "reason": "시장 관심도 높음",
                    "score": {
                        "popularity": 5,
                        "economy": 4,
                        "realestate": 4,
                        "virality": 3,
                        "richgo_fit": 5,
                        "discussion": 4,
                    },
                    "risk": "정치적 민감",
                    "keywords": ["금리", "한국은행"],
                }
            ],
            "selected_topic": "금리 인하 시그널",
            "selected_reason": "점수 최고",
        }
        mock_llm_factory.return_value = mock_client

        select_topic(
            TopicInput(
                user_intent="금리",
                current_issues=["금리 인하 기대"],
                trend_keywords=["금리", "부동산"],
            )
        )

        user_prompt = mock_client.generate_json.call_args.kwargs["user"]
        assert "가슴 뛰는 목표" in user_prompt
        assert "통제력과 영향력" in user_prompt
        assert "어려운 선택" in user_prompt

    @patch("app.modules.scenario.generator.llm")
    def test_scenario_prompt_includes_kim_kiwon_editorial_context(self, mock_llm_factory):
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
        }
        mock_llm_factory.return_value = mock_client

        generate_scenario(ScenarioInput(topic="금리 인하 시그널", keywords=["금리"], session_id="sess-1"))

        user_prompt = mock_client.generate_json.call_args.kwargs["user"]
        assert "통제력과 영향력" in user_prompt
        assert "본질 중심" in user_prompt
        assert "실수요" in user_prompt

    @patch("app.modules.review.reviewer.llm")
    def test_review_prompt_includes_editorial_context(self, mock_llm_factory):
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "passed": False,
            "issues": ["근거가 약함"],
            "fix_suggestions": ["기사 근거를 더 넣어라"],
        }
        mock_llm_factory.return_value = mock_client

        review_scenario(
            ReviewInput(
                topic="금리 인하 시그널",
                scenario=ScenarioOutput(
                    hook="강한 훅",
                    hook_30s="30초 훅",
                    bridge_3min="3분 브릿지",
                    body=["본문 요약"],
                    body_sections=[{"heading": "핵심", "script": "설명"}],
                    conclusion="결론",
                    action_takeaways=["체크포인트"],
                    cta="댓글로 남겨주세요",
                    title_candidates=["제목1"],
                    thumbnail_candidates=["썸네일1"],
                    opening="오프닝",
                    opening_title="오프닝 타이틀",
                    estimated_duration_min=11,
                ),
            )
        )

        user_prompt = mock_client.generate_json.call_args.kwargs["user"]
        assert "가슴 뛰는 목표" in user_prompt
        assert "통제력과 영향력" in user_prompt
        assert "본질 중심" in user_prompt


class TestWorkspaceObsidianExport:
    def test_export_workspace_package_writes_obsidian_markdown_and_json(self, tmp_path, monkeypatch):
        from app.modules.sync import obsidian as obsidian_sync

        monkeypatch.setattr(obsidian_sync.settings, "obsidian_vault", str(tmp_path))
        row = ScenarioWorkspace(
            id="w1",
            session_id="sess-1",
            selected_topic="금리 인하 시그널",
            target_duration_min=10,
            target_duration_max=12,
            hook_30s="30초 훅",
            bridge_3min="3분 브릿지",
            body_sections=[{"heading": "핵심", "script": "설명"}],
            full_script_markdown="# script",
            title_candidates=["제목1"],
            thumbnail_candidates=["썸네일1"],
            references_snapshot={
                "articles": [{"id": "a1", "title": "기사1", "url": "https://example.com/article"}],
                "videos": [{"id": "v1", "title": "영상1", "url": "https://youtube.com/watch?v=1"}],
                "keywords": ["금리", "부동산"],
                "selected_article_ids": ["a1"],
                "selected_video_ids": ["v1"],
                "scenario": {
                    "hook": "강한 훅",
                    "hook_30s": "30초 훅",
                    "bridge_3min": "3분 브릿지",
                    "body": ["본문 요약"],
                    "body_sections": [{"heading": "핵심", "script": "설명"}],
                    "conclusion": "결론",
                    "action_takeaways": ["체크포인트"],
                    "cta": "댓글로 남겨주세요",
                    "title_candidates": ["제목1"],
                    "thumbnail_candidates": ["썸네일1"],
                    "opening": "오프닝",
                    "opening_title": "오프닝 타이틀",
                    "estimated_duration_min": 11,
                },
                "review": {"passed": False, "issues": ["근거가 약함"], "fix_suggestions": ["기사 근거를 더 넣어라"]},
            },
            status="reviewed",
            created_at=datetime(2026, 4, 21, 0, 0, 0),
            updated_at=datetime(2026, 4, 21, 1, 0, 0),
        )

        md_path, json_path = obsidian_sync.export_workspace_package(row)

        assert md_path.exists()
        assert json_path.exists()
        markdown = md_path.read_text(encoding="utf-8")
        payload = json_path.read_text(encoding="utf-8")
        assert "session_id: sess-1" in markdown
        assert "## 🎯 주제" in markdown
        assert "## 📚 선택 근거" in markdown
        assert "## 🧪 검수 결과" in markdown
        assert "금리 인하 시그널" in markdown
        assert '"selected_topic": "금리 인하 시그널"' in payload
