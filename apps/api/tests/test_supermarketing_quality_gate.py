from app.modules.narration import narrator
from app.modules.scenario import generator
from app.modules.topic import selector
from app.schemas import NarrationInput, ScenarioInput, ScenarioOutput, TopicInput


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def generate_json(self, system: str, user: str):
        self.calls.append({"system": system, "user": user})
        return self.payload


def test_topic_prompt_uses_supermarketing_haico_sukgo_gate(monkeypatch):
    fake = FakeLLM(
        {
            "recommended_topics": [
                {
                    "title": "금리보다 먼저 봐야 할 전세 신호",
                    "reason": "실수요 판단에 직접 연결됩니다.",
                    "score": {
                        "popularity": 5,
                        "economy": 5,
                        "realestate": 5,
                        "virality": 5,
                        "richgo_fit": 5,
                        "discussion": 5,
                    },
                    "risk": "과장된 매수 신호로 오해될 수 있습니다.",
                    "archetype": "판단형",
                    "keywords": ["금리", "전세", "집값"],
                    "discovery_hypothesis": "전세 신호가 매수 판단을 바꾸는지 확인합니다.",
                    "strategy_hypothesis": "리치고의 데이터 판단 포지션을 강화합니다.",
                    "tactical_hypothesis": "첫 30초에 전세-매매 연결을 보여줍니다.",
                    "verification_signals": ["CTR", "유지율", "댓글"],
                    "failure_criteria": ["초반 이탈"],
                    "decision_label": "scale",
                    "next_loop": "성과 댓글로 다음 각도를 재검증합니다.",
                }
            ],
            "selected_topic": "금리보다 먼저 봐야 할 전세 신호",
            "selected_reason": "가설과 검증 신호가 가장 선명합니다.",
            "selected_archetype": "판단형",
        }
    )
    monkeypatch.setattr(selector, "llm", lambda temperature=0.5: fake)

    selector.select_topic(TopicInput(current_issues=["전세가 상승"], trend_keywords=["금리", "전세"]))

    prompt = fake.calls[0]["user"]
    assert "Supermarketing" in prompt
    assert "HAICo" in prompt
    assert "sukgo" in prompt or "숙고" in prompt
    assert "발산" in prompt
    assert "실패 기준" in prompt


def test_scenario_prompt_uses_supermarketing_haico_sukgo_and_10min_gate(monkeypatch):
    fake = FakeLLM(
        {
            "hook": "훅",
            "hook_30s": "30초 훅",
            "bridge_3min": "3분 브릿지",
            "body": ["본문"],
            "body_sections": [{"heading": "본문", "script": "짧은 본문", "narration": "짧은 본문"}],
            "conclusion": "결론",
            "cta": "CTA",
            "title_candidates": ["제목"],
            "thumbnail_candidates": ["썸네일"],
            "estimated_duration_min": 10,
            "archetype": "판단형",
        }
    )
    monkeypatch.setattr(generator, "llm", lambda temperature=0.6: fake)

    generator.generate_scenario(ScenarioInput(topic="금리와 집값", keywords=["금리"], target_duration_min=10))

    prompt = fake.calls[0]["user"]
    assert "Supermarketing" in prompt
    assert "HAICo" in prompt
    assert "sukgo" in prompt or "숙고" in prompt
    assert "최소 4,500자" in prompt


def test_narration_enforces_10_minimum_when_llm_returns_short(monkeypatch, tmp_path):
    scenario = ScenarioOutput(
        hook="집값 판단 기준을 보겠습니다.",
        hook_30s="오늘은 금리보다 먼저 봐야 할 신호를 보겠습니다.",
        bridge_3min="뉴스와 실제 시장을 분리해야 합니다.",
        body=["본문"],
        body_sections=[
            {
                "heading": "전세 신호",
                "summary": "전세와 매매 연결",
                "script": "전세가 움직이면 매매 판단도 달라집니다. 실수요자는 월 부담을 먼저 봐야 합니다.",
                "narration": "전세가 움직이면 매매 판단도 달라집니다. 실수요자는 월 부담을 먼저 봐야 합니다.",
            }
        ],
        conclusion="기준을 가지고 대응해야 합니다.",
        cta="댓글로 관심 지역을 남겨주세요.",
        title_candidates=["제목"],
        thumbnail_candidates=["썸네일"],
        estimated_duration_min=10,
    )
    fake = FakeLLM({"text_ko": "너무 짧은 나레이션입니다.", "sentences": ["너무 짧은 나레이션입니다."]})
    monkeypatch.setattr(narrator, "llm", lambda temperature=0.4: fake)
    monkeypatch.setattr(narrator, "workspace_dir", lambda run_id, kind: tmp_path / run_id / kind)
    monkeypatch.setattr(narrator, "_azure_tts", lambda text, sentences, out_dir: (_ for _ in ()).throw(RuntimeError("skip")))

    result = narrator.generate_narration("run-1", NarrationInput(scenario=scenario, expected_length_sec=600))

    assert len(result.text_ko) >= 4500
    assert "Supermarketing" not in result.text_ko
    assert "실수요자" in result.text_ko
    assert len(result.sentences) > 20
