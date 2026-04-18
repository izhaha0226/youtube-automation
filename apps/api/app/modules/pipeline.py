"""End-to-end autonomous pipeline.

intent → topic → scenario → review → narration → subtitles → thumbnail → meta → package → (upload)
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.core.logging import get_logger
from app.core.paths import run_id as make_run_id
from app.core.paths import workspace_dir
from app.models import (
    AssetRecord,
    PipelineRun,
    ReviewRecord,
    ScenarioRecord,
    TopicRecord,
    UploadRecord,
)
from app.modules.narration.narrator import generate_narration
from app.modules.trend.scanner import scan as scan_trends
from app.modules.review.reviewer import review_scenario
from app.modules.scenario.generator import generate_scenario
from app.modules.subtitle.subtitler import generate_subtitles
from app.modules.sync.obsidian import write_obsidian, write_obsidian_json
from app.modules.thumbnail.generator import generate_thumbnail
from app.modules.topic.selector import select_topic
from app.modules.upload.meta import build_upload_meta
from app.modules.upload.packager import build_package
from app.modules.upload.youtube import upload_to_youtube
from app.modules.video.assembler import assemble_video
from app.modules.video.broll import generate_broll
from app.schemas import (
    NarrationInput,
    ReviewInput,
    ScenarioInput,
    ThumbnailInput,
    TopicInput,
)

log = get_logger(__name__)


def run_full_pipeline(
    intent: str,
    avoid_keywords: list[str] | None = None,
    must_include: list[str] | None = None,
    auto_upload: bool = False,
) -> dict:
    # 0. trend scan — feeds live signals into topic selection
    trend = scan_trends()

    # 1. topic
    topic_result = select_topic(
        TopicInput(
            user_intent=intent,
            avoid_keywords=avoid_keywords or [],
            must_include=must_include or [],
            current_issues=trend.as_current_issues(),
            trend_keywords=trend.keywords(),
        )
    )
    topic = topic_result.selected_topic
    rid = make_run_id(topic)
    log.info("pipeline.start", run_id=rid, topic=topic)

    with Session(engine) as s:
        s.add(
            PipelineRun(
                id=rid,
                channel=settings.channel_name,
                intent=intent,
                status="topic",
                meta={"selected_reason": topic_result.selected_reason},
            )
        )
        for c in topic_result.recommended_topics:
            s.add(
                TopicRecord(
                    id=str(uuid.uuid4()),
                    run_id=rid,
                    title=c.title,
                    reason=c.reason,
                    score=c.score.total(),
                    risk=c.risk,
                    selected=(c.title == topic),
                    payload=c.model_dump(),
                )
            )
        s.commit()

    _save("topics", rid, "topic_result.json", topic_result.model_dump())

    # 2. scenario
    keywords = next(
        (c.keywords for c in topic_result.recommended_topics if c.title == topic), []
    )
    scenario = generate_scenario(ScenarioInput(topic=topic, keywords=keywords))
    _save("scenarios", rid, "scenario.json", scenario.model_dump())
    with Session(engine) as s:
        s.add(
            ScenarioRecord(
                id=str(uuid.uuid4()),
                run_id=rid,
                title=topic,
                hook=scenario.hook,
                body=scenario.body,
                conclusion=scenario.conclusion,
                cta=scenario.cta,
                title_candidates=scenario.title_candidates,
                thumbnail_candidates=scenario.thumbnail_candidates,
            )
        )
        s.commit()

    # 3. review — auto-retry once if failed
    review = review_scenario(ReviewInput(scenario=scenario, topic=topic))
    if not review.passed and review.fix_suggestions:
        log.info("pipeline.review.retry", issues=review.issues)
        scenario = generate_scenario(
            ScenarioInput(
                topic=topic,
                keywords=keywords,
                reference_points=review.fix_suggestions,
            )
        )
        review = review_scenario(ReviewInput(scenario=scenario, topic=topic))
    _save("scenarios", rid, "review.json", review.model_dump())
    with Session(engine) as s:
        s.add(
            ReviewRecord(
                id=str(uuid.uuid4()),
                run_id=rid,
                passed=review.passed,
                issues=review.issues,
                fix_suggestions=review.fix_suggestions,
            )
        )
        s.commit()

    # 4. narration
    narration = generate_narration(rid, NarrationInput(scenario=scenario))
    _save(
        "narrations",
        rid,
        "narration.json",
        {"text_ko": narration.text_ko, "sentences": narration.sentences, "timeline": narration.timeline},
    )

    # 5. subtitles (KO/EN/JA/ZH)
    subs = generate_subtitles(rid, narration)

    # 6. thumbnail
    profile = settings.channel_profile.get("profile_image")
    thumb_text = (scenario.thumbnail_candidates or [topic])[0]
    thumb = generate_thumbnail(
        rid,
        ThumbnailInput(
            title=topic,
            thumbnail_text=thumb_text,
            profile_image=profile,
        ),
    )

    # 7. video — B-roll + assemble
    video_dir = workspace_dir(rid, "videos")
    broll = generate_broll(rid, scenario, video_dir / "broll")
    ko_srt = next(
        (s.srt_path for s in subs if s.lang == "ko"),
        None,
    )
    video = assemble_video(rid, narration, broll, video_dir, subtitle_path=ko_srt)
    if video.video_path:
        _save("videos", rid, "video_meta.json", video.model_dump())

    # 8. upload meta + package
    meta = build_upload_meta(rid, topic, scenario)
    manifest = build_package(rid, video_path=video.video_path)

    # 9. obsidian sync (markdown summary + trend snapshot)
    summary = _summary_md(rid, topic, topic_result.selected_reason, scenario, review, meta, video)
    write_obsidian("runs", f"{rid}.md", summary)
    write_obsidian_json("runs", f"{rid}.json", manifest.model_dump())
    write_obsidian_json(
        "trends",
        f"{rid}_trend.json",
        {
            "youtube": trend.youtube[:10],
            "news": trend.news[:10],
            "keywords": trend.keywords()[:30],
        },
    )

    # 10. upload (optional)
    upload_result = {"skipped": True}
    if auto_upload:
        upload_result = upload_to_youtube(rid, dry_run=False)
        with Session(engine) as s:
            s.add(
                UploadRecord(
                    id=str(uuid.uuid4()),
                    run_id=rid,
                    video_id=upload_result.get("video_id"),
                    url=upload_result.get("url"),
                    status="success" if upload_result.get("ok") else "failed",
                    log=upload_result,
                )
            )
            s.commit()

    with Session(engine) as s:
        run = s.get(PipelineRun, rid)
        if run:
            run.status = "done"
            s.add(run)
            s.commit()

    log.info("pipeline.done", run_id=rid, passed=review.passed, auto_upload=auto_upload)
    return {
        "run_id": rid,
        "topic": topic,
        "review_passed": review.passed,
        "review_issues": review.issues,
        "scenario": scenario.model_dump(),
        "meta": meta.model_dump(),
        "manifest": manifest.model_dump(),
        "subtitles": [s.model_dump() for s in subs],
        "thumbnail": thumb.model_dump(),
        "video": video.model_dump(),
        "upload": upload_result,
    }


def _save(kind: str, rid: str, filename: str, data: dict) -> Path:
    d = workspace_dir(rid, kind)
    p = d / filename
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    with Session(engine) as s:
        s.add(
            AssetRecord(
                id=str(uuid.uuid4()),
                run_id=rid,
                kind=kind,
                path=str(p),
                meta={"filename": filename},
            )
        )
        s.commit()
    return p


def _summary_md(rid, topic, reason, scenario, review, meta, video=None) -> str:
    return f"""# {topic}

- run_id: {rid}
- selected_reason: {reason}
- review_passed: {review.passed}

## 제목 후보
{chr(10).join(f'- {t}' for t in scenario.title_candidates)}

## 훅
{scenario.hook}

## 본문
{chr(10).join(f'- {b}' for b in scenario.body)}

## 결론
{scenario.conclusion}

## CTA
{scenario.cta}

## 업로드 메타
- title: {meta.title}
- tags: {', '.join(meta.tags)}
- hashtags: {', '.join(meta.hashtags)}

## 영상
- video_path: {video.video_path or '(미생성)'}
- duration: {video.duration_sec}s / slides: {video.slide_count}

## 검수 이슈
{chr(10).join(f'- {i}' for i in review.issues) or '- (없음)'}
"""
