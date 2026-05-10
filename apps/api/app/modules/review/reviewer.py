from __future__ import annotations

from app.core.llm import LLMError, llm
from app.core.logging import get_logger
from app.core.prompts import load_prompt, render
from app.modules.richgo.editorial import editorial_rules_context, philosophy_context
from app.schemas import ReviewInput, ReviewOutput

log = get_logger(__name__)


def review_scenario(payload: ReviewInput) -> ReviewOutput:
    system = "You are a strict reviewer for the 리치고 channel. Output JSON only."
    user = render(
        load_prompt("review"),
        topic=payload.topic,
        scenario_json=payload.scenario.model_dump_json(),
        kim_kiwon_philosophy=philosophy_context(),
        editorial_rules=editorial_rules_context(),
    )
    try:
        data = llm(temperature=0.2).generate_json(system=system, user=user)
    except LLMError as e:
        log.warning("review.fallback", error=str(e), topic=payload.topic)
        return _fallback_review(payload)
    out = ReviewOutput(
        passed=bool(data.get("passed", False)),
        issues=data.get("issues", []),
        fix_suggestions=data.get("fix_suggestions", []),
    )
    log.info("review.done", passed=out.passed, issues=len(out.issues))
    return out


def _fallback_review(payload: ReviewInput) -> ReviewOutput:
    issues: list[str] = []
    fix_suggestions: list[str] = []
    if len(payload.scenario.body_sections) < 3:
        issues.append("본문 섹션 수가 부족합니다.")
        fix_suggestions.append("본문을 최소 3개 이상 섹션으로 나눠 근거와 판단 포인트를 분리하세요.")
    missing_narration = [section.heading or f"섹션 {idx + 1}" for idx, section in enumerate(payload.scenario.body_sections) if not section.narration.strip()]
    if missing_narration:
        issues.append(f"나레이션 누락 섹션: {', '.join(missing_narration[:3])}")
        fix_suggestions.append("각 본문 섹션에 실제 읽을 구어체 나레이션을 함께 채우세요.")
    if not payload.scenario.action_takeaways:
        issues.append("액션 포인트가 없습니다.")
        fix_suggestions.append("시청자가 바로 점검할 체크리스트를 3개 이상 추가하세요.")
    return ReviewOutput(
        passed=len(issues) == 0,
        issues=issues,
        fix_suggestions=fix_suggestions,
    )
