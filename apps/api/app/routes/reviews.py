from fastapi import APIRouter, HTTPException

from app.core.llm import LLMError
from app.core.logging import get_logger
from app.modules.review.reviewer import review_scenario
from app.schemas import ReviewInput, ReviewOutput

log = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=ReviewOutput)
def reviews_run(payload: ReviewInput) -> ReviewOutput:
    try:
        return review_scenario(payload)
    except LLMError as e:
        log.error("reviews.llm_error", error=str(e))
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        log.error("reviews.unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
