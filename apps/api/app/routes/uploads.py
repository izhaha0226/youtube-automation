from fastapi import APIRouter
from pydantic import BaseModel

from app.modules.upload.meta import build_upload_meta
from app.modules.upload.packager import build_package
from app.modules.upload.youtube import upload_to_youtube
from app.schemas import PackageManifest, ScenarioOutput, UploadMeta

router = APIRouter()


class MetaPayload(BaseModel):
    run_id: str
    topic: str
    scenario: ScenarioOutput


class PackagePayload(BaseModel):
    run_id: str


class UploadPayload(BaseModel):
    run_id: str
    dry_run: bool = False


@router.post("/meta", response_model=UploadMeta)
def meta_run(payload: MetaPayload) -> UploadMeta:
    return build_upload_meta(payload.run_id, payload.topic, payload.scenario)


@router.post("/package", response_model=PackageManifest)
def package_run(payload: PackagePayload) -> PackageManifest:
    return build_package(payload.run_id)


@router.post("/youtube")
def youtube_run(payload: UploadPayload):
    return upload_to_youtube(payload.run_id, dry_run=payload.dry_run)
