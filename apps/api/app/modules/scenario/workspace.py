from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.core.db import engine
from app.models import ScenarioWorkspace
from app.modules.sync.obsidian import export_workspace_package
from app.schemas import NarrationOutput, ReviewOutput, ScenarioInput, ScenarioOutput, SubtitleOutput, ThumbnailOutput, UploadMeta


def save_scenario_workspace(payload: ScenarioInput, scenario: ScenarioOutput) -> ScenarioWorkspace:
    workspace = ScenarioWorkspace(
        id=str(uuid.uuid4()),
        session_id=payload.session_id or str(uuid.uuid4()),
        selected_topic=payload.topic,
        target_duration_min=payload.target_duration_min,
        target_duration_max=payload.target_duration_max,
        hook_30s=scenario.hook_30s,
        bridge_3min=scenario.bridge_3min,
        body_sections=[section.model_dump() for section in scenario.body_sections],
        full_script_markdown=_to_markdown(scenario),
        title_candidates=scenario.title_candidates,
        thumbnail_candidates=scenario.thumbnail_candidates,
        references_snapshot={
            "articles": payload.selected_articles,
            "videos": payload.selected_videos,
            "keywords": payload.keywords,
            "selected_article_ids": [article.get("id") for article in payload.selected_articles if article.get("id")],
            "selected_video_ids": [video.get("id") for video in payload.selected_videos if video.get("id")],
            "scenario": scenario.model_dump(),
        },
        status="generated",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    with Session(engine) as s:
        existing = s.exec(
            select(ScenarioWorkspace)
            .where(ScenarioWorkspace.session_id == workspace.session_id)
            .order_by(ScenarioWorkspace.created_at.desc())
        ).first()
        if existing:
            existing.selected_topic = workspace.selected_topic
            existing.target_duration_min = workspace.target_duration_min
            existing.target_duration_max = workspace.target_duration_max
            existing.hook_30s = workspace.hook_30s
            existing.bridge_3min = workspace.bridge_3min
            existing.body_sections = workspace.body_sections
            existing.full_script_markdown = workspace.full_script_markdown
            existing.title_candidates = workspace.title_candidates
            existing.thumbnail_candidates = workspace.thumbnail_candidates
            existing.references_snapshot = workspace.references_snapshot
            existing.status = workspace.status
            existing.updated_at = datetime.utcnow()
            s.add(existing)
            s.commit()
            s.refresh(existing)
            export_workspace_package(existing)
            return existing
        s.add(workspace)
        s.commit()
        s.refresh(workspace)
        export_workspace_package(workspace)
        return workspace


def get_workspace_by_session(session_id: str) -> ScenarioWorkspace | None:
    with Session(engine) as s:
        return s.exec(
            select(ScenarioWorkspace)
            .where(ScenarioWorkspace.session_id == session_id)
            .order_by(ScenarioWorkspace.created_at.desc())
        ).first()


def save_workspace_review(session_id: str, review: ReviewOutput) -> ScenarioWorkspace | None:
    with Session(engine) as s:
        row = s.exec(
            select(ScenarioWorkspace)
            .where(ScenarioWorkspace.session_id == session_id)
            .order_by(ScenarioWorkspace.created_at.desc())
        ).first()
        if not row:
            return None
        snapshot = row.references_snapshot or {}
        snapshot["review"] = review.model_dump()
        row.references_snapshot = snapshot
        row.status = "reviewed"
        row.updated_at = datetime.utcnow()
        s.add(row)
        s.commit()
        s.refresh(row)
        export_workspace_package(row)
        return row


def save_workspace_narration(session_id: str, narration: NarrationOutput) -> ScenarioWorkspace | None:
    with Session(engine) as s:
        row = s.exec(
            select(ScenarioWorkspace)
            .where(ScenarioWorkspace.session_id == session_id)
            .order_by(ScenarioWorkspace.created_at.desc())
        ).first()
        if not row:
            return None
        snapshot = row.references_snapshot or {}
        snapshot["narration"] = narration.model_dump()
        row.references_snapshot = snapshot
        row.status = "narrated"
        row.updated_at = datetime.utcnow()
        s.add(row)
        s.commit()
        s.refresh(row)
        export_workspace_package(row)
        return row


def save_workspace_subtitles(session_id: str, subtitles: list[SubtitleOutput]) -> ScenarioWorkspace | None:
    with Session(engine) as s:
        row = s.exec(
            select(ScenarioWorkspace)
            .where(ScenarioWorkspace.session_id == session_id)
            .order_by(ScenarioWorkspace.created_at.desc())
        ).first()
        if not row:
            return None
        snapshot = row.references_snapshot or {}
        snapshot["subtitles"] = [subtitle.model_dump() for subtitle in subtitles]
        row.references_snapshot = snapshot
        row.status = "subtitled"
        row.updated_at = datetime.utcnow()
        s.add(row)
        s.commit()
        s.refresh(row)
        export_workspace_package(row)
        return row


def save_workspace_thumbnail(session_id: str, thumbnail: ThumbnailOutput) -> ScenarioWorkspace | None:
    with Session(engine) as s:
        row = s.exec(
            select(ScenarioWorkspace)
            .where(ScenarioWorkspace.session_id == session_id)
            .order_by(ScenarioWorkspace.created_at.desc())
        ).first()
        if not row:
            return None
        snapshot = row.references_snapshot or {}
        snapshot["thumbnail"] = thumbnail.model_dump()
        row.references_snapshot = snapshot
        row.status = "thumbnailed"
        row.updated_at = datetime.utcnow()
        s.add(row)
        s.commit()
        s.refresh(row)
        export_workspace_package(row)
        return row


def save_workspace_upload_meta(session_id: str, upload_meta: UploadMeta) -> ScenarioWorkspace | None:
    with Session(engine) as s:
        row = s.exec(
            select(ScenarioWorkspace)
            .where(ScenarioWorkspace.session_id == session_id)
            .order_by(ScenarioWorkspace.created_at.desc())
        ).first()
        if not row:
            return None
        snapshot = row.references_snapshot or {}
        snapshot["upload_meta"] = upload_meta.model_dump()
        row.references_snapshot = snapshot
        row.status = "meta_ready"
        row.updated_at = datetime.utcnow()
        s.add(row)
        s.commit()
        s.refresh(row)
        export_workspace_package(row)
        return row


def scenario_from_workspace(row: ScenarioWorkspace) -> ScenarioOutput:
    snapshot = row.references_snapshot or {}
    data = snapshot.get("scenario") or {
        "hook": row.hook_30s,
        "hook_30s": row.hook_30s,
        "bridge_3min": row.bridge_3min,
        "archetype": "판단형",
        "body": [],
        "body_sections": row.body_sections,
        "conclusion": "",
        "action_takeaways": [],
        "cta": "",
        "title_candidates": row.title_candidates,
        "thumbnail_candidates": row.thumbnail_candidates,
        "opening": "",
        "opening_title": row.selected_topic,
        "estimated_duration_min": row.target_duration_min,
    }
    return ScenarioOutput.model_validate(data)


def scenario_input_from_workspace(row: ScenarioWorkspace, reference_points: list[str] | None = None) -> ScenarioInput:
    snapshot = row.references_snapshot or {}
    scenario = snapshot.get("scenario") or {}
    return ScenarioInput(
        topic=row.selected_topic,
        archetype=scenario.get("archetype", "판단형"),
        keywords=snapshot.get("keywords", []),
        selected_articles=snapshot.get("articles", []),
        selected_videos=snapshot.get("videos", []),
        target_duration_min=row.target_duration_min,
        target_duration_max=row.target_duration_max,
        session_id=row.session_id,
        reference_points=reference_points or [],
    )


def _to_markdown(scenario: ScenarioOutput) -> str:
    lines = []
    if scenario.opening_title:
        lines += [f"# {scenario.opening_title}", ""]
    if scenario.hook_30s:
        lines += ["## 0~30초 Hook", scenario.hook_30s, ""]
    if scenario.bridge_3min:
        lines += ["## 30초~3분", scenario.bridge_3min, ""]
    if scenario.body_sections:
        lines.append("## 본문")
        lines.append("")
        for section in scenario.body_sections:
            lines += [f"### {section.heading or '섹션'}", section.script, ""]
            if section.narration and section.narration != section.script:
                lines += ["#### 나레이션", section.narration, ""]
    elif scenario.body:
        lines.append("## 본문")
        lines.append("")
        for block in scenario.body:
            lines += [block, ""]
    if scenario.action_takeaways:
        lines.append("## 액션 포인트")
        lines += [*(f"- {item}" for item in scenario.action_takeaways), ""]
    if scenario.conclusion:
        lines += ["## 결론", scenario.conclusion, ""]
    if scenario.cta:
        lines += ["## CTA", scenario.cta, ""]
    return "\n".join(lines).strip()
