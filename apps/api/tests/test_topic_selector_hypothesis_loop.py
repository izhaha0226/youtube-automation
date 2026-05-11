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


def test_select_topic_rewrites_news_copy_title_into_hook_topic(monkeypatch):
    source_title = "서울 아파트 전세대출 금리 다시 오른다"
    payload = {
        "recommended_topics": [
            _candidate(
                source_title,
                24,
                discovery_hypothesis="전세대출 금리 이슈가 실수요 판단에 직접 영향을 준다.",
                strategy_hypothesis="뉴스를 리치고 데이터 기반 판단 프레임으로 재구성한다.",
                tactical_hypothesis="첫 30초에 금리-월상환액-집값 선택지를 제시한다.",
                verification_signals=["CTR", "유지율", "댓글"],
                failure_criteria=["뉴스 복붙 반응", "CTR 저조"],
                decision_label="scale",
                next_loop="제목 후킹 각도와 유지율을 비교한다.",
            )
        ],
        "selected_topic": source_title,
        "selected_reason": "뉴스 제목을 그대로 낸 잘못된 LLM 응답",
        "selected_archetype": "판단형",
    }
    monkeypatch.setattr(selector, "llm", lambda temperature=0.5: FakeLLM(payload))

    result = selector.select_topic(
        TopicInput(current_issues=[f"[ARTICLE] {source_title}"], trend_keywords=["금리", "아파트", "전세대출"])
    )

    assert result.selected_topic != source_title
    assert result.recommended_topics[0].title == result.selected_topic
    assert "뉴스 제목은 이게 아닙니다" not in result.selected_topic
    assert any(token in result.selected_topic for token in ["모르는", "놓치면", "갈리는", "반전"])
    assert "내 집값" in result.selected_topic
