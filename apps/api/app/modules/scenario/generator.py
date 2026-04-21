from __future__ import annotations

import json

from app.core.llm import llm
from app.core.logging import get_logger
from app.core.prompts import load_prompt, render
from app.modules.richgo.editorial import editorial_rules_context, philosophy_context
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
        channel=payload.channel,
        tone=payload.tone,
        keywords=", ".join(payload.keywords) or "(없음)",
        reference_points=", ".join(payload.reference_points) or "(없음)",
        selected_articles_json=json.dumps(payload.selected_articles, ensure_ascii=False),
        selected_videos_json=json.dumps(payload.selected_videos, ensure_ascii=False),
        target_duration_min=payload.target_duration_min,
        target_duration_max=payload.target_duration_max,
        session_id=payload.session_id or "(없음)",
        kim_kiwon_philosophy=philosophy_context(),
        editorial_rules=editorial_rules_context(),
    )
    data = llm(temperature=0.6).generate_json(system=system, user=user)
    out = ScenarioOutput(
        hook=data.get("hook", ""),
        hook_30s=data.get("hook_30s", data.get("hook", "")),
        bridge_3min=data.get("bridge_3min", ""),
        body=data.get("body", []),
        body_sections=data.get("body_sections", []),
        conclusion=data.get("conclusion", ""),
        action_takeaways=data.get("action_takeaways", []),
        cta=data.get("cta", ""),
        title_candidates=data.get("title_candidates", []),
        thumbnail_candidates=data.get("thumbnail_candidates", []),
        opening=data.get("opening", ""),
        opening_title=data.get("opening_title", ""),
        estimated_duration_min=data.get("estimated_duration_min", payload.target_duration_min),
    )
    log.info(
        "scenario.gen.done",
        hook_len=len(out.hook),
        body=len(out.body),
        titles=len(out.title_candidates),
    )
    return out
