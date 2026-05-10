from app.modules.topic import selector
from app.schemas import TopicInput


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload

    def generate_json(self, system: str, user: str):
        return self.payload


def _candidate(title: str, total_score: int, **extra):
    # Six-axis total = total_score. Keep the first axis variable and the rest zero
    # so the threshold behavior is easy to reason about in the test.
    return {
        "title": title,
        "reason": f"{title} reason",
        "score": {
            "popularity": total_score,
            "economy": 0,
            "realestate": 0,
            "virality": 0,
            "richgo_fit": 0,
            "discussion": 0,
        },
        "risk": "risk",
        "archetype": "판단형",
        "keywords": ["금리", "부동산"],
        **extra,
    }


def test_select_topic_keeps_selected_topic_inside_filtered_recommendations(monkeypatch):
    payload = {
        "recommended_topics": [
            _candidate("필터링되어야 하는 낮은 점수 주제", 10, decision_label="scale"),
            _candidate(
                "실제 추천 가능한 주제",
                20,
                discovery_hypothesis="금리 이슈가 실수요 판단에 직접 영향을 준다.",
                strategy_hypothesis="리치고의 데이터 기반 판단 포지션을 강화한다.",
                tactical_hypothesis="첫 30초에 금리-대출-집값 연결을 숫자로 제시한다.",
                verification_signals=["CTR", "유지율", "댓글"],
                failure_criteria=["CTR 3% 미만", "초반 이탈률 급증"],
                decision_label="iterate",
                next_loop="업로드 후 CTR/유지율로 제목 각도를 재검증한다.",
                hypothesis_payload={"source": "unit-test"},
            ),
        ],
        "selected_topic": "필터링되어야 하는 낮은 점수 주제",
        "selected_reason": "LLM이 낮은 점수 주제를 골랐지만 API는 필터링 결과와 맞춰야 한다.",
        "selected_archetype": "경고형",
    }
    monkeypatch.setattr(selector, "llm", lambda temperature=0.4: FakeLLM(payload))

    result = selector.select_topic(
        TopicInput(current_issues=["금리 인하 기대"], trend_keywords=["금리", "부동산"])
    )

    assert [topic.title for topic in result.recommended_topics] == ["실제 추천 가능한 주제"]
    assert result.selected_topic == "실제 추천 가능한 주제"
    assert result.selected_reason == "실제 추천 가능한 주제 reason"
    assert result.selected_archetype == "판단형"
    selected = result.recommended_topics[0]
    assert selected.discovery_hypothesis
    assert selected.strategy_hypothesis
    assert selected.tactical_hypothesis
    assert selected.verification_signals == ["CTR", "유지율", "댓글"]
    assert selected.failure_criteria == ["CTR 3% 미만", "초반 이탈률 급증"]
    assert selected.decision_label == "iterate"
    assert selected.next_loop
    assert selected.hypothesis_payload == {"source": "unit-test"}
