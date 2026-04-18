from fastapi import APIRouter

from app.modules.scenario.generator import generate_scenario
from app.schemas import ScenarioInput, ScenarioOutput

router = APIRouter()


@router.post("", response_model=ScenarioOutput)
def scenarios_run(payload: ScenarioInput) -> ScenarioOutput:
    return generate_scenario(payload)
