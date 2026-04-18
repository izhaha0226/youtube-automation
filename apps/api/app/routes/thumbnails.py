from fastapi import APIRouter
from pydantic import BaseModel

from app.modules.thumbnail.generator import generate_thumbnail
from app.schemas import ThumbnailInput, ThumbnailOutput

router = APIRouter()


class ThumbnailPayload(BaseModel):
    run_id: str
    input: ThumbnailInput


@router.post("", response_model=ThumbnailOutput)
def thumbnails_run(payload: ThumbnailPayload) -> ThumbnailOutput:
    return generate_thumbnail(payload.run_id, payload.input)
