from __future__ import annotations

import json

from app.core.llm import LLMError, llm
from app.core.logging import get_logger
from app.core.prompts import load_prompt, render
from app.modules.richgo.editorial import editorial_rules_context, philosophy_context
from app.schemas import ScenarioInput, ScenarioOutput

log = get_logger(__name__)


def generate_scenario(payload: ScenarioInput) -> ScenarioOutput:
    system = (
        "You are the scenario writer for the 리치고 channel. "
        "구어체 한국어로 작성. Output valid JSON only."
    )
    user = render(
        load_prompt("scenario_generate"),
        topic=payload.topic,
        channel=payload.channel,
        tone=payload.tone,
        archetype=payload.archetype,
        keywords=", ".join(payload.keywords) or "(없음)",
        reference_points=", ".join(payload.reference_points) or "(없음)",
        selected_articles_json=json.dumps(payload.selected_articles, ensure_ascii=False),
        selected_videos_json=json.dumps(payload.selected_videos, ensure_ascii=False),
        target_duration_min=payload.target_duration_min,
        target_duration_max=payload.target_duration_max,
        session_id=payload.session_id or "(없음)",
        kim_kiwon_philosophy=philosophy_context(),
        editorial_rules=editorial_rules_context(),
    )
    try:
        data = llm(temperature=0.6).generate_json(system=system, user=user)
    except LLMError as e:
        log.warning("scenario.gen.fallback", error=str(e), topic=payload.topic)
        return _fallback_scenario(payload)

    out = ScenarioOutput(
        hook=data.get("hook", ""),
        hook_30s=data.get("hook_30s", data.get("hook", "")),
        bridge_3min=data.get("bridge_3min", ""),
        archetype=data.get("archetype", payload.archetype),
        body=data.get("body", []),
        body_sections=data.get("body_sections", []),
        conclusion=data.get("conclusion", ""),
        action_takeaways=data.get("action_takeaways", []),
        cta=data.get("cta", ""),
        title_candidates=data.get("title_candidates", []),
        thumbnail_candidates=data.get("thumbnail_candidates", []),
        opening=data.get("opening", ""),
        opening_title=data.get("opening_title", ""),
        estimated_duration_min=data.get("estimated_duration_min", payload.target_duration_min),
    )
    log.info(
        "scenario.gen.done",
        hook_len=len(out.hook),
        body=len(out.body),
        titles=len(out.title_candidates),
    )
    return out


def _fallback_scenario(payload: ScenarioInput) -> ScenarioOutput:
    """Deterministic fallback so the Scenario button works when the configured LLM/CLI is unavailable."""
    keywords = [kw for kw in payload.keywords if kw] or _keywords_from_sources(payload)
    keywords = list(dict.fromkeys(keywords))[:5] or ["부동산", "금리", "서울"]
    focus = " · ".join(keywords[:3])
    topic = payload.topic.strip()
    first_keyword = keywords[0]
    body_sections = [
        {
            "heading": "1. 오늘 이 이슈를 봐야 하는 이유",
            "script": f"오늘 주제는 '{topic}'입니다. 핵심은 {focus}가 같은 방향을 가리키는지 먼저 확인하는 겁니다. 뉴스 제목 하나만 보고 움직이면 늦거나 과하게 반응할 수 있습니다.",
            "summary": "뉴스 반응이 아니라 판단 기준으로 접근",
            "viewer_takeaway": "지금 필요한 것은 결론보다 체크리스트입니다.",
        },
        {
            "heading": "2. 사도 되는 구간과 기다려야 하는 구간",
            "script": f"첫째, 가격이 버티는 지역인지 봅니다. 둘째, 금리와 대출 조건이 실제 부담을 낮추는지 봅니다. 셋째, {first_keyword} 관련 정책 변화가 매수자에게 유리한지 불리한지 분리해서 봐야 합니다.",
            "summary": "가격·금리·정책을 분리해서 판단",
            "viewer_takeaway": "세 조건 중 둘 이상이 맞아야 행동 후보입니다.",
        },
        {
            "heading": "3. 리치고식 최종 판단 프레임",
            "script": "실수요자는 거주 안정성과 현금흐름을 먼저 보고, 투자자는 출구와 보유 비용을 먼저 봐야 합니다. 둘을 섞으면 '좋은 이야기'에는 반응하지만 실제 의사결정은 흔들립니다.",
            "summary": "실수요와 투자를 분리",
            "viewer_takeaway": "내 포지션부터 정해야 같은 데이터도 다르게 해석됩니다.",
        },
    ]
    body = [section["script"] for section in body_sections]
    opening_title = f"{topic}, 지금 움직여도 될까?"
    hook_30s = f"{focus} 때문에 시장이 헷갈립니다. 오늘은 사야 하는 사람과 기다려야 하는 사람을 3가지 기준으로 나눠보겠습니다."
    return ScenarioOutput(
        hook=hook_30s,
        hook_30s=hook_30s,
        bridge_3min="먼저 뉴스의 분위기보다 숫자와 조건을 분리해 보겠습니다. 지금 시장은 같은 이슈라도 실수요자와 투자자에게 완전히 다르게 작동합니다.",
        archetype=payload.archetype,
        body=body,
        body_sections=body_sections,
        conclusion="결론은 단순합니다. 내가 감당 가능한 현금흐름, 지역의 수요, 정책 변화의 방향이 동시에 맞으면 검토하고, 하나라도 흔들리면 기다리는 쪽이 안전합니다.",
        action_takeaways=[
            "관심 지역의 최근 실거래와 매물 증감을 같이 확인한다.",
            "대출 금리 1%p 변화가 월 부담에 미치는 영향을 계산한다.",
            "정책 뉴스는 매수자·보유자·매도자 중 누구에게 유리한지 나눠 읽는다.",
        ],
        cta="댓글에 관심 지역과 상황을 남겨주시면 다음 영상에서 판단 기준으로 다시 풀어보겠습니다.",
        title_candidates=[
            f"{topic}, 지금 사도 될까? 판단 기준 3가지",
            f"{first_keyword} 이슈 이후 부동산 시장, 기다릴 사람과 움직일 사람",
            f"집값 뉴스에 흔들리지 않는 리치고식 매수 체크리스트",
        ],
        thumbnail_candidates=[
            "지금 사도 될까?",
            "기다릴 사람 vs 움직일 사람",
            "부동산 판단 기준 3가지",
        ],
        opening="오늘 시장은 단순히 오른다, 내린다로 말하기 어렵습니다. 그래서 기준부터 잡아야 합니다.",
        opening_title=opening_title,
        estimated_duration_min=payload.target_duration_min,
    )


def _keywords_from_sources(payload: ScenarioInput) -> list[str]:
    values: list[str] = []
    for source in [*payload.selected_articles, *payload.selected_videos]:
        for keyword in source.get("keywords", []) or []:
            if isinstance(keyword, str) and keyword.strip():
                values.append(keyword.strip())
    return values
