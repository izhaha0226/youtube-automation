from __future__ import annotations

from app.core.llm import llm
from app.core.logging import get_logger
from app.core.prompts import load_prompt, render
from app.schemas import ReviewInput, ReviewOutput

log = get_logger(__name__)


def review_scenario(payload: ReviewInput) -> ReviewOutput:
    system = "You are a strict reviewer for the 리치고 channel. Output JSON only."
    user = render(
        load_prompt("review"),
        topic=payload.topic,
        scenario_json=payload.scenario.model_dump_json(),
    )
    data = llm(temperature=0.2).generate_json(system=system, user=user)
    out = ReviewOutput(
        passed=bool(data.get("passed", False)),
        issues=data.get("issues", []),
        fix_suggestions=data.get("fix_suggestions", []),
    )
    log.info("review.done", passed=out.passed, issues=len(out.issues))
    return out
