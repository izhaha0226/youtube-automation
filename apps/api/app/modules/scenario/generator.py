from __future__ import annotations

import json
import re

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
        body_sections=_normalize_body_sections(data.get("body_sections", []), data.get("body", [])),
        conclusion=data.get("conclusion", ""),
        action_takeaways=data.get("action_takeaways", []),
        cta=data.get("cta", ""),
        title_candidates=data.get("title_candidates", []),
        thumbnail_candidates=data.get("thumbnail_candidates", []),
        opening=data.get("opening", ""),
        opening_title=data.get("opening_title", ""),
        estimated_duration_min=data.get("estimated_duration_min", payload.target_duration_min),
    )
    out = _sanitize_scenario_output(_ensure_richgo_data_section(out))
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
    news_examples = _source_titles(payload.selected_articles) or _source_titles(payload.selected_videos)
    news_a = news_examples[0] if len(news_examples) > 0 else f"{first_keyword} 관련 시장 뉴스"
    news_b = news_examples[1] if len(news_examples) > 1 else f"{focus}를 둘러싼 후속 보도"
    news_c = news_examples[2] if len(news_examples) > 2 else "거래량과 금리 변화를 다룬 기사"
    body_sections = [
        _section(
            "1. 오늘 이 이슈를 봐야 하는 이유",
            "뉴스 반응이 아니라 판단 기준으로 접근",
            f"오늘 주제는 '{topic}'입니다. {news_a}만 보면 시장이 곧바로 한 방향으로 움직일 것처럼 보일 수 있습니다. 그런데 김기원 대표 관점에서 보면 첫 번째 질문은 '오르냐, 내리냐'가 아닙니다. 이 뉴스가 실제 매수자와 세입자의 행동을 바꿀 만큼 강한 신호인지부터 봐야 합니다. 예를 들어 금리 뉴스가 나왔더라도 대출 한도, 월 상환액, 전세 가격이 같이 움직이지 않으면 체감 시장은 바로 바뀌지 않습니다. 그래서 오늘은 기사 제목을 따라가는 게 아니라, {focus}가 같은 방향으로 움직이는지 확인하겠습니다. 끝까지 보시면 지금 움직일 사람과 기다릴 사람을 나누는 기준을 잡으실 수 있습니다.",
            "지금 필요한 것은 결론보다 체크리스트입니다.",
            "article" if payload.selected_articles else "mixed",
            news_a,
        ),
        _section(
            "2. 뉴스 제목과 실제 시장 사이의 간격",
            "헤드라인과 체감 시장을 분리",
            f"두 번째로 봐야 할 것은 뉴스 제목과 실제 현장의 간격입니다. {news_b}처럼 강한 표현의 보도가 나오면 많은 분들이 '이제 시장이 바뀌는 건가' 하고 바로 반응합니다. 하지만 현장에서는 매도자가 가격을 내리는 속도, 매수자가 대출을 실행하는 속도, 세입자가 전세를 선택하는 속도가 전부 다릅니다. 예를 들어 전세 세입자라면 집값 전망보다 내 보증금 안전성과 다음 갱신 시점의 전세 물량이 더 중요합니다. 매수 대기자라면 기사 하나보다 같은 단지의 호가와 실거래 차이가 줄어드는지를 봐야 합니다. 뉴스는 방향을 알려주지만, 행동 타이밍은 숫자가 알려줍니다.",
            "헤드라인은 신호이고, 행동은 실거래·호가·대출 부담으로 판단합니다.",
            "article" if payload.selected_articles else "mixed",
            news_b,
        ),
        _section(
            "3. 실수요자는 무엇을 먼저 봐야 하나",
            "실거주 안정성과 월 부담 우선",
            f"실수요자는 투자자처럼 움직이면 안 됩니다. {news_c}에서 시장 분위기가 좋아 보이더라도, 내 월 부담이 감당 가능한지가 먼저입니다. 예를 들어 4인 가족이 학군 때문에 이사를 고민한다면, 집값이 조금 더 오를 것 같다는 이유만으로 서두르면 안 됩니다. 대출 금리가 0.5%포인트만 달라져도 월 상환액은 체감될 정도로 바뀔 수 있습니다. 또 전세에서 매매로 넘어갈 때는 취득세, 이사비, 수리비까지 한 번에 들어갑니다. 그래서 실수요자는 '가격이 오를까'보다 '이 집을 5년 이상 흔들리지 않고 보유할 수 있나'를 먼저 물어야 합니다.",
            "실수요자는 상승 기대보다 보유 지속 가능성을 먼저 봅니다.",
            "mixed",
            news_c,
        ),
        _section(
            "4. 리치고 데이터 확인 및 분석",
            "리치고 데이터로 거래·전세·대출 신호 확인",
            f"여기서 중간 점검을 하겠습니다. 지금부터는 기사 표현을 잠깐 내려놓고 리치고 데이터를 확인해서 분석하는 구간입니다. 먼저 관심 지역의 최근 실거래가와 거래량이 같이 움직이는지 봅니다. 가격만 올랐는데 거래량이 줄었다면 시장 전체가 강해진 게 아니라 일부 거래만 튄 것일 수 있습니다. 다음으로 전세가율과 전세 매물 변화를 봅니다. 전세가 받쳐주지 않으면 매매 상승은 오래 버티기 어렵습니다. 마지막으로 대출 금리와 월 상환액을 같이 보겠습니다. 같은 {first_keyword} 이슈라도 내 월 부담이 감당 가능한지에 따라 결론은 완전히 달라집니다. 이 데이터 확인을 거쳐야 오늘 주제가 실제 행동 신호인지, 아니면 더 지켜봐야 할 뉴스인지 구분할 수 있습니다.",
            "리치고 데이터로 실거래·거래량·전세가율·월 상환액을 확인합니다.",
            "internal",
            "리치고 데이터 확인 구간",
        ),
        _section(
            "5. 투자자는 출구와 보유비용을 먼저 봐야 한다",
            "좋은 이야기보다 빠져나올 수 있는 구조",
            f"투자자라면 관점이 또 달라집니다. 뉴스에서 특정 지역이나 정책 수혜가 언급되면 기회처럼 보일 수 있습니다. 하지만 투자 판단에서는 들어가는 이유보다 나오는 이유가 더 중요합니다. 예를 들어 단기 호재로 가격이 움직이는 지역이라도 거래량이 얇으면 원하는 시점에 팔기 어렵습니다. 보유세, 이자, 공실 가능성까지 계산하면 겉으로 보이는 수익률이 크게 줄어들 수 있습니다. 그래서 {first_keyword} 이슈를 볼 때도 '얼마나 오를까'보다 '누가 다음 매수자가 될까'를 확인해야 합니다. 이 질문에 답이 안 나오면 좋은 뉴스도 아직 내 투자는 아닐 수 있습니다.",
            "투자는 진입보다 출구와 보유비용이 먼저입니다.",
            "mixed",
            first_keyword,
        ),
        _section(
            "6. 반대로 봐야 할 리스크와 예외",
            "모든 뉴스가 같은 방향으로 작동하지 않음",
            "여기서 반드시 반대로 봐야 할 부분도 있습니다. 같은 뉴스라도 서울 핵심지, 수도권 외곽, 지방 구축 시장에 미치는 영향은 다릅니다. 금리 부담이 낮아지는 뉴스는 매수 심리를 살릴 수 있지만, 소득 대비 가격이 너무 높은 지역에서는 거래 회복이 제한될 수 있습니다. 정책 완화 뉴스도 마찬가지입니다. 규제가 풀렸다고 모든 지역이 오르는 게 아니라, 이미 수요가 있는 지역에서 먼저 반응합니다. 그래서 시청자분들은 본인 지역을 볼 때 '전국 평균'이 아니라 우리 동네 입주 물량, 전세가율, 급매 소진 속도를 봐야 합니다. 예외를 보지 않으면 뉴스는 맞았는데 내 판단은 틀릴 수 있습니다.",
            "전국 뉴스는 지역별로 다르게 번역해야 합니다.",
            "internal",
            "지역별 예외와 리스크",
        ),
        _section(
            "7. 지금 숫자로 확인할 체크포인트",
            "감정 대신 확인할 숫자를 고정",
            f"이제 실제로 무엇을 확인할지 정리해보겠습니다. 첫 번째는 거래량입니다. 가격이 올랐다는 뉴스보다 중요한 것은 그 가격에 실제 거래가 따라붙었는지입니다. 두 번째는 전세가율입니다. 전세가 받쳐주지 않는 매매 상승은 오래가기 어렵습니다. 세 번째는 대출 가능 금액과 월 상환액입니다. 같은 {first_keyword} 뉴스라도 소득이 높은 가구와 대출 여력이 부족한 가구에게는 완전히 다르게 작동합니다. 네 번째는 매물의 질입니다. 급매가 사라진 것인지, 아니면 안 팔리는 매물이 가격만 높여놓은 것인지 구분해야 합니다. 다섯 번째는 실패 기준입니다. 숫자를 확인했는데 거래량이 줄고 전세가가 밀리고 대출 부담이 커진다면, 뉴스가 좋아 보여도 이번 판단은 보류해야 합니다. 이 다섯 가지를 같이 보면 뉴스가 실제 시장을 움직이는지, 아니면 분위기만 만든 것인지 훨씬 분명해집니다.",
            "거래량·전세가율·월 상환액·매물 질을 같이 봅니다.",
            "mixed",
            "핵심 지표 체크리스트",
        ),
        _section(
            "8. 최종 판단 프레임",
            "가격·금리·정책·지역 수요를 합쳐 판단",
            f"정리하면 오늘의 핵심은 단순합니다. 첫째, 뉴스가 말하는 방향과 실제 숫자가 같은 방향인지 봅니다. 둘째, 내 포지션이 실수요자인지 투자자인지 먼저 나눕니다. 셋째, {focus} 중에서 최소 두 가지 이상이 같은 결론을 가리킬 때만 행동 후보로 올립니다. 예를 들어 매수 대기자라면 관심 단지의 급매가 줄고, 전세가가 버티고, 대출 부담이 감당 가능할 때 검토할 수 있습니다. 반대로 뉴스는 좋아 보여도 거래량이 없고 호가만 올라가면 기다리는 편이 낫습니다. 특히 내 집 마련을 고민하는 분들은 남들이 산다는 말보다 내가 버틸 수 있는 기간을 먼저 봐야 합니다. 투자자라면 상승 가능성보다 손실이 났을 때 버틸 현금흐름을 먼저 계산해야 합니다. 시장은 맞히는 대상이 아니라 대응하는 대상입니다. 오늘 영상의 목적도 정답을 찍는 것이 아니라, 여러분이 자기 상황에 맞는 기준을 갖게 하는 것입니다.",
            "두 개 이상의 신호가 맞을 때만 행동 후보로 봅니다.",
            "mixed",
            focus,
        ),
    ]
    body = [section["script"] for section in body_sections]
    opening_title = f"{topic}, 지금 움직여도 될까?"
    hook_30s = _build_fallback_hook_30s(topic)
    return _sanitize_scenario_output(_ensure_richgo_data_section(ScenarioOutput(
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
            "집값 뉴스에 흔들리지 않는 매수 체크리스트",
        ],
        thumbnail_candidates=[
            "지금 사도 될까?",
            "기다릴 사람 vs 움직일 사람",
            "부동산 판단 기준 3가지",
        ],
        opening="오늘 시장은 단순히 오른다, 내린다로 말하기 어렵습니다. 그래서 기준부터 잡아야 합니다.",
        opening_title=opening_title,
        estimated_duration_min=payload.target_duration_min,
    )))


def _section(
    heading: str,
    summary: str,
    script: str,
    viewer_takeaway: str,
    reference_type: str,
    reference_hint: str,
) -> dict:
    return {
        "heading": heading,
        "script": script,
        "narration": script,
        "summary": summary,
        "reference_type": reference_type,
        "reference_hint": reference_hint,
        "viewer_takeaway": viewer_takeaway,
    }


def _build_fallback_hook_30s(topic: str) -> str:
    clean_topic = re.sub(r"\s+", " ", topic or "오늘 이 이슈").strip()
    return (
        f"오늘 주제는 '{clean_topic}'입니다. "
        "문제는 이걸 보고 지금 사야 하는 사람과 기다려야 하는 사람이 완전히 갈린다는 겁니다. "
        "오늘은 키워드를 따라가는 게 아니라 실거래가, 거래량, 전세가율, 대출 금리와 월 상환액 기준으로 "
        "내 상황에서 움직여도 되는지 판단하는 3가지 기준을 잡아보겠습니다."
    )


def _source_titles(sources: list[dict]) -> list[str]:
    titles: list[str] = []
    for source in sources:
        title = str(source.get("title") or source.get("headline") or source.get("summary") or "").strip()
        if title:
            titles.append(title[:90])
    return titles


def _keywords_from_sources(payload: ScenarioInput) -> list[str]:
    values: list[str] = []
    for source in [*payload.selected_articles, *payload.selected_videos]:
        for keyword in source.get("keywords", []) or []:
            if isinstance(keyword, str) and keyword.strip():
                values.append(keyword.strip())
    return values


def _normalize_body_sections(sections: list[dict], body: list[str]) -> list[dict]:
    normalized: list[dict] = []
    for index, raw in enumerate(sections or []):
        if not isinstance(raw, dict):
            continue
        script = str(raw.get("script") or raw.get("narration") or "").strip()
        narration = str(raw.get("narration") or script).strip()
        normalized.append(
            {
                **raw,
                "heading": str(raw.get("heading") or f"섹션 {index + 1}"),
                "summary": str(raw.get("summary") or ""),
                "script": script,
                "narration": narration,
                "reference_type": str(raw.get("reference_type") or ""),
                "reference_hint": str(raw.get("reference_hint") or ""),
                "viewer_takeaway": str(raw.get("viewer_takeaway") or ""),
            }
        )
    if normalized:
        return normalized
    return [
        {
            "heading": f"섹션 {index + 1}",
            "summary": "",
            "script": str(script),
            "narration": str(script),
            "reference_type": "internal",
            "reference_hint": "본문 요약에서 자동 구성",
            "viewer_takeaway": "",
        }
        for index, script in enumerate(body or [])
        if str(script).strip()
    ]


def _strip_forbidden_scenario_terms(text: str) -> str:
    text = re.sub(r"(?<!\S)#[^\s#]+", "", text or "")
    text = text.replace("리치고식", "김기원 대표 기준")
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def _sanitize_scenario_output(out: ScenarioOutput) -> ScenarioOutput:
    data = out.model_dump()
    for key in ["hook", "hook_30s", "bridge_3min", "conclusion", "cta", "opening", "opening_title"]:
        data[key] = _strip_forbidden_scenario_terms(str(data.get(key, "")))
    data["body"] = [_strip_forbidden_scenario_terms(str(item)) for item in data.get("body", [])]
    data["title_candidates"] = [_strip_forbidden_scenario_terms(str(item)) for item in data.get("title_candidates", [])]
    data["thumbnail_candidates"] = [_strip_forbidden_scenario_terms(str(item)) for item in data.get("thumbnail_candidates", [])]
    sanitized_sections = []
    for section in data.get("body_sections", []):
        sanitized = dict(section)
        for key in ["heading", "summary", "script", "narration", "reference_hint", "viewer_takeaway"]:
            sanitized[key] = _strip_forbidden_scenario_terms(str(sanitized.get(key, "")))
        sanitized_sections.append(sanitized)
    data["body_sections"] = sanitized_sections
    return ScenarioOutput(**data)


def _ensure_richgo_data_section(out: ScenarioOutput) -> ScenarioOutput:
    if any("리치고 데이터" in section.heading or "리치고 데이터를 확인" in section.narration for section in out.body_sections):
        return out
    data_section = {
        "heading": "리치고 데이터 확인 및 분석",
        "summary": "중간에 리치고 데이터로 실거래·전세·대출 신호를 확인",
        "script": "여기서 중간 점검을 하겠습니다. 지금부터는 기사 표현을 잠깐 내려놓고 리치고 데이터를 확인해서 분석하는 구간입니다. 최근 실거래가와 거래량이 같이 움직이는지, 전세가율과 전세 매물이 버티는지, 대출 금리와 월 상환액이 감당 가능한지를 차례로 보겠습니다. 이 데이터 확인을 거쳐야 오늘 주제가 실제 행동 신호인지, 아니면 더 지켜봐야 할 뉴스인지 구분할 수 있습니다.",
        "narration": "여기서 중간 점검을 하겠습니다. 지금부터는 기사 표현을 잠깐 내려놓고 리치고 데이터를 확인해서 분석하는 구간입니다. 최근 실거래가와 거래량이 같이 움직이는지, 전세가율과 전세 매물이 버티는지, 대출 금리와 월 상환액이 감당 가능한지를 차례로 보겠습니다. 이 데이터 확인을 거쳐야 오늘 주제가 실제 행동 신호인지, 아니면 더 지켜봐야 할 뉴스인지 구분할 수 있습니다.",
        "reference_type": "internal",
        "reference_hint": "리치고 데이터 확인 구간",
        "viewer_takeaway": "뉴스 해석 전 실제 숫자로 확인한다.",
    }
    body_sections = [section.model_dump() if hasattr(section, "model_dump") else dict(section) for section in out.body_sections]
    insert_at = min(3, len(body_sections))
    body_sections.insert(insert_at, data_section)
    body = [str(section.get("script") or section.get("narration") or "") for section in body_sections]
    data = out.model_dump()
    data["body_sections"] = body_sections
    data["body"] = body
    return ScenarioOutput(**data)
