from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import engine
from app.models import (
    AssetRecord,
    PipelineRun,
    ReviewRecord,
    ScenarioRecord,
    TopicRecord,
    UploadRecord,
)
from app.modules.pipeline import run_full_pipeline

router = APIRouter()


class RunPayload(BaseModel):
    intent: str
    avoid_keywords: list[str] = []
    must_include: list[str] = []
    auto_upload: bool = False


class RunUpdatePayload(BaseModel):
    intent: str | None = None
    status: str | None = None
    meta: dict | None = None


@router.post("/run")
def pipeline_run(payload: RunPayload):
    return run_full_pipeline(
        intent=payload.intent,
        avoid_keywords=payload.avoid_keywords,
        must_include=payload.must_include,
        auto_upload=payload.auto_upload,
    )


@router.get("/runs")
def pipeline_runs(limit: int = 20):
    with Session(engine) as s:
        rows = s.exec(
            select(PipelineRun).order_by(PipelineRun.created_at.desc()).limit(limit)
        ).all()
    return [
        {
            "run_id": r.id,
            "intent": r.intent,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "meta": r.meta,
        }
        for r in rows
    ]


@router.get("/runs/{run_id}")
def pipeline_run_detail(run_id: str):
    with Session(engine) as s:
        run = s.get(PipelineRun, run_id)
        if not run:
            raise HTTPException(404, "Run not found")
        topics = s.exec(select(TopicRecord).where(TopicRecord.run_id == run_id)).all()
        scenarios = s.exec(select(ScenarioRecord).where(ScenarioRecord.run_id == run_id)).all()
        reviews = s.exec(select(ReviewRecord).where(ReviewRecord.run_id == run_id)).all()
        assets = s.exec(select(AssetRecord).where(AssetRecord.run_id == run_id)).all()
        uploads = s.exec(select(UploadRecord).where(UploadRecord.run_id == run_id)).all()

    return {
        "run_id": run.id,
        "channel": run.channel,
        "intent": run.intent,
        "status": run.status,
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
        "meta": run.meta,
        "topics": [{"id": t.id, "title": t.title, "reason": t.reason, "score": t.score, "risk": t.risk, "selected": t.selected} for t in topics],
        "scenarios": [{"id": sc.id, "title": sc.title, "hook": sc.hook, "body": sc.body, "conclusion": sc.conclusion, "cta": sc.cta, "title_candidates": sc.title_candidates, "thumbnail_candidates": sc.thumbnail_candidates} for sc in scenarios],
        "reviews": [{"id": rv.id, "passed": rv.passed, "issues": rv.issues, "fix_suggestions": rv.fix_suggestions} for rv in reviews],
        "assets": [{"id": a.id, "kind": a.kind, "path": a.path, "meta": a.meta} for a in assets],
        "uploads": [{"id": u.id, "video_id": u.video_id, "url": u.url, "status": u.status} for u in uploads],
    }


@router.patch("/runs/{run_id}")
def pipeline_run_update(run_id: str, payload: RunUpdatePayload):
    from datetime import datetime

    with Session(engine) as s:
        run = s.get(PipelineRun, run_id)
        if not run:
            raise HTTPException(404, "Run not found")
        if payload.intent is not None:
            run.intent = payload.intent
        if payload.status is not None:
            run.status = payload.status
        if payload.meta is not None:
            run.meta = payload.meta
        run.updated_at = datetime.utcnow()
        s.add(run)
        s.commit()
        s.refresh(run)
    return {"ok": True, "run_id": run.id, "status": run.status}


@router.delete("/runs/{run_id}")
def pipeline_run_delete(run_id: str):
    with Session(engine) as s:
        run = s.get(PipelineRun, run_id)
        if not run:
            raise HTTPException(404, "Run not found")
        for model in [TopicRecord, ScenarioRecord, ReviewRecord, AssetRecord, UploadRecord]:
            for row in s.exec(select(model).where(model.run_id == run_id)).all():
                s.delete(row)
        s.delete(run)
        s.commit()
    return {"ok": True, "deleted": run_id}
