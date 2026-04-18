from fastapi import APIRouter

from app.modules.performance.tracker import fetch_latest, weekly_report

router = APIRouter()


@router.post("/fetch")
def performance_fetch():
    return fetch_latest()


@router.get("/report")
def performance_report():
    return weekly_report()
