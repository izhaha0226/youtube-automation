from fastapi import APIRouter

from app.modules.review.reviewer import review_scenario
from app.schemas import ReviewInput, ReviewOutput

router = APIRouter()


@router.post("", response_model=ReviewOutput)
def reviews_run(payload: ReviewInput) -> ReviewOutput:
    return review_scenario(payload)
