from app.core.llm import LLMError
from app.modules.scenario import generator
from app.schemas import ScenarioInput


def test_generate_scenario_returns_fallback_when_llm_unavailable(monkeypatch):
    class BrokenLLM:
        def generate_json(self, system: str, user: str):
            raise LLMError("codex CLI not installed")

    monkeypatch.setattr(generator, "llm", lambda temperature=0.6: BrokenLLM())

    result = generator.generate_scenario(
        ScenarioInput(
            topic="서울 집값, 지금 사도 되는지 기다려야 하는지 판단 기준 3가지",
            archetype="판단형",
            keywords=["부동산", "금리", "서울"],
            selected_articles=[
                {"title": "서울 아파트 거래량이 다시 늘었다"},
                {"title": "전세대출 금리 변화가 시장에 미치는 영향"},
                {"title": "정책 완화 이후 지역별 온도차 확대"},
            ],
            target_duration_min=10,
            target_duration_max=12,
        )
    )

    assert result.hook
    assert result.hook_30s
    assert result.body_sections
    assert len(result.body) == len(result.body_sections)
    assert all(section.narration for section in result.body_sections)
    assert result.title_candidates
    assert result.thumbnail_candidates
    assert result.archetype == "판단형"
    assert "부동산" in result.hook_30s
    assert len(result.body_sections) >= 6
    joined = "\n".join(section.narration for section in result.body_sections)
    assert "뉴스" in joined
    assert "실수요" in joined
    assert "서울 아파트 거래량이 다시 늘었다" in joined
    assert len(joined) > 2500
