from app.core.llm import LLMError
from app.modules.topic import selector
from app.schemas import TopicInput


def test_select_topic_returns_deterministic_fallback_when_llm_unavailable(monkeypatch):
    class BrokenLLM:
        def generate_json(self, system: str, user: str):
            raise LLMError("codex unavailable")

    monkeypatch.setattr(selector, "llm", lambda temperature=0.4: BrokenLLM())

    result = selector.select_topic(
        TopicInput(
            user_intent="오늘 바로 촬영 가능한 부동산 영상",
            current_issues=["[ARTICLE] 서울 아파트 전세대출 금리 다시 오른다"],
            trend_keywords=["금리", "아파트", "전세대출"],
        )
    )

    assert len(result.recommended_topics) == 3
    assert result.selected_topic == result.recommended_topics[0].title
    assert "서울 아파트 전세대출 금리" in result.selected_topic
    assert result.selected_archetype == "판단형"
