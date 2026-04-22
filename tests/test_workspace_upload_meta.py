from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from fastapi.testclient import TestClient

with patch("app.core.db.init_db"):
    from app.main import app

client = TestClient(app)


def _mock_upload_meta():
    return {
        "title": "금리보다 더 중요한 변수, 지금 집값을 가르는 신호",
        "description": "요약\n\n본문 포인트\n\nCTA",
        "tags": ["금리", "부동산", "리치고"],
        "hashtags": ["#금리", "#부동산", "#리치고"],
        "pinned_comment": "여러분 지역은 어떤가요?",
    }


class TestWorkspaceUploadMeta:
    @patch("app.routes.scenarios.upload_meta_workspace")
    def test_scenario_workspace_upload_meta(self, mock_upload_meta_workspace):
        mock_upload_meta_workspace.return_value = _mock_upload_meta()

        resp = client.post("/scenarios/workspace/sess-1/upload-meta")
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"].startswith("금리보다")
        assert body["tags"] == ["금리", "부동산", "리치고"]
        assert body["pinned_comment"] == "여러분 지역은 어떤가요?"


class TestUploadMetaPromptFlow:
    @patch("app.modules.upload.meta.llm")
    def test_upload_meta_prompt_includes_editorial_context(self, mock_llm_factory):
        from app.modules.upload.meta import build_upload_meta
        from app.schemas import ScenarioOutput

        mock_client = MagicMock()
        mock_client.generate_json.return_value = _mock_upload_meta()
        mock_llm_factory.return_value = mock_client

        build_upload_meta(
            "sess-1",
            "금리보다 더 중요한 변수",
            ScenarioOutput(
                hook="훅",
                hook_30s="30초 훅",
                bridge_3min="3분 브릿지",
                archetype="판단형",
                body=["본문1"],
                body_sections=[{"heading": "핵심", "script": "설명"}],
                conclusion="결론",
                action_takeaways=["체크포인트"],
                cta="댓글 남겨주세요",
                title_candidates=["제목1"],
                thumbnail_candidates=["썸네일1"],
                opening="오프닝",
                opening_title="오프닝 타이틀",
                estimated_duration_min=11,
            ),
        )

        user_prompt = mock_client.generate_json.call_args.kwargs["user"]
        assert "통제력과 영향력" in user_prompt
        assert "판단형" in user_prompt
        assert "실수요" in user_prompt
