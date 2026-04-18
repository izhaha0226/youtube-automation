from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm import LLMError
from app.core.logging import get_logger
from app.modules.narration.narrator import generate_narration
from app.modules.subtitle.subtitler import generate_subtitles
from app.schemas import NarrationInput, NarrationOutput, SubtitleOutput

log = get_logger(__name__)
router = APIRouter()


class NarrationPayload(BaseModel):
    run_id: str
    narration: NarrationInput


class SubtitlePayload(BaseModel):
    run_id: str
    narration: NarrationOutput


@router.post("/narration", response_model=NarrationOutput)
def narration_run(payload: NarrationPayload) -> NarrationOutput:
    try:
        return generate_narration(payload.run_id, payload.narration)
    except LLMError as e:
        log.error("subtitles.narration.llm_error", error=str(e))
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("subtitles.narration.unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate", response_model=list[SubtitleOutput])
def subtitles_run(payload: SubtitlePayload) -> list[SubtitleOutput]:
    try:
        return generate_subtitles(payload.run_id, payload.narration)
    except LLMError as e:
        log.error("subtitles.translate.llm_error", error=str(e))
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("subtitles.translate.unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
