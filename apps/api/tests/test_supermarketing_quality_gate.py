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
    assert "supermarketing-aimtop" in prompt
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
    assert "supermarketing-aimtop" in prompt
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


def test_topic_result_contains_per_video_analysis_and_application(monkeypatch):
    fake = FakeLLM({
        "video_analyses": [
            {
                "title": "서울 집값 영상",
                "content_summary": "5.9 대책 이후 서울 집값 판단 기준을 설명합니다.",
                "duration": "18:20",
                "production_intent": "정책 직후 불안한 실수요자의 매수/대기 판단을 돕기 위해 제작된 영상입니다.",
                "most_watched_time": "data_missing",
                "most_watched_scene": "가장 많이 시청한 장면 데이터 없음",
                "hook_takeaway": "정책 직후 결론을 먼저 던지고 근거를 뒤에 배치합니다.",
            }
        ],
        "production_application": {
            "opening_strategy": "우리 영상은 첫 10초에 '지금 사도 되는 사람/기다려야 하는 사람'을 먼저 나눠서 도입합니다.",
            "structure_strategy": "선택 영상의 정책 해설 구조를 리치고 데이터 기준표로 바꿉니다.",
            "scene_strategy": "retention 데이터가 없으므로 실제 장면은 지어내지 않고 제목·조회수·훅 구조만 차용합니다.",
            "topic_generation_basis": "선택 영상의 조회수, 분량, 제작의도, 도입부 구조를 주제 후보에 반영합니다.",
        },
        "recommended_topics": [{
            "title": "조회수 높은 영상 도입부를 변환한 부동산 판단 기준",
            "reason": "선택 영상의 조회수와 훅 구조를 근거로 도입부를 설계합니다.",
            "score": {"popularity": 5, "economy": 4, "realestate": 5, "virality": 4, "richgo_fit": 5, "discussion": 4},
            "risk": "가장 많이 시청한 장면 데이터 없음",
            "archetype": "판단형",
            "keywords": ["부동산"],
            "discovery_hypothesis": "선택 영상 근거",
            "strategy_hypothesis": "리치고 변환",
            "tactical_hypothesis": "첫 10초 훅, 첫 30초 문제 제기, 1분 내 데이터 제시",
            "verification_signals": ["CTR", "유지율"],
            "failure_criteria": ["가장 많이 시청한 장면 데이터 없음"],
            "decision_label": "iterate",
            "next_loop": "실제 유지율 확인",
        }],
        "selected_topic": "조회수 높은 영상 도입부를 변환한 부동산 판단 기준",
        "selected_reason": "선택 영상 기반",
        "selected_archetype": "판단형",
    })
    monkeypatch.setattr(selector, "llm", lambda temperature=0.5: fake)

    result = selector.select_topic(TopicInput(
        current_issues=["[VIDEO] &#39;서울 집값&#39;"],
        trend_keywords=["부동산"],
        selected_videos=[{"title": "&#39;서울 집값&#39;", "channel": "A", "views": 24000, "duration": "18:20", "creative_analysis": {"hook_type": "informational", "score": 8}}],
    ))

    prompt = fake.calls[0]["user"]
    assert "선택 영상 분석 원본" in prompt
    assert "video-analysis" in prompt
    assert "24000" in prompt
    assert "가장 많이 시청한 장면 데이터 없음" in prompt
    assert "video_analyses" in prompt
    assert "production_application" in prompt
    assert len(result.video_analyses) == 1
    assert result.video_analyses[0].title == "서울 집값 영상"
    assert result.video_analyses[0].duration == "18:20"
    assert "data_missing" in result.video_analyses[0].most_watched_time
    assert "첫 10초" in result.production_application.opening_strategy


def test_topic_rejects_video_issue_without_selected_video_data():
    try:
        selector.select_topic(TopicInput(current_issues=["[VIDEO] 제목만 있음"], trend_keywords=["부동산"]))
    except ValueError as exc:
        assert "선택 영상 원본 데이터" in str(exc)
    else:
        raise AssertionError("영상 원본 없이 주제를 만들면 안 됩니다.")


def test_topic_rejects_more_than_three_selected_videos():
    videos = [{"title": f"영상 {idx}", "channel": "A", "views": 1000} for idx in range(4)]
    try:
        selector.select_topic(TopicInput(
            current_issues=[f"[VIDEO] 영상 {idx}" for idx in range(4)],
            trend_keywords=["부동산"],
            selected_videos=videos,
        ))
    except ValueError as exc:
        assert "최대 3개" in str(exc)
    else:
        raise AssertionError("선택 영상 4개 이상은 차단해야 합니다.")
