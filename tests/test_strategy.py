from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.db import get_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def isolated_client(tmp_path: Path) -> Iterator[TestClient]:
    db_path = tmp_path / "strategy.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_strategy_schema_exposes_supabase_contract():
    client = TestClient(app)
    resp = client.get("/strategy/schema")
    assert resp.status_code == 200
    body = resp.json()
    assert "Supabase" in body["storage_target"]
    assert body["pc_layout"]["columns"] == 2
    assert body["pc_layout"]["right"] is None
    assert any(table["name"] == "topic_recommendation" for table in body["tables"])
    assert any(contract["path"].endswith("/validations") for contract in body["api_contracts"])
    assert any(contract["path"].endswith("/scenarios") for contract in body["api_contracts"])


def test_strategy_session_issue_topic_and_command_center_flow(isolated_client: TestClient):
    client = isolated_client
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


def test_strategy_storage_contract_roundtrip(isolated_client: TestClient):
    client = isolated_client
    session_resp = client.post(
        "/strategy/sessions",
        json={"channel": "리치고", "selected_issue_title": "강남 집값 반등"},
    )
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    issue_id = session_resp.json()["selected_issue_id"]

    validation_resp = client.post(
        f"/strategy/sessions/{session_id}/validations",
        json={
            "issue_id": issue_id,
            "provider": "naver",
            "keyword": "강남 집값",
            "score": 88,
            "basis": "검색량 급증",
        },
    )
    assert validation_resp.status_code == 200

    news_resp = client.post(
        f"/strategy/sessions/{session_id}/news",
        json={
            "issue_id": issue_id,
            "title": "강남 주요 단지 신고가",
            "source": "테스트뉴스",
            "stance": "neutral",
        },
    )
    assert news_resp.status_code == 200

    benchmark_resp = client.post(
        f"/strategy/sessions/{session_id}/benchmarks",
        json={
            "issue_id": issue_id,
            "title": "집값 반등인가 착시인가",
            "channel": "벤치마크채널",
            "views": 120000,
            "hook_pattern": "질문형 경고 훅",
            "success_factors": ["숫자", "논쟁"],
        },
    )
    assert benchmark_resp.status_code == 200

    topic_resp = client.post(
        f"/strategy/sessions/{session_id}/topics",
        json={
            "issue_id": issue_id,
            "title": "강남 반등, 전국 회복 신호인가",
            "angle": "착시와 구조적 회복 분리",
            "score_hexagon": {
                "trend_fit": 90,
                "view_potential": 86,
                "hook_power": 84,
                "target_clarity": 80,
                "richgo_philosophy_fit": 92,
                "production_ease": 75,
            },
        },
    )
    assert topic_resp.status_code == 200
    topic_id = topic_resp.json()["id"]

    scenario_resp = client.post(
        f"/strategy/sessions/{session_id}/scenarios",
        json={
            "topic_id": topic_id,
            "version": 1,
            "title": "강남 반등의 진짜 의미",
            "script_markdown": "# 오프닝\n강남 반등을 데이터로 봅니다.",
            "opening_30s": "반등인지 착시인지 30초 안에 보겠습니다.",
        },
    )
    assert scenario_resp.status_code == 200
    scenario_id = scenario_resp.json()["id"]

    select_resp = client.post(
        f"/strategy/sessions/{session_id}/select",
        params={"target_type": "scenario", "target_id": scenario_id},
    )
    assert select_resp.status_code == 200

    center_resp = client.get(f"/strategy/sessions/{session_id}/command-center")
    assert center_resp.status_code == 200
    center = center_resp.json()
    assert len(center["validations"]) == 1
    assert len(center["news_articles"]) == 1
    assert len(center["youtube_benchmarks"]) == 1
    assert len(center["topic_recommendations"]) == 1
    assert len(center["scenario_versions"]) == 1
    assert center["scenario_versions"][0]["opening_30s"].startswith("반등인지")
