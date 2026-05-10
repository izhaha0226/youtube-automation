from __future__ import annotations

import json

from app.core.config import settings
from app.core.llm import llm
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
    data = llm(temperature=0.5).generate_json(system=system, user=user)

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
