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
            target_duration_min=10,
            target_duration_max=12,
        )
    )

    assert result.hook
    assert result.hook_30s
    assert result.body_sections
    assert len(result.body) == len(result.body_sections)
    assert result.title_candidates
    assert result.thumbnail_candidates
    assert result.archetype == "판단형"
    assert "부동산" in result.hook_30s
