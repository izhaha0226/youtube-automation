from app.core.llm import LLMError
from app.modules.narration import narrator
from app.modules.review import reviewer
from app.schemas import NarrationInput, ReviewInput, ScenarioOutput


def _scenario() -> ScenarioOutput:
    return ScenarioOutput(
        hook="훅",
        hook_30s="오늘은 이 이슈를 봐야 합니다.",
        bridge_3min="그래서 내 집값 판단에 왜 중요한지 보겠습니다.",
        archetype="판단형",
        body=["요약1", "요약2", "요약3"],
        body_sections=[
            {"heading": "섹션1", "script": "첫 번째 대본입니다.", "narration": "첫 번째 나레이션입니다."},
            {"heading": "섹션2", "script": "두 번째 대본입니다.", "narration": "두 번째 나레이션입니다."},
            {"heading": "섹션3", "script": "세 번째 대본입니다.", "narration": "세 번째 나레이션입니다."},
        ],
        conclusion="결론입니다.",
        action_takeaways=["체크1", "체크2", "체크3"],
        cta="댓글로 지역을 남겨주세요.",
        title_candidates=["제목1"],
        thumbnail_candidates=["썸네일"],
        opening="바로 시작하겠습니다.",
        opening_title="오프닝 제목",
        estimated_duration_min=10,
    )


def test_review_returns_fallback_when_llm_unavailable(monkeypatch):
    class BrokenLLM:
        def generate_json(self, system: str, user: str):
            raise LLMError("codex CLI not installed")

    monkeypatch.setattr(reviewer, "llm", lambda temperature=0.2: BrokenLLM())

    result = reviewer.review_scenario(ReviewInput(scenario=_scenario(), topic="테스트 주제"))

    assert result.passed is True
    assert result.issues == []
    assert 0 <= result.tone_structure_difference_percent <= 100
    assert "지난 영상" in result.tone_structure_comment
    assert "구조" in result.structure_recommendation
    assert result.recommended_action in {"keep_content_adjust_structure", "keep_structure_adjust_tone", "pass"}


def test_narration_returns_fallback_when_llm_unavailable(monkeypatch, tmp_path):
    class BrokenLLM:
        def generate_json(self, system: str, user: str):
            raise LLMError("codex CLI not installed")

    monkeypatch.setattr(narrator, "llm", lambda temperature=0.4: BrokenLLM())
    monkeypatch.setattr(narrator, "workspace_dir", lambda run_id, name: tmp_path / run_id / name)

    result = narrator.generate_narration("test-run", NarrationInput(scenario=_scenario()))

    assert "첫 번째 나레이션입니다." in result.text_ko
    assert result.sentences
    assert result.timeline
    assert result.audio_path is None
