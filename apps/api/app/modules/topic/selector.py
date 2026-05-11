from __future__ import annotations

import difflib
import hashlib
import html
import json
import re
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.core.llm import LLMError, llm
from app.core.logging import get_logger
from app.core.prompts import load_prompt, render
from app.models import VideoAnalysisCache
from app.modules.richgo.editorial import content_archetype_context, editorial_rules_context, philosophy_context
from app.modules.trend.scanner import scan  # used as fallback when no pre-fetched data
from app.schemas import TopicCandidate, TopicInput, TopicProductionApplication, TopicResult, TopicScore, TopicVideoAnalysis

log = get_logger(__name__)
MAX_SELECTED_VIDEOS = 3
BAD_TITLE_PHRASES = ("뉴스 제목은 이게 아닙니다", "뉴스 제목은")


def select_topic(payload: TopicInput) -> TopicResult:
    selected_videos = [_normalize_video_source(v) for v in payload.selected_videos if _normalize_video_source(v)]
    selected_videos = _attach_cached_video_analyses(selected_videos)
    if len(selected_videos) > MAX_SELECTED_VIDEOS:
        raise ValueError(f"영상 분석은 최대 {MAX_SELECTED_VIDEOS}개까지만 가능합니다.")
    if payload.current_issues and any(str(issue).startswith("[VIDEO]") for issue in payload.current_issues) and not selected_videos:
        raise ValueError("영상 분석 주제 생성에는 선택 영상 원본 데이터가 필요합니다. 관련 유튜브에서 영상을 먼저 선택하세요.")

    if payload.current_issues or payload.trend_keywords:
        current_issues = payload.current_issues
        trend_keywords = payload.trend_keywords
    else:
        snap = scan()
        current_issues = snap.as_current_issues()
        trend_keywords = snap.keywords()

    system = (
        "You are the topic-selection agent for the 리치고 channel. "
        "Follow the IO spec strictly. Output valid JSON only."
    )
    user = render(
        load_prompt("topic_select"),
        channel=payload.channel,
        user_intent=payload.user_intent or "(없음)",
        avoid_keywords=", ".join(payload.avoid_keywords) or "(없음)",
        must_include=", ".join(payload.must_include) or "(없음)",
        current_issues=json.dumps(current_issues, ensure_ascii=False),
        trend_keywords=", ".join(trend_keywords[:30]) or "(없음)",
        selected_video_analysis=json.dumps(_selected_video_prompt_payload(selected_videos), ensure_ascii=False) if selected_videos else "[]",
        source_mode=("video-analysis" if selected_videos else "research-backed" if payload.current_issues or payload.trend_keywords else "trend-scan"),
        target_speed="오늘 바로 촬영 가능한 주제를 우선",
        kim_kiwon_philosophy=philosophy_context(),
        editorial_rules=editorial_rules_context(),
        content_archetype_guide=content_archetype_context(),
    )
    try:
        data = llm(temperature=0.5).generate_json(system=system, user=user)
    except LLMError as e:
        log.warning("topic.select.fallback", error=str(e))
        return _fallback_topic_result(payload, current_issues, trend_keywords)

    rules = settings.scoring_rules
    threshold_recommend = rules.get("thresholds", {}).get("recommend", 18)
    top_k = rules.get("top_k", 3)

    source_titles = _source_titles(current_issues, selected_videos)
    raw_to_title: dict[str, str] = {}
    candidates = []
    for idx, c in enumerate(data.get("recommended_topics", [])):
        score = TopicScore(**c.get("score", {}))
        if score.total() < threshold_recommend:
            continue
        decision_label = c.get("decision_label")
        if decision_label not in {"scale", "iterate", "stop", "data_missing"}:
            decision_label = "scale" if score.total() >= 24 else "iterate" if score.total() >= threshold_recommend else "stop"
        raw_title = c.get("title", "")
        title = _sanitize_topic_hook(_rewrite_if_source_copy(raw_title, source_titles, trend_keywords, idx), source_titles, trend_keywords, idx)
        raw_to_title[raw_title] = title
        candidates.append(
            TopicCandidate(
                title=title,
                reason=c.get("reason", ""),
                score=score,
                archetype=c.get("archetype", "판단형"),
                risk=c.get("risk", ""),
                keywords=c.get("keywords", []),
                discovery_hypothesis=c.get("discovery_hypothesis", c.get("reason", "")),
                strategy_hypothesis=c.get("strategy_hypothesis", c.get("reason", "")),
                tactical_hypothesis=c.get("tactical_hypothesis", c.get("risk", "")),
                verification_signals=c.get("verification_signals", []),
                failure_criteria=c.get("failure_criteria", []),
                decision_label=decision_label,
                next_loop=c.get("next_loop", ""),
                hypothesis_payload=c.get("hypothesis_payload", {}),
            )
        )
    candidates.sort(key=lambda c: c.score.total(), reverse=True)
    candidates = candidates[:top_k]

    selected = data.get("selected_topic") or (candidates[0].title if candidates else "")
    selected = raw_to_title.get(selected, selected)
    selected = _sanitize_topic_hook(selected, source_titles, trend_keywords, 0) if selected else selected
    selected_candidate = next((candidate for candidate in candidates if candidate.title == selected), None)
    selected_was_filtered = selected_candidate is None and bool(candidates)
    if selected_was_filtered:
        selected_candidate = candidates[0]
        selected = selected_candidate.title

    reason = data.get("selected_reason") if not selected_was_filtered else ""
    reason = reason or (selected_candidate.reason if selected_candidate else "")
    selected_archetype = selected_candidate.archetype if selected_candidate else "판단형"

    result = TopicResult(
        recommended_topics=candidates,
        selected_topic=selected,
        selected_reason=reason,
        selected_archetype=selected_archetype,
        video_analyses=_build_video_analyses(data.get("video_analyses"), selected_videos),
        production_application=_build_production_application(data.get("production_application"), selected_videos),
    )
    _save_video_analysis_cache(selected_videos, result.video_analyses)
    log.info("topic.select.done", count=len(candidates), selected=selected)
    return result


def _fallback_topic_result(payload: TopicInput, current_issues: list[str], trend_keywords: list[str]) -> TopicResult:
    """Deterministic fallback so /api/topics does not 503 when Codex/LLM is unavailable."""
    selected_videos = [_normalize_video_source(v) for v in payload.selected_videos if _normalize_video_source(v)]
    video_analyses = _build_video_analyses(None, selected_videos)
    production_application = _build_production_application(None, selected_videos)
    primary_issue = _clean_issue(current_issues[0]) if current_issues else (payload.user_intent or "오늘 부동산 시장 핵심 변화")
    keywords = list(dict.fromkeys([kw for kw in trend_keywords[:8] if kw])) or ["부동산", "금리", "아파트"]
    focus = " · ".join(keywords[:3])
    anchor = _topic_anchor(primary_issue, keywords)
    templates = [
        ("판단형", f"{anchor}, 대부분 아직 모르는 내 집값 신호 3가지"),
        ("구조해설형", f"다들 {keywords[0]}만 보지만 실제로 갈리는 건 이 조건입니다"),
        ("기회형", f"불안한 사람이 놓치면 늦는 {focus}의 반전 조건"),
    ]
    candidates: list[TopicCandidate] = []
    for idx, (archetype, title) in enumerate(templates):
        score = TopicScore(popularity=4, economy=4, realestate=5, virality=4 - min(idx, 1), richgo_fit=5, discussion=4)
        candidates.append(
            TopicCandidate(
                title=title,
                reason="LLM 호출 실패 시에도 촬영을 멈추지 않도록 선택 이슈와 트렌드 키워드 기반으로 자동 생성한 후보입니다.",
                score=score,
                archetype=archetype,
                risk="실시간 근거와 실제 데이터 확인 후 표현 강도를 조정해야 합니다.",
                keywords=keywords[:5],
                discovery_hypothesis=f"{focus} 조합은 오늘 시청자가 바로 판단하고 싶은 문제와 연결됩니다.",
                strategy_hypothesis="리치고 관점의 숫자 기반 판단 프레임으로 뉴스 요약과 차별화합니다.",
                tactical_hypothesis="오프닝은 선택지를 선명하게 던지고, 본문은 데이터→판단 기준→실행/보류 조건 순서로 구성합니다.",
                verification_signals=["CTR", "유지율", "댓글 질문", "저장", "공유"],
                failure_criteria=["클릭률 저조", "뉴스 요약 반응만 발생", "실행 기준이 모호하다는 댓글"],
                decision_label="iterate" if idx else "scale",
                next_loop="업로드 후 실제 성과와 댓글 질문으로 다음 주제 각도를 재검증합니다.",
            )
        )
    return TopicResult(
        recommended_topics=candidates,
        selected_topic=candidates[0].title,
        selected_reason=candidates[0].reason,
        selected_archetype=candidates[0].archetype,
        video_analyses=video_analyses,
        production_application=production_application,
    )


def _source_titles(current_issues: list[str], selected_videos: list[dict]) -> list[str]:
    titles = [_clean_issue(issue) for issue in current_issues if issue]
    titles.extend(str(video.get("title") or "") for video in selected_videos)
    return [title.strip() for title in titles if title and title.strip()]


def _normalize_title_for_similarity(title: str) -> str:
    title = html.unescape(str(title or "")).lower()
    title = re.sub(r"\[(article|video)\]", "", title)
    title = re.sub(r"[^0-9a-z가-힣]+", "", title)
    return title


def _is_source_copy(title: str, source_titles: list[str]) -> bool:
    normalized = _normalize_title_for_similarity(title)
    if len(normalized) < 6:
        return False
    for source in source_titles:
        source_norm = _normalize_title_for_similarity(source)
        if len(source_norm) < 6:
            continue
        if normalized == source_norm:
            return True
        if normalized in source_norm or source_norm in normalized:
            return True
        if difflib.SequenceMatcher(None, normalized, source_norm).ratio() >= 0.72:
            return True
    return False


def _topic_anchor(source_title: str, keywords: list[str]) -> str:
    cleaned = _clean_issue(source_title)
    for token in ["...", "…", "｜", "|", "-", "—", ":"]:
        cleaned = cleaned.split(token)[0]
    words = re.findall(r"[0-9A-Za-z가-힣]+", cleaned)
    stopwords = {"속보", "단독", "종합", "영상", "뉴스", "오늘", "이번", "관련", "발표"}
    meaningful = [word for word in words if word not in stopwords]
    if len(meaningful) >= 2:
        return " ".join(meaningful[:4])
    return " · ".join(keywords[:2]) if keywords else "부동산 시장"


def _rewrite_if_source_copy(title: str, source_titles: list[str], keywords: list[str], index: int) -> str:
    title = str(title or "").strip()
    if not _is_source_copy(title, source_titles):
        return title
    anchor = _topic_anchor(source_titles[0] if source_titles else title, keywords)
    key = keywords[index % len(keywords)] if keywords else "부동산"
    templates = [
        f"{anchor}, 대부분 아직 모르는 내 집값 신호 3가지",
        f"다들 {key}만 보는데 실제로 갈리는 건 이 조건입니다",
        f"지금 불안한 사람이 놓치면 늦는 {anchor}의 반전 조건",
    ]
    return templates[index % len(templates)]


def _sanitize_topic_hook(title: str, source_titles: list[str], keywords: list[str], index: int) -> str:
    title = str(title or "").strip()
    if any(phrase in title for phrase in BAD_TITLE_PHRASES):
        return _curiosity_hook(source_titles, keywords, index)
    return title


def _curiosity_hook(source_titles: list[str], keywords: list[str], index: int) -> str:
    anchor = _topic_anchor(source_titles[0] if source_titles else "", keywords)
    key = keywords[index % len(keywords)] if keywords else "부동산"
    templates = [
        f"{anchor}, 대부분 아직 모르는 내 집값 신호 3가지",
        f"다들 {key}만 보는데 실제로 갈리는 건 이 조건입니다",
        f"지금 불안한 사람이 놓치면 늦는 {anchor}의 반전 조건",
    ]
    return templates[index % len(templates)]


def _video_cache_key(video: dict) -> str:
    identity = video.get("youtube_video_id") or video.get("url") or f"{video.get('channel', '')}:{video.get('title', '')}"
    normalized = _normalize_title_for_similarity(identity)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _attach_cached_video_analyses(selected_videos: list[dict]) -> list[dict]:
    enriched: list[dict] = []
    for video in selected_videos:
        item = dict(video)
        cache_key = _video_cache_key(item)
        item["analysis_cache"] = "miss"
        item["cache_key"] = cache_key
        try:
            with Session(engine) as session:
                cached = session.get(VideoAnalysisCache, cache_key)
        except SQLAlchemyError as exc:
            log.warning("topic.video_analysis_cache.load_failed", error=str(exc))
            cached = None
        if cached and cached.analysis:
            item["analysis_cache"] = "hit"
            item["cached_analysis"] = cached.analysis
        enriched.append(item)
    return enriched


def _selected_video_prompt_payload(selected_videos: list[dict]) -> list[dict]:
    payload: list[dict] = []
    for video in selected_videos:
        base = {
            "youtube_video_id": video.get("youtube_video_id"),
            "title": video.get("title"),
            "channel": video.get("channel"),
            "url": video.get("url"),
            "views": video.get("views"),
            "published_at": video.get("published_at"),
            "duration": video.get("duration"),
            "analysis_cache": video.get("analysis_cache", "miss"),
        }
        if video.get("cached_analysis"):
            base["cached_analysis"] = video["cached_analysis"]
        else:
            base.update(
                {
                    "most_watched_scene": video.get("most_watched_scene"),
                    "most_watched_time": video.get("most_watched_time"),
                    "hook_type": video.get("hook_type"),
                    "creative_score": video.get("creative_score"),
                    "patterns": video.get("patterns"),
                }
            )
        payload.append(base)
    return payload


def _analysis_to_cache_payload(analysis: TopicVideoAnalysis) -> dict:
    return {
        "title": analysis.title,
        "channel": analysis.channel,
        "content_summary": analysis.content_summary,
        "duration": analysis.duration,
        "production_intent": analysis.production_intent,
        "most_watched_time": analysis.most_watched_time,
        "most_watched_scene": analysis.most_watched_scene,
        "hook_takeaway": analysis.hook_takeaway,
        "views": analysis.views,
        "url": analysis.url,
    }


def _save_video_analysis_cache(selected_videos: list[dict], analyses: list[TopicVideoAnalysis]) -> None:
    if not selected_videos or not analyses:
        return
    now = datetime.utcnow()
    try:
        with Session(engine) as session:
            for idx, video in enumerate(selected_videos[:MAX_SELECTED_VIDEOS]):
                analysis = analyses[idx] if idx < len(analyses) else None
                if not analysis:
                    continue
                cache_key = video.get("cache_key") or _video_cache_key(video)
                row = session.get(VideoAnalysisCache, cache_key)
                payload = _analysis_to_cache_payload(analysis)
                if row:
                    row.analysis = payload
                    row.source_snapshot = _selected_video_prompt_payload([video])[0]
                    row.updated_at = now
                else:
                    row = VideoAnalysisCache(
                        cache_key=cache_key,
                        youtube_video_id=video.get("youtube_video_id"),
                        url=video.get("url", ""),
                        title=video.get("title", ""),
                        channel=video.get("channel", ""),
                        analysis=payload,
                        source_snapshot=_selected_video_prompt_payload([video])[0],
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(row)
            session.commit()
    except SQLAlchemyError as exc:
        log.warning("topic.video_analysis_cache.save_failed", error=str(exc))


def _build_video_analyses(raw_analyses: object, selected_videos: list[dict]) -> list[TopicVideoAnalysis]:
    by_title = {}
    if isinstance(raw_analyses, list):
        for raw in raw_analyses:
            if isinstance(raw, dict):
                title = html.unescape(str(raw.get("title") or "")).strip()
                if title:
                    by_title[title] = raw

    analyses: list[TopicVideoAnalysis] = []
    raw_list = [raw for raw in raw_analyses if isinstance(raw, dict)] if isinstance(raw_analyses, list) else []
    for idx, video in enumerate(selected_videos[:MAX_SELECTED_VIDEOS]):
        raw = by_title.get(video["title"], raw_list[idx] if idx < len(raw_list) else video.get("cached_analysis", {}))
        most_watched_scene = raw.get("most_watched_scene") or video.get("most_watched_scene") or "가장 많이 시청한 장면 데이터 없음"
        most_watched_time = raw.get("most_watched_time") or video.get("most_watched_time") or "data_missing"
        analyses.append(
            TopicVideoAnalysis(
                title=raw.get("title") or video["title"],
                channel=raw.get("channel") or video.get("channel", ""),
                content_summary=raw.get("content_summary") or _default_content_summary(video),
                duration=raw.get("duration") or video.get("duration") or "분량 데이터 없음",
                production_intent=raw.get("production_intent") or _default_production_intent(video),
                most_watched_time=most_watched_time,
                most_watched_scene=most_watched_scene,
                hook_takeaway=raw.get("hook_takeaway") or _default_hook_takeaway(video),
                views=video.get("views", 0),
                url=video.get("url", ""),
            )
        )
    return analyses


def _build_production_application(raw: object, selected_videos: list[dict]) -> TopicProductionApplication:
    if isinstance(raw, dict):
        return TopicProductionApplication(
            opening_strategy=raw.get("opening_strategy") or "",
            structure_strategy=raw.get("structure_strategy") or "",
            scene_strategy=raw.get("scene_strategy") or "",
            topic_generation_basis=raw.get("topic_generation_basis") or "",
        )
    if not selected_videos:
        return TopicProductionApplication()
    top_video = max(selected_videos, key=lambda item: item.get("views", 0))
    missing_scene = any("데이터 없음" in str(video.get("most_watched_scene", "")) for video in selected_videos)
    return TopicProductionApplication(
        opening_strategy=f"우리 영상은 첫 10초에 '{top_video['title']}'처럼 결론형 질문을 먼저 던지고, 첫 30초 안에 시청자 선택지를 제시합니다.",
        structure_strategy="선택 영상들의 조회수·분량·훅 패턴을 비교해 정책/시장 이슈를 리치고식 데이터 판단표로 재구성합니다.",
        scene_strategy=(
            "가장 많이 시청한 장면 데이터가 없으므로 임의 장면은 만들지 않고, 제목·조회수·훅 구조를 도입부 설계 근거로만 사용합니다."
            if missing_scene
            else "가장 많이 시청한 시간대의 장면 구조를 도입부 문제 제기와 1분 내 데이터 제시 구간에 반영합니다."
        ),
        topic_generation_basis="각 선택 영상의 내용, 분량, 제작의도, 조회수, 훅/장면 단서를 주제 후보 점수와 도입 전략에 반영합니다.",
    )


def _default_content_summary(video: dict) -> str:
    return f"'{video['title']}'의 제목·채널·조회수·훅 패턴을 기준으로 시청자가 궁금해하는 시장 판단 문제를 요약합니다."


def _default_production_intent(video: dict) -> str:
    hook = video.get("hook_type") or "unknown"
    return f"{hook} 훅으로 시청자의 불안/궁금증을 즉시 자극하고, 조회수 {video.get('views', 0)} 흐름을 이용해 클릭을 확보하려는 의도입니다."


def _default_hook_takeaway(video: dict) -> str:
    scene = video.get("most_watched_scene") or "가장 많이 시청한 장면 데이터 없음"
    return f"우리 도입부에는 제목의 긴장감, {video.get('duration', '분량 데이터 없음')} 분량감, 장면 단서({scene})를 데이터 판단 질문으로 변환합니다."


def _clean_issue(issue: str) -> str:
    return issue.replace("[ARTICLE]", "").replace("[VIDEO]", "").strip()


def _normalize_video_source(raw: dict) -> dict:
    if not isinstance(raw, dict):
        return {}
    title = html.unescape(str(raw.get("title") or "")).strip()
    if not title:
        return {}
    analysis = raw.get("creative_analysis") or {}
    views = raw.get("views") or 0
    try:
        views = int(views)
    except (TypeError, ValueError):
        views = 0
    most_watched_scene = raw.get("most_watched_scene") or raw.get("retention_peak") or "가장 많이 시청한 장면 데이터 없음"
    most_watched_time = raw.get("most_watched_time") or raw.get("retention_peak_time") or "data_missing"
    return {
        "youtube_video_id": raw.get("youtube_video_id") or raw.get("video_id") or raw.get("id"),
        "title": title,
        "channel": html.unescape(str(raw.get("channel") or "")).strip(),
        "url": raw.get("url") or "",
        "views": views,
        "published_at": raw.get("published_at") or raw.get("published") or "",
        "duration": raw.get("duration") or raw.get("duration_text") or "분량 데이터 없음",
        "most_watched_scene": most_watched_scene,
        "most_watched_time": most_watched_time,
        "hook_type": analysis.get("hook_type") or raw.get("hook_type") or "unknown",
        "creative_score": analysis.get("score"),
        "patterns": analysis.get("patterns") or [],
    }
