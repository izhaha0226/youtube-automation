from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm import LLMError
from app.core.logging import get_logger
from app.modules.thumbnail.generator import generate_thumbnail
from app.schemas import ThumbnailInput, ThumbnailOutput

log = get_logger(__name__)
router = APIRouter()


class ThumbnailPayload(BaseModel):
    run_id: str
    input: ThumbnailInput


@router.post("", response_model=ThumbnailOutput)
def thumbnails_run(payload: ThumbnailPayload) -> ThumbnailOutput:
    try:
        return generate_thumbnail(payload.run_id, payload.input)
    except LLMError as e:
        log.error("thumbnails.llm_error", error=str(e))
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("thumbnails.unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
