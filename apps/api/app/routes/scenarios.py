from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from app.core.db import engine
from app.core.llm import LLMError
from app.core.logging import get_logger
from app.models import ScenarioWorkspace
from app.modules.narration.narrator import generate_narration
from app.modules.review.reviewer import review_scenario
from app.modules.scenario.generator import generate_scenario
from app.modules.scenario.workspace import (
    get_workspace_by_session,
    save_scenario_workspace,
    save_workspace_narration,
    save_workspace_review,
    save_workspace_subtitles,
    save_workspace_thumbnail,
    save_workspace_upload_meta,
    scenario_from_workspace,
    scenario_input_from_workspace,
)
from app.modules.subtitle.subtitler import generate_subtitles
from app.modules.thumbnail.generator import generate_thumbnail
from app.modules.upload.meta import build_upload_meta
from app.schemas import (
    NarrationInput,
    NarrationOutput,
    ReviewInput,
    ReviewOutput,
    ScenarioInput,
    ScenarioOutput,
    SubtitleOutput,
    ThumbnailInput,
    ThumbnailOutput,
    UploadMeta,
)

log = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=ScenarioOutput)
def scenarios_run(payload: ScenarioInput) -> ScenarioOutput:
    try:
        result = generate_scenario(payload)
        save_scenario_workspace(payload, result)
        return result
    except LLMError as e:
        log.error("scenarios.llm_error", error=str(e))
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("scenarios.unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/{session_id}")
def scenario_workspace_get(session_id: str):
    row = get_workspace_by_session(session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
    snapshot = row.references_snapshot or {}
    scenario = snapshot.get("scenario") or scenario_from_workspace(row).model_dump()
    return {
        "id": row.id,
        "session_id": row.session_id,
        "selected_topic": row.selected_topic,
        "target_duration_min": row.target_duration_min,
        "target_duration_max": row.target_duration_max,
        "hook_30s": row.hook_30s,
        "bridge_3min": row.bridge_3min,
        "body_sections": row.body_sections,
        "full_script_markdown": row.full_script_markdown,
        "title_candidates": row.title_candidates,
        "thumbnail_candidates": row.thumbnail_candidates,
        "references_snapshot": snapshot,
        "selected_article_ids": snapshot.get("selected_article_ids", []),
        "selected_video_ids": snapshot.get("selected_video_ids", []),
        "scenario": scenario,
        "review": snapshot.get("review"),
        "narration": snapshot.get("narration"),
        "subtitles": snapshot.get("subtitles"),
        "thumbnail": snapshot.get("thumbnail"),
        "upload_meta": snapshot.get("upload_meta"),
        "status": row.status,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


@router.post("/workspace/{session_id}/review", response_model=ReviewOutput)
def scenario_workspace_review(session_id: str) -> ReviewOutput:
    try:
        return review_workspace(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LLMError as e:
        log.error("scenarios.workspace_review.llm_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("scenarios.workspace_review.unexpected_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/{session_id}/regenerate", response_model=ScenarioOutput)
def scenario_workspace_regenerate(session_id: str) -> ScenarioOutput:
    try:
        return regenerate_workspace(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LLMError as e:
        log.error("scenarios.workspace_regenerate.llm_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("scenarios.workspace_regenerate.unexpected_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/{session_id}/narrate", response_model=NarrationOutput)
def scenario_workspace_narrate(session_id: str) -> NarrationOutput:
    try:
        return narrate_workspace(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LLMError as e:
        log.error("scenarios.workspace_narrate.llm_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("scenarios.workspace_narrate.unexpected_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/{session_id}/subtitles", response_model=list[SubtitleOutput])
def scenario_workspace_subtitles(session_id: str) -> list[SubtitleOutput]:
    try:
        return subtitle_workspace(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LLMError as e:
        log.error("scenarios.workspace_subtitles.llm_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("scenarios.workspace_subtitles.unexpected_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/{session_id}/thumbnail", response_model=ThumbnailOutput)
def scenario_workspace_thumbnail(session_id: str) -> ThumbnailOutput:
    try:
        return thumbnail_workspace(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LLMError as e:
        log.error("scenarios.workspace_thumbnail.llm_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("scenarios.workspace_thumbnail.unexpected_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/{session_id}/upload-meta", response_model=UploadMeta)
def scenario_workspace_upload_meta(session_id: str) -> UploadMeta:
    try:
        return upload_meta_workspace(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LLMError as e:
        log.error("scenarios.workspace_upload_meta.llm_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("scenarios.workspace_upload_meta.unexpected_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=str(e))


def review_workspace(session_id: str) -> ReviewOutput:
    row = get_workspace_by_session(session_id)
    if not row:
        raise ValueError("Workspace not found")
    review = review_scenario(ReviewInput(scenario=scenario_from_workspace(row), topic=row.selected_topic))
    save_workspace_review(session_id, review)
    return review


def regenerate_workspace(session_id: str) -> ScenarioOutput:
    row = get_workspace_by_session(session_id)
    if not row:
        raise ValueError("Workspace not found")
    snapshot = row.references_snapshot or {}
    review_snapshot = snapshot.get("review") or {}
    scenario_input = scenario_input_from_workspace(
        row,
        reference_points=review_snapshot.get("fix_suggestions", []),
    )
    scenario = generate_scenario(scenario_input)
    save_scenario_workspace(scenario_input, scenario)
    return scenario


def narrate_workspace(session_id: str) -> NarrationOutput:
    row = get_workspace_by_session(session_id)
    if not row:
        raise ValueError("Workspace not found")
    scenario = scenario_from_workspace(row)
    narration = generate_narration(session_id, NarrationInput(scenario=scenario))
    save_workspace_narration(session_id, narration)
    return narration


def subtitle_workspace(session_id: str) -> list[SubtitleOutput]:
    row = get_workspace_by_session(session_id)
    if not row:
        raise ValueError("Workspace not found")
    snapshot = row.references_snapshot or {}
    narration_snapshot = snapshot.get("narration")
    if not narration_snapshot:
        raise ValueError("Narration not found")
    narration = NarrationOutput.model_validate(narration_snapshot)
    subtitles = generate_subtitles(session_id, narration)
    save_workspace_subtitles(session_id, subtitles)
    return subtitles


def thumbnail_workspace(session_id: str) -> ThumbnailOutput:
    row = get_workspace_by_session(session_id)
    if not row:
        raise ValueError("Workspace not found")
    scenario = scenario_from_workspace(row)
    snapshot = row.references_snapshot or {}
    thumbnail_text = (scenario.thumbnail_candidates or [row.selected_topic])[0]
    thumbnail = generate_thumbnail(
        session_id,
        ThumbnailInput(
            title=row.selected_topic,
            thumbnail_text=thumbnail_text,
        ),
    )
    save_workspace_thumbnail(session_id, thumbnail)
    return thumbnail


def upload_meta_workspace(session_id: str) -> UploadMeta:
    row = get_workspace_by_session(session_id)
    if not row:
        raise ValueError("Workspace not found")
    scenario = scenario_from_workspace(row)
    upload_meta = build_upload_meta(session_id, row.selected_topic, scenario)
    save_workspace_upload_meta(session_id, upload_meta)
    return upload_meta
