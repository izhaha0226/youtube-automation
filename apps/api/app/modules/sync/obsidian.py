from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.models import ScenarioWorkspace

log = get_logger(__name__)


def write_obsidian(sub: str, filename: str, content: str) -> Path:
    """Obsidian first, then Workspace sync handled by caller."""
    base = Path(settings.obsidian_vault) / "notes" / "auto" / sub
    base.mkdir(parents=True, exist_ok=True)
    p = base / filename
    p.write_text(content, encoding="utf-8")
    log.info("sync.obsidian", path=str(p))
    return p


def write_obsidian_json(sub: str, filename: str, data: dict) -> Path:
    return write_obsidian(sub, filename, json.dumps(data, ensure_ascii=False, indent=2))


def mirror_to_workspace(obsidian_path: Path, workspace_path: Path) -> None:
    workspace_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(obsidian_path, workspace_path)
    log.info("sync.mirror", src=str(obsidian_path), dst=str(workspace_path))


def export_workspace_package(row: ScenarioWorkspace) -> tuple[Path, Path]:
    snapshot = row.references_snapshot or {}
    scenario = snapshot.get("scenario") or {}
    review = snapshot.get("review") or {}
    narration = snapshot.get("narration") or {}
    subtitles = snapshot.get("subtitles") or []
    thumbnail = snapshot.get("thumbnail") or {}
    upload_meta = snapshot.get("upload_meta") or {}
    articles = snapshot.get("articles") or []
    videos = snapshot.get("videos") or []
    keywords = snapshot.get("keywords") or []

    markdown = _workspace_markdown(
        row=row,
        scenario=scenario,
        review=review,
        narration=narration,
        subtitles=subtitles,
        thumbnail=thumbnail,
        upload_meta=upload_meta,
        articles=articles,
        videos=videos,
        keywords=keywords,
    )
    payload = {
        "id": row.id,
        "session_id": row.session_id,
        "selected_topic": row.selected_topic,
        "target_duration_min": row.target_duration_min,
        "target_duration_max": row.target_duration_max,
        "hook_30s": row.hook_30s,
        "bridge_3min": row.bridge_3min,
        "body_sections": row.body_sections,
        "full_script_markdown": row.full_script_markdown,
        "title_candidates": row.title_candidates,
        "thumbnail_candidates": row.thumbnail_candidates,
        "references_snapshot": snapshot,
        "status": row.status,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }
    md_path = write_obsidian("workspaces", f"{row.session_id}.md", markdown)
    json_path = write_obsidian_json("workspaces", f"{row.session_id}.json", payload)
    return md_path, json_path


def _workspace_markdown(
    *,
    row: ScenarioWorkspace,
    scenario: dict,
    review: dict,
    narration: dict,
    subtitles: list[dict],
    thumbnail: dict,
    upload_meta: dict,
    articles: list[dict],
    videos: list[dict],
    keywords: list[str],
) -> str:
    lines = [
        "---",
        f"session_id: {row.session_id}",
        f"selected_topic: {row.selected_topic}",
        f"status: {row.status}",
        f"target_duration_min: {row.target_duration_min}",
        f"target_duration_max: {row.target_duration_max}",
        f"updated: {row.updated_at.isoformat()}",
        "---",
        "",
        f"# {row.selected_topic}",
        "",
        "> [!info] 워크스페이스 패키지",
        "> 리서치 근거, 시나리오, 검수, 후속 제작 결과를 한 곳에 모은 자동 생성 노트",
        "",
        "## 🎯 주제",
        f"- 상태: `{row.status}`",
        f"- 목표 길이: {row.target_duration_min}분부터 {row.target_duration_max}분까지",
        f"- 키워드: {', '.join(keywords) if keywords else '(없음)'}",
        "",
        "## 🎬 시나리오 핵심",
        f"- Hook 30초: {row.hook_30s or '(없음)'}",
        f"- Bridge 3분: {row.bridge_3min or '(없음)'}",
        f"- Opening Title: {scenario.get('opening_title', '(없음)')}",
        "",
        "## 📝 풀 스크립트",
        row.full_script_markdown or "(없음)",
        "",
        "## 📚 선택 근거",
    ]
    if articles:
        lines.append("### 기사")
        for article in articles:
            lines.append(f"- {article.get('title', '(제목 없음)')} — {article.get('url', '')}".rstrip())
    else:
        lines.append("- 기사 근거 없음")
    if videos:
        lines.append("")
        lines.append("### 영상")
        for video in videos:
            lines.append(f"- {video.get('title', '(제목 없음)')} — {video.get('url', '')}".rstrip())
    else:
        lines.append("")
        lines.append("### 영상")
        lines.append("- 영상 근거 없음")

    lines += ["", "## 🧪 검수 결과"]
    if review:
        lines.append(f"- 통과 여부: {'통과' if review.get('passed') else '수정 필요'}")
        issues = review.get('issues') or []
        fixes = review.get('fix_suggestions') or []
        if issues:
            lines.append("- 이슈:")
            lines.extend(f"  - {issue}" for issue in issues)
        if fixes:
            lines.append("- 수정 제안:")
            lines.extend(f"  - {fix}" for fix in fixes)
    else:
        lines.append("- 아직 검수 결과 없음")

    lines += ["", "## 🎙️ 후속 제작"]
    if narration:
        lines.append(f"- 나레이션 문장 수: {len(narration.get('sentences', []))}")
        lines.append(f"- 오디오 경로: {narration.get('audio_path', '(없음)')}")
    else:
        lines.append("- 나레이션 없음")
    if subtitles:
        lines.append(f"- 자막 언어: {', '.join(sub.get('lang', '?') for sub in subtitles)}")
    else:
        lines.append("- 자막 없음")
    if thumbnail:
        lines.append(f"- 썸네일 결과: {thumbnail.get('final_image', '(없음)')}")
    else:
        lines.append("- 썸네일 없음")
    if upload_meta:
        lines.append(f"- 업로드 메타 제목: {upload_meta.get('title', '(없음)')}")
    else:
        lines.append("- 업로드 메타 없음")

    lines += ["", "## 🧭 액션 포인트"]
    takeaways = scenario.get('action_takeaways') or []
    if takeaways:
        lines.extend(f"- {item}" for item in takeaways)
    else:
        lines.append("- 액션 포인트 없음")

    return "\n".join(lines).strip() + "\n"
