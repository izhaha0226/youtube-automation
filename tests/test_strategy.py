from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.db import init_db  # noqa: E402

with patch("app.core.db.init_db"):
    from app.main import app  # noqa: E402

client = TestClient(app)


def test_strategy_schema_exposes_supabase_contract():
    resp = client.get("/strategy/schema")
    assert resp.status_code == 200
    body = resp.json()
    assert "Supabase" in body["storage_target"]
    assert body["pc_layout"]["columns"] == 2
    assert body["pc_layout"]["right"] is None
    assert any(table["name"] == "topic_recommendation" for table in body["tables"])


def test_strategy_session_issue_topic_and_command_center_flow():
    init_db()

    session_resp = client.post(
        "/strategy/sessions",
        json={"channel": "리치고", "selected_issue_title": "금리 인하와 서울 아파트 매수심리"},
    )
    assert session_resp.status_code == 200
    session = session_resp.json()
    session_id = session["session_id"]
    assert session["context"]["right_panel"] == "disabled"
    assert session["selected_issue_id"].startswith("issue_")

    issue_resp = client.post(
        f"/strategy/sessions/{session_id}/issues",
        json={
            "title": "전세대출 규제 완화",
            "summary": "실수요자 대출 규제 변화가 시장 심리에 미치는 영향",
            "category": "금리·대출",
            "keywords": ["전세대출", "DSR", "실수요"],
            "urgency_score": 82,
            "richgo_fit_score": 88,
        },
    )
    assert issue_resp.status_code == 200
    issue_id = issue_resp.json()["id"]

    topic_resp = client.post(
        f"/strategy/sessions/{session_id}/topics",
        json={
            "issue_id": issue_id,
            "title": "전세대출 완화, 집값보다 먼저 봐야 할 3가지",
            "angle": "정책 변화의 착시와 실수요 체크리스트",
            "score_hexagon": {
                "trend_fit": 87,
                "view_potential": 80,
                "hook_power": 84,
                "target_clarity": 90,
                "richgo_philosophy_fit": 93,
                "production_ease": 76,
            },
        },
    )
    assert topic_resp.status_code == 200
    topic = topic_resp.json()
    assert topic["total_score"] == 510

    select_resp = client.post(
        f"/strategy/sessions/{session_id}/select",
        params={"target_type": "topic", "target_id": topic["id"]},
    )
    assert select_resp.status_code == 200
    assert select_resp.json()["ok"] is True

    command_resp = client.get(f"/strategy/sessions/{session_id}/command-center")
    assert command_resp.status_code == 200
    command = command_resp.json()
    assert command["layout"]["right"] is None
    assert command["left_layer"]["evidence_mode"] == "accordion_in_left_layer_or_center_drawer"
    assert command["session"]["selected_topic_id"] == topic["id"]
    assert len(command["issues"]) >= 2
    assert any(item["id"] == topic["id"] for item in command["topic_recommendations"])
