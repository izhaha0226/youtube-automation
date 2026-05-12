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
    assert "부동산 · 금리 · 서울 때문에" not in result.hook_30s
    assert "키워드를 따라가는 게 아니라" in result.hook_30s
    assert len(result.body_sections) >= 6
    joined = "\n".join(section.narration for section in result.body_sections)
    assert "뉴스" in joined
    assert "실수요" in joined
    assert "서울 아파트 거래량이 다시 늘었다" in joined
    assert len(joined) > 2500
    assert "리치고식" not in joined
    assert any("리치고 데이터" in section.heading for section in result.body_sections)
    assert any("리치고 데이터를 확인" in section.narration for section in result.body_sections)


def test_scenario_prompt_sets_kim_kiwon_speaker_and_data_section(monkeypatch):
    class FakeLLM:
        def __init__(self):
            self.calls = []

        def generate_json(self, system: str, user: str):
            self.calls.append({"system": system, "user": user})
            return {
                "hook": "훅",
                "hook_30s": "30초 훅",
                "bridge_3min": "3분 브릿지",
                "body": ["요약"],
                "body_sections": [{"heading": "리치고 데이터 확인", "script": "리치고 데이터를 확인합니다.", "narration": "리치고 데이터를 확인합니다."}],
                "conclusion": "결론",
                "cta": "CTA",
                "title_candidates": ["제목"],
                "thumbnail_candidates": ["썸네일"],
                "estimated_duration_min": 10,
                "archetype": "판단형",
            }

    fake = FakeLLM()
    monkeypatch.setattr(generator, "llm", lambda temperature=0.6: fake)

    generator.generate_scenario(ScenarioInput(topic="전세와 매매 판단", keywords=["전세"]))

    prompt = fake.calls[0]["user"]
    assert "김기원 대표가 직접 말하는 1인칭" in prompt
    assert "리치고식" in prompt and "금지" in prompt
    assert "리치고 데이터 확인 및 분석" in prompt
    assert "키워드를 나열해 훅 문장으로 만들면 실패" in prompt
    assert "시청자 불안/오해 → 오늘 볼 판단 기준 → 얻는 이익" in prompt
    assert "시청자 욕망/불안 + 숨은 긴장 + 판단 이익" in prompt


def test_scenario_supermarketing_audit_rewrites_weak_llm_output(monkeypatch):
    class WeakLLM:
        def generate_json(self, system: str, user: str):
            return {
                "hook": "부동산 · 데이터분석 · 리치고 때문에 시장이 헷갈립니다.",
                "hook_30s": "부동산 · 데이터분석 · 리치고 때문에 시장이 헷갈립니다. 오늘은 기준을 보겠습니다.",
                "bridge_3min": "짧은 브릿지",
                "body": ["짧은 본문"],
                "body_sections": [{"heading": "본문", "script": "짧은 본문", "narration": "짧은 본문"}],
                "conclusion": "결론",
                "cta": "댓글 남겨주세요.",
                "title_candidates": ["제목"],
                "thumbnail_candidates": ["썸네일"],
                "estimated_duration_min": 10,
                "archetype": "판단형",
            }

    monkeypatch.setattr(generator, "llm", lambda temperature=0.6: WeakLLM())

    result = generator.generate_scenario(
        ScenarioInput(
            topic="토허구역 전세 낀 집, 대부분 아직 모르는 내 집값 신호 3가지",
            keywords=["부동산", "데이터분석", "리치고"],
            target_duration_min=10,
        )
    )

    joined = "\n".join(section.narration for section in result.body_sections)
    assert "부동산 · 데이터분석 · 리치고 때문에" not in result.hook_30s
    assert "키워드를 따라가는 게 아니라" in result.hook_30s
    assert len(result.title_candidates) == 5
    assert all(title != "제목" for title in result.title_candidates)
    assert any("기다릴" in title or "놓치는" in title for title in result.title_candidates)
    assert len(result.body_sections) >= 6
    assert len(joined) > 2500
    assert any("리치고 데이터" in section.heading for section in result.body_sections)
