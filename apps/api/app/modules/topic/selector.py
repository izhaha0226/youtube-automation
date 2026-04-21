from __future__ import annotations

import json

from app.core.config import settings
from app.core.llm import llm
from app.core.logging import get_logger
from app.core.prompts import load_prompt, render
from app.modules.richgo.editorial import editorial_rules_context, philosophy_context
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
        candidates.append(
            TopicCandidate(
                title=c.get("title", ""),
                reason=c.get("reason", ""),
                score=score,
                risk=c.get("risk", ""),
                keywords=c.get("keywords", []),
            )
        )
    candidates.sort(key=lambda c: c.score.total(), reverse=True)
    candidates = candidates[:top_k]

    selected = data.get("selected_topic") or (candidates[0].title if candidates else "")
    reason = data.get("selected_reason") or (candidates[0].reason if candidates else "")

    result = TopicResult(
        recommended_topics=candidates,
        selected_topic=selected,
        selected_reason=reason,
    )
    log.info("topic.select.done", count=len(candidates), selected=selected)
    return result
