from __future__ import annotations

import json

from app.core.config import settings
from app.core.llm import LLMError, llm
from app.core.logging import get_logger
from app.core.prompts import load_prompt, render
from app.modules.richgo.editorial import content_archetype_context, editorial_rules_context, philosophy_context
from app.modules.trend.scanner import scan  # used as fallback when no pre-fetched data
from app.schemas import TopicCandidate, TopicInput, TopicResult, TopicScore

log = get_logger(__name__)


def select_topic(payload: TopicInput) -> TopicResult:
    if payload.current_issues or payload.trend_keywords:
        current_issues = payload.current_issues
        trend_keywords = payload.trend_keywords
    else:
        snap = scan()
        current_issues = snap.as_current_issues()
        trend_keywords = snap.keywords()

    system = (
        "You are the topic-selection agent for the 리치고 channel. "
        "Follow the IO spec strictly. Output valid JSON only."
    )
    user = render(
        load_prompt("topic_select"),
        channel=payload.channel,
        user_intent=payload.user_intent or "(없음)",
        avoid_keywords=", ".join(payload.avoid_keywords) or "(없음)",
        must_include=", ".join(payload.must_include) or "(없음)",
        current_issues=json.dumps(current_issues, ensure_ascii=False),
        trend_keywords=", ".join(trend_keywords[:30]) or "(없음)",
        source_mode=("research-backed" if payload.current_issues or payload.trend_keywords else "trend-scan"),
        target_speed="오늘 바로 촬영 가능한 주제를 우선",
        kim_kiwon_philosophy=philosophy_context(),
        editorial_rules=editorial_rules_context(),
        content_archetype_guide=content_archetype_context(),
    )
    try:
        data = llm(temperature=0.5).generate_json(system=system, user=user)
    except LLMError as e:
        log.warning("topic.select.fallback", error=str(e))
        return _fallback_topic_result(payload, current_issues, trend_keywords)

    rules = settings.scoring_rules
    threshold_recommend = rules.get("thresholds", {}).get("recommend", 18)
    top_k = rules.get("top_k", 3)

    candidates = []
    for c in data.get("recommended_topics", []):
        score = TopicScore(**c.get("score", {}))
        if score.total() < threshold_recommend:
            continue
        decision_label = c.get("decision_label")
        if decision_label not in {"scale", "iterate", "stop", "data_missing"}:
            decision_label = "scale" if score.total() >= 24 else "iterate" if score.total() >= threshold_recommend else "stop"
        candidates.append(
            TopicCandidate(
                title=c.get("title", ""),
                reason=c.get("reason", ""),
                score=score,
                archetype=c.get("archetype", "판단형"),
                risk=c.get("risk", ""),
                keywords=c.get("keywords", []),
                discovery_hypothesis=c.get("discovery_hypothesis", c.get("reason", "")),
                strategy_hypothesis=c.get("strategy_hypothesis", c.get("reason", "")),
                tactical_hypothesis=c.get("tactical_hypothesis", c.get("risk", "")),
                verification_signals=c.get("verification_signals", []),
                failure_criteria=c.get("failure_criteria", []),
                decision_label=decision_label,
                next_loop=c.get("next_loop", ""),
                hypothesis_payload=c.get("hypothesis_payload", {}),
            )
        )
    candidates.sort(key=lambda c: c.score.total(), reverse=True)
    candidates = candidates[:top_k]

    selected = data.get("selected_topic") or (candidates[0].title if candidates else "")
    selected_candidate = next((candidate for candidate in candidates if candidate.title == selected), None)
    selected_was_filtered = selected_candidate is None and bool(candidates)
    if selected_was_filtered:
        selected_candidate = candidates[0]
        selected = selected_candidate.title

    reason = data.get("selected_reason") if not selected_was_filtered else ""
    reason = reason or (selected_candidate.reason if selected_candidate else "")
    selected_archetype = selected_candidate.archetype if selected_candidate else "판단형"

    result = TopicResult(
        recommended_topics=candidates,
        selected_topic=selected,
        selected_reason=reason,
        selected_archetype=selected_archetype,
    )
    log.info("topic.select.done", count=len(candidates), selected=selected)
    return result


def _fallback_topic_result(payload: TopicInput, current_issues: list[str], trend_keywords: list[str]) -> TopicResult:
    """Deterministic fallback so /api/topics does not 503 when Codex/LLM is unavailable."""
    primary_issue = _clean_issue(current_issues[0]) if current_issues else (payload.user_intent or "오늘 부동산 시장 핵심 변화")
    keywords = list(dict.fromkeys([kw for kw in trend_keywords[:8] if kw])) or ["부동산", "금리", "아파트"]
    focus = " · ".join(keywords[:3])
    templates = [
        ("판단형", f"{primary_issue}, 지금 사도 되는지 기다려야 하는지 판단 기준 3가지"),
        ("구조해설형", f"{focus} 신호로 보는 이번 부동산 시장 변화의 진짜 이유"),
        ("기회형", f"남들은 불안해할 때 기회가 생기는 조건, {keywords[0]}에서 확인해야 할 것"),
    ]
    candidates: list[TopicCandidate] = []
    for idx, (archetype, title) in enumerate(templates):
        score = TopicScore(popularity=4, economy=4, realestate=5, virality=4 - min(idx, 1), richgo_fit=5, discussion=4)
        candidates.append(
            TopicCandidate(
                title=title,
                reason="LLM 호출 실패 시에도 촬영을 멈추지 않도록 선택 이슈와 트렌드 키워드 기반으로 자동 생성한 후보입니다.",
                score=score,
                archetype=archetype,
                risk="실시간 근거와 실제 데이터 확인 후 표현 강도를 조정해야 합니다.",
                keywords=keywords[:5],
                discovery_hypothesis=f"{focus} 조합은 오늘 시청자가 바로 판단하고 싶은 문제와 연결됩니다.",
                strategy_hypothesis="리치고 관점의 숫자 기반 판단 프레임으로 뉴스 요약과 차별화합니다.",
                tactical_hypothesis="오프닝은 선택지를 선명하게 던지고, 본문은 데이터→판단 기준→실행/보류 조건 순서로 구성합니다.",
                verification_signals=["CTR", "유지율", "댓글 질문", "저장", "공유"],
                failure_criteria=["클릭률 저조", "뉴스 요약 반응만 발생", "실행 기준이 모호하다는 댓글"],
                decision_label="iterate" if idx else "scale",
                next_loop="업로드 후 실제 성과와 댓글 질문으로 다음 주제 각도를 재검증합니다.",
            )
        )
    return TopicResult(
        recommended_topics=candidates,
        selected_topic=candidates[0].title,
        selected_reason=candidates[0].reason,
        selected_archetype=candidates[0].archetype,
    )


def _clean_issue(issue: str) -> str:
    return issue.replace("[ARTICLE]", "").replace("[VIDEO]", "").strip()
