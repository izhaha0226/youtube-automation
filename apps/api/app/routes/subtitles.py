from fastapi import APIRouter
from pydantic import BaseModel

from app.modules.narration.narrator import generate_narration
from app.modules.subtitle.subtitler import generate_subtitles
from app.schemas import NarrationInput, NarrationOutput, SubtitleOutput

router = APIRouter()


class NarrationPayload(BaseModel):
    run_id: str
    narration: NarrationInput


class SubtitlePayload(BaseModel):
    run_id: str
    narration: NarrationOutput


@router.post("/narration", response_model=NarrationOutput)
def narration_run(payload: NarrationPayload) -> NarrationOutput:
    return generate_narration(payload.run_id, payload.narration)


@router.post("/translate", response_model=list[SubtitleOutput])
def subtitles_run(payload: SubtitlePayload) -> list[SubtitleOutput]:
    return generate_subtitles(payload.run_id, payload.narration)
