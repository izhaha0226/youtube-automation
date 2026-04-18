from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm import LLMError
from app.core.logging import get_logger
from app.modules.narration.narrator import generate_narration
from app.schemas import NarrationInput, NarrationOutput

log = get_logger(__name__)
router = APIRouter()


class NarrationPayload(BaseModel):
    run_id: str
    narration: NarrationInput


@router.post("", response_model=NarrationOutput)
def narrations_run(payload: NarrationPayload) -> NarrationOutput:
    try:
        return generate_narration(payload.run_id, payload.narration)
    except LLMError as e:
        log.error("narrations.llm_error", error=str(e))
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("narrations.unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
