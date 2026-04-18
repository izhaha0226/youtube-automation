from fastapi import APIRouter

from app.modules.topic.selector import select_topic
from app.schemas import TopicInput, TopicResult

router = APIRouter()


@router.post("", response_model=TopicResult)
def topics_run(payload: TopicInput) -> TopicResult:
    return select_topic(payload)
