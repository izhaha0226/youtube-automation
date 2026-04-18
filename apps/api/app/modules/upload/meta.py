from __future__ import annotations

from app.core.llm import llm
from app.core.logging import get_logger
from app.core.paths import workspace_dir
from app.core.prompts import load_prompt, render
from app.schemas import ScenarioOutput, UploadMeta

log = get_logger(__name__)


def build_upload_meta(run_id: str, topic: str, scenario: ScenarioOutput) -> UploadMeta:
    system = "You produce YouTube upload metadata for the 리치고 channel. JSON only."
    user = render(
        load_prompt("upload_meta"),
        topic=topic,
        scenario_json=scenario.model_dump_json(),
    )
    data = llm(temperature=0.5).generate_json(system=system, user=user)
    meta = UploadMeta(
        title=data.get("title", topic),
        description=data.get("description", ""),
        tags=data.get("tags", []),
        hashtags=data.get("hashtags", []),
        pinned_comment=data.get("pinned_comment", ""),
    )
    out_dir = workspace_dir(run_id, "packages")
    (out_dir / "upload_meta.json").write_text(meta.model_dump_json(indent=2), encoding="utf-8")
    log.info("upload.meta.done", title=meta.title)
    return meta
