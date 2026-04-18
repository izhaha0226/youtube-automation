"""API endpoint tests — FastAPI TestClient with mocked LLM / DB calls."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

# Patch init_db before importing app so lifespan doesn't touch a real DB.
with patch("app.core.db.init_db"):
    from app.main import app

client = TestClient(app)


# ── Health ──────────────────────────────────────────────────────────────


class TestHealth:
    def test_health_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert "model" in body
        assert "channel" in body
        assert "env" in body

    def test_health_channel_name(self):
        resp = client.get("/health")
        assert resp.json()["channel"] == "리치고"


# ── Topics ──────────────────────────────────────────────────────────────


def _mock_llm_topic_response():
    """Return a realistic LLM JSON response for topic selection."""
    return {
        "recommended_topics": [
            {
                "title": "금리 인하 시그널",
                "reason": "시장 관심도 높음",
                "score": {
                    "popularity": 5, "economy": 4, "realestate": 4,
                    "virality": 3, "richgo_fit": 5, "discussion": 4,
                },
                "risk": "정치적 민감",
                "keywords": ["금리", "한국은행"],
            },
            {
                "title": "아파트 가격 반등",
                "reason": "거래량 증가",
                "score": {
                    "popularity": 4, "economy": 3, "realestate": 5,
                    "virality": 4, "richgo_fit": 5, "discussion": 3,
                },
                "risk": "",
                "keywords": ["부동산", "아파트"],
            },
        ],
        "selected_topic": "금리 인하 시그널",
        "selected_reason": "점수 최고",
    }


class TestTopics:
    @patch("app.modules.topic.selector.llm")
    def test_topics_post(self, mock_llm_factory):
        mock_client = MagicMock()
        mock_client.generate_json.return_value = _mock_llm_topic_response()
        mock_llm_factory.return_value = mock_client

        payload = {
            "channel": "리치고",
            "user_intent": "금리",
            "current_issues": ["금리 인하 기대"],
            "trend_keywords": ["금리", "부동산"],
        }
        resp = client.post("/topics", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "recommended_topics" in body
        assert body["selected_topic"] == "금리 인하 시그널"
        assert body["next_step"] == "scenario"
        assert len(body["recommended_topics"]) <= 3

    @patch("app.modules.topic.selector.llm")
    def test_topics_filters_low_scores(self, mock_llm_factory):
        """Topics below the recommend threshold (18) are filtered out."""
        mock_client = MagicMock()
        low_score_data = {
            "recommended_topics": [
                {
                    "title": "저점수 주제",
                    "reason": "별로",
                    "score": {
                        "popularity": 1, "economy": 1, "realestate": 1,
                        "virality": 1, "richgo_fit": 1, "discussion": 1,
                    },
                },
            ],
            "selected_topic": "",
            "selected_reason": "",
        }
        mock_client.generate_json.return_value = low_score_data
        mock_llm_factory.return_value = mock_client

        resp = client.post("/topics", json={
            "current_issues": ["x"], "trend_keywords": ["y"],
        })
        assert resp.status_code == 200
        assert resp.json()["recommended_topics"] == []

    @patch("app.modules.topic.selector.llm")
    def test_topics_empty_payload(self, mock_llm_factory):
        """Empty payload should trigger trend scan fallback — mock it."""
        mock_client = MagicMock()
        mock_client.generate_json.return_value = _mock_llm_topic_response()
        mock_llm_factory.return_value = mock_client

        with patch("app.modules.topic.selector.scan") as mock_scan:
            snap = MagicMock()
            snap.as_current_issues.return_value = ["이슈1"]
            snap.keywords.return_value = ["키워드1"]
            mock_scan.return_value = snap

            resp = client.post("/topics", json={})
            assert resp.status_code == 200
            mock_scan.assert_called_once()


# ── Scenarios ───────────────────────────────────────────────────────────


def _mock_llm_scenario_response():
    return {
        "hook": "금리 인하의 진짜 의미",
        "hook_30s": "30초 안에 판단 끝냅니다",
        "bridge_3min": "3분 안에 시장 영향까지 연결합니다",
        "body": ["본론 1: 시장 반응", "본론 2: 향후 전망"],
        "body_sections": [{"heading": "시장 반응", "script": "시장 반응 설명"}],
        "conclusion": "정리하면 이렇습니다",
        "action_takeaways": ["체크포인트 1"],
        "cta": "구독과 좋아요 부탁드립니다",
        "title_candidates": ["금리 인하, 집값은?", "한국은행의 선택"],
        "thumbnail_candidates": ["금리↓ 집값↑?"],
        "opening": "안녕하세요 리치고입니다",
        "opening_title": "오늘의 핵심 해설",
        "estimated_duration_min": 11,
    }


class TestScenarios:
    @patch("app.modules.scenario.generator.llm")
    @patch("app.routes.scenarios.save_scenario_workspace")
    def test_scenarios_post(self, mock_save_workspace, mock_llm_factory):
        mock_client = MagicMock()
        mock_client.generate_json.return_value = _mock_llm_scenario_response()
        mock_llm_factory.return_value = mock_client
        mock_save_workspace.return_value = MagicMock()

        payload = {"topic": "금리 인하 시그널", "keywords": ["금리"], "session_id": "sess-1"}
        resp = client.post("/scenarios", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["hook"] == "금리 인하의 진짜 의미"
        assert len(body["body"]) == 2
        assert len(body["title_candidates"]) == 2
        assert body["opening"] == "안녕하세요 리치고입니다"
        assert body["hook_30s"] == "30초 안에 판단 끝냅니다"
        assert body["estimated_duration_min"] == 11

    def test_scenarios_missing_topic(self):
        resp = client.post("/scenarios", json={})
        assert resp.status_code == 422

    @patch("app.routes.scenarios.get_workspace_by_session")
    def test_scenario_workspace_get(self, mock_get):
        mock_get.return_value = MagicMock(
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
                "articles": [{"id": "a1", "title": "기사1"}],
                "videos": [{"id": "v1", "title": "영상1"}],
                "keywords": ["금리"],
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
            },
            status="generated",
            created_at=MagicMock(isoformat=lambda: "2026-04-18T00:00:00"),
            updated_at=MagicMock(isoformat=lambda: "2026-04-18T00:00:00"),
        )
        resp = client.get("/scenarios/workspace/sess-1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"] == "sess-1"
        assert body["selected_article_ids"] == ["a1"]
        assert body["selected_video_ids"] == ["v1"]
        assert body["scenario"]["opening"] == "오프닝"
        assert body["scenario"]["conclusion"] == "결론"
        assert body["scenario"]["action_takeaways"] == ["체크포인트"]

    @patch("app.routes.scenarios.review_workspace")
    def test_scenario_workspace_review(self, mock_review_workspace):
        mock_review_workspace.return_value = {
            "passed": False,
            "issues": ["근거가 약함"],
            "fix_suggestions": ["기사 근거를 더 넣어라"],
        }
        resp = client.post("/scenarios/workspace/sess-1/review")
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed"] is False
        assert body["issues"] == ["근거가 약함"]
        assert body["fix_suggestions"] == ["기사 근거를 더 넣어라"]

    @patch("app.routes.scenarios.regenerate_workspace")
    def test_scenario_workspace_regenerate(self, mock_regenerate_workspace):
        mock_regenerate_workspace.return_value = _mock_llm_scenario_response()
        resp = client.post("/scenarios/workspace/sess-1/regenerate")
        assert resp.status_code == 200
        body = resp.json()
        assert body["hook_30s"] == "30초 안에 판단 끝냅니다"
        assert body["bridge_3min"] == "3분 안에 시장 영향까지 연결합니다"
        assert body["estimated_duration_min"] == 11

    @patch("app.routes.scenarios.narrate_workspace")
    def test_scenario_workspace_narrate(self, mock_narrate_workspace):
        mock_narrate_workspace.return_value = {
            "text_ko": "안녕하세요. 오늘 핵심부터 말씀드릴게요.",
            "sentences": ["안녕하세요.", "오늘 핵심부터 말씀드릴게요."],
            "audio_path": "/tmp/narration.mp3",
            "timeline": [{"idx": 0, "text": "안녕하세요.", "start_ms": 0, "end_ms": 900}],
        }
        resp = client.post("/scenarios/workspace/sess-1/narrate")
        assert resp.status_code == 200
        body = resp.json()
        assert body["audio_path"] == "/tmp/narration.mp3"
        assert len(body["sentences"]) == 2
        assert body["timeline"][0]["text"] == "안녕하세요."

    @patch("app.routes.scenarios.subtitle_workspace")
    def test_scenario_workspace_subtitle(self, mock_subtitle_workspace):
        mock_subtitle_workspace.return_value = [
            {"lang": "ko", "srt_path": "/tmp/subtitles_ko.srt", "json_path": "/tmp/subtitles_ko.json"},
            {"lang": "en", "srt_path": "/tmp/subtitles_en.srt", "json_path": "/tmp/subtitles_en.json"},
        ]
        resp = client.post("/scenarios/workspace/sess-1/subtitles")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        assert body[0]["lang"] == "ko"
        assert body[1]["srt_path"] == "/tmp/subtitles_en.srt"

    @patch("app.routes.scenarios.thumbnail_workspace")
    def test_scenario_workspace_thumbnail(self, mock_thumbnail_workspace):
        mock_thumbnail_workspace.return_value = {
            "draft_images": ["/tmp/draft_1.png", "/tmp/draft_2.png"],
            "final_image": "/tmp/final.png",
            "overlay_used": True,
            "save_path": "/tmp/thumbs",
        }
        resp = client.post("/scenarios/workspace/sess-1/thumbnail")
        assert resp.status_code == 200
        body = resp.json()
        assert body["final_image"] == "/tmp/final.png"
        assert body["overlay_used"] is True
        assert len(body["draft_images"]) == 2


class TestResearch:
    @patch("app.routes.research.create_from_url")
    def test_research_create_url(self, mock_create):
        mock_create.return_value = {
            "session_id": "s1",
            "mode": "url",
            "category": "economy",
            "source": {"type": "article", "title": "기사", "url": "https://example.com", "summary": "요약", "keywords": ["금리"]},
            "articles": [],
            "videos": [],
        }
        resp = client.post("/research/sessions", json={"mode": "url", "url": "https://example.com", "category": "economy"})
        assert resp.status_code == 200
        assert resp.json()["mode"] == "url"

    @patch("app.routes.research.create_from_category")
    def test_research_create_category(self, mock_create):
        mock_create.return_value = {
            "session_id": "s2",
            "mode": "category",
            "category": "부동산",
            "source": {"type": "article", "title": "부동산 최신 이슈", "url": "", "summary": "", "keywords": ["부동산"]},
            "articles": [],
            "videos": [],
        }
        resp = client.post("/research/sessions", json={"mode": "category", "category": "부동산"})
        assert resp.status_code == 200
        assert resp.json()["category"] == "부동산"

    @patch("app.routes.research.expand_session")
    def test_research_expand(self, mock_expand):
        mock_expand.return_value = {
            "session_id": "s2",
            "mode": "category",
            "category": "부동산",
            "source": {"type": "article", "title": "부동산 최신 이슈", "url": "", "summary": "", "keywords": ["부동산"]},
            "articles": [],
            "videos": [],
        }
        resp = client.post("/research/sessions/expand", json={"session_id": "s2", "article_ids": ["a1"], "video_ids": ["v1"]})
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "s2"

    @patch("app.routes.research.Session")
    def test_research_get(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            id="s3", mode="category", category="경제", source_title="경제 이슈", source_url="", source_summary="요약", source_keywords=["경제"]
        )
        empty_result = MagicMock()
        empty_result.all.return_value = []
        mock_session.exec.side_effect = [empty_result, empty_result]
        resp = client.get("/research/sessions/s3")
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "s3"


# ── Reviews ─────────────────────────────────────────────────────────────


class TestReviews:
    @patch("app.modules.review.reviewer.llm")
    def test_reviews_passed(self, mock_llm_factory):
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "passed": True, "issues": [], "fix_suggestions": [],
        }
        mock_llm_factory.return_value = mock_client

        payload = {
            "topic": "금리 인하",
            "scenario": {
                "hook": "훅", "body": ["본론"], "conclusion": "결론",
                "cta": "CTA", "title_candidates": ["제목"],
                "thumbnail_candidates": ["썸네일"],
            },
        }
        resp = client.post("/reviews", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed"] is True
        assert body["issues"] == []

    @patch("app.modules.review.reviewer.llm")
    def test_reviews_failed(self, mock_llm_factory):
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "passed": False,
            "issues": ["근거 부족", "톤 불일치"],
            "fix_suggestions": ["데이터 추가", "톤 수정"],
        }
        mock_llm_factory.return_value = mock_client

        payload = {
            "topic": "금리 인하",
            "scenario": {
                "hook": "훅", "body": ["본론"], "conclusion": "결론",
                "cta": "CTA", "title_candidates": ["제목"],
                "thumbnail_candidates": ["썸네일"],
            },
        }
        resp = client.post("/reviews", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed"] is False
        assert len(body["issues"]) == 2
        assert len(body["fix_suggestions"]) == 2

    def test_reviews_missing_scenario(self):
        resp = client.post("/reviews", json={"topic": "금리"})
        assert resp.status_code == 422


# ── 404 / Method Not Allowed ────────────────────────────────────────────


class TestMisc:
    def test_not_found(self):
        resp = client.get("/nonexistent")
        assert resp.status_code == 404

    def test_topics_get_not_allowed(self):
        resp = client.get("/topics")
        assert resp.status_code == 405
