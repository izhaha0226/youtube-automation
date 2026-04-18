from fastapi import APIRouter, HTTPException

from app.core.llm import LLMError
from app.core.logging import get_logger
from app.modules.topic.selector import select_topic
from app.schemas import TopicInput, TopicResult

log = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=TopicResult)
def topics_run(payload: TopicInput) -> TopicResult:
    try:
        return select_topic(payload)
    except LLMError as e:
        log.error("topics.llm_error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"LLM service unavailable: {e}. Check ANTHROPIC_API_KEY or install codex CLI.",
        )
    except Exception as e:
        log.error("topics.unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
