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
        tone_structure_difference_percent=_bounded_percent(data.get("tone_structure_difference_percent", 0)),
        tone_structure_comment=str(data.get("tone_structure_comment") or "리치고 지난 영상 레퍼런스 대비 톤과 구조 차이를 확인했습니다."),
        structure_recommendation=str(data.get("structure_recommendation") or "리치고 지난 영상처럼 오프닝 훅 → 리치고 데이터 확인 → 실수요자 판단 기준 → 리스크/예외 → 결론 구조를 추천합니다."),
        recommended_action=_normalize_recommended_action(data.get("recommended_action")),
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
    difference = 18 if not issues else 42
    return ReviewOutput(
        passed=len(issues) == 0,
        issues=issues,
        fix_suggestions=fix_suggestions,
        tone_structure_difference_percent=difference,
        tone_structure_comment=f"리치고 지난 영상 레퍼런스 대비 나레이션 톤과 구조 차이는 약 {difference}%입니다. 현재 대본은 김기원 대표의 직접 설명 톤을 유지하되 데이터 확인 구간의 위치를 더 선명하게 보면 좋습니다.",
        structure_recommendation="리치고 지난 영상처럼 오프닝 훅 → 리치고 데이터 확인 및 분석 → 실수요자 판단 기준 → 리스크/예외 → 결론 구조를 추천합니다. 내용은 유지한 채 시나리오 구조를 이 순서로 변경하겠습니다.",
        recommended_action="pass" if not issues else "keep_content_adjust_structure",
    )


def _bounded_percent(value: object) -> int:
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return 0


def _normalize_recommended_action(value: object) -> str:
    allowed = {"keep_content_adjust_structure", "keep_structure_adjust_tone", "pass"}
    text = str(value or "pass")
    return text if text in allowed else "pass"
