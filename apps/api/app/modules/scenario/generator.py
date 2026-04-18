from __future__ import annotations

from app.core.llm import llm
from app.core.logging import get_logger
from app.core.prompts import load_prompt, render
from app.schemas import ScenarioInput, ScenarioOutput

log = get_logger(__name__)


def generate_scenario(payload: ScenarioInput) -> ScenarioOutput:
    system = (
        "You are the scenario writer for the 리치고 channel. "
        "구어체 한국어로 작성. Output valid JSON only."
    )
    user = render(
        load_prompt("scenario_generate"),
        topic=payload.topic,
        tone=payload.tone,
        keywords=", ".join(payload.keywords) or "(없음)",
        reference_points=", ".join(payload.reference_points) or "(없음)",
    )
    data = llm(temperature=0.6).generate_json(system=system, user=user)
    out = ScenarioOutput(
        hook=data.get("hook", ""),
        body=data.get("body", []),
        conclusion=data.get("conclusion", ""),
        cta=data.get("cta", ""),
        title_candidates=data.get("title_candidates", []),
        thumbnail_candidates=data.get("thumbnail_candidates", []),
        opening=data.get("opening", ""),
    )
    log.info(
        "scenario.gen.done",
        hook_len=len(out.hook),
        body=len(out.body),
        titles=len(out.title_candidates),
    )
    return out
