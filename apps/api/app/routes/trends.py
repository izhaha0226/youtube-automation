from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from itertools import combinations

from fastapi import APIRouter, Query

from app.modules.trend.benchmark import fetch_all_benchmarks
from app.modules.trend.naver_trend import fetch_search_trend
from app.modules.trend.scanner import fetch_community, scan

router = APIRouter()

STOPWORDS = {
    "있는", "하는", "되는", "있다", "없다", "한다", "된다", "했다", "됐다", "됩니다",
    "이렇게", "앞으로", "그래서", "하지만", "그러나", "그리고", "때문에", "하면서",
    "이번", "대한", "통해", "위한", "관련", "따른", "관한", "대해", "결국", "어떻게",
    "하고", "되고", "하며", "으로", "에서", "까지", "부터", "이상", "이하", "해야",
    "것은", "것이", "것을", "것에", "중인", "가능", "예정", "이런", "저런", "어떤",
    "지난", "올해", "오늘", "내일", "현재", "최근", "아직", "벌써", "이미", "다시",
    "진짜", "정말", "매우", "많은", "모든", "각종", "다양한", "또한", "과연", "역시",
    "돼요", "해요", "있어", "없어", "합니다", "입니다", "습니다", "겠습", "보겠",
    "알아", "봤더", "봤습", "했습", "됐습", "다만", "만약", "여전", "그냥", "조금",
    "기자", "뉴스", "보도", "속보", "영상", "전문가", "시청자", "오르고",
    "올라", "내려", "떨어", "나오는", "들어", "시작", "계속", "발생", "나온다",
    "연합뉴스", "한겨레", "중앙일보", "조선일보", "매일경제", "한국경제", "머니투데이",
    "the", "and", "for", "with", "from", "that", "this", "are", "was", "has",
    "you", "your", "how", "what", "why", "who", "which", "will",
}

NOUN_PATTERN = re.compile(r"[가-힣A-Z]{2,12}")
PERIOD_MAP = {"today": 1, "3d": 3, "7d": 7, "30d": 30}

KEYWORD_CLUSTERS: dict[str, list[str]] = {
    "금리·대출": [
        "금리", "기준금리", "대출", "주담대", "전세대출", "정책대출", "DSR", "LTV", "스트레스DSR", "연준",
    ],
    "아파트·공급": [
        "아파트", "청약", "분양", "분양가상한제", "미분양", "입주물량", "재건축", "재개발", "공급부족", "매수심리",
    ],
    "전세·월세": [
        "전세", "월세", "역전세", "전세사기", "보증금", "전세보증보험", "월세전환", "갭투자", "실거주", "임대차",
    ],
    "정책·세제": [
        "규제", "완화", "세금", "양도세", "종부세", "취득세", "특별법", "장특공", "정부", "정책",
    ],
    "지역·교통": [
        "서울", "강남", "잠실", "용산", "마포", "송파", "GTX", "반도체", "클러스터", "토지거래허가구역",
    ],
}

CLUSTER_BY_KEYWORD = {keyword: cluster for cluster, keywords in KEYWORD_CLUSTERS.items() for keyword in keywords}
SUPPLEMENTAL_KEYWORDS = [kw for keywords in KEYWORD_CLUSTERS.values() for kw in keywords]

POLITICAL_TERMS = {
    "대선", "총선", "지방선거", "보궐선거", "선거", "후보", "유세", "출마", "공천",
    "선거사무소", "당대표", "원내대표", "대통령", "국회", "의회", "정당", "여야",
    "민주당", "국민의힘", "조국혁신당", "개혁신당", "이재명", "윤석열", "한동훈", "장동혁",
    "오세훈", "정원오", "홍준표", "김문수", "안철수", "유승민", "이준석", "나경원",
    "탄핵", "특검", "정쟁", "정계", "정치권",
}

ECONOMIC_TERMS = {
    "경제", "금리", "기준금리", "대출", "주담대", "전세대출", "정책대출", "DSR", "LTV",
    "집값", "부동산", "아파트", "전세", "월세", "매매", "청약", "분양", "미분양",
    "재건축", "재개발", "공급", "세금", "양도세", "종부세", "취득세", "규제", "완화",
    "정책", "환율", "주식", "증시", "코스피", "코스닥", "연준", "Fed", "달러", "물가", "CPI",
    "GDP", "무역", "부채", "PF", "임대차", "보증금", "GTX", "토지거래허가구역",
}


def is_political_text(text: str) -> bool:
    normalized = text.replace(" ", "")
    return any(term in text or term in normalized for term in POLITICAL_TERMS)


def is_economic_text(text: str) -> bool:
    return any(term in text for term in ECONOMIC_TERMS)


def filter_economic_items(items: list[dict]) -> list[dict]:
    filtered: list[dict] = []
    for item in items:
        text = " ".join(str(item.get(key, "")) for key in ("title", "desc", "query", "source"))
        if is_political_text(text):
            continue
        if not is_economic_text(text):
            continue
        filtered.append(item)
    return filtered


def extract_nouns(text: str) -> list[str]:
    tokens = NOUN_PATTERN.findall(text)
    return [token for token in tokens if token not in STOPWORDS]


def parse_any_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    now = datetime.now(timezone.utc)
    relative = re.search(r"(\d+)\s*(분|시간|일|주|개월|년)\s*전", raw)
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2)
        if unit == "분":
            return now - timedelta(minutes=amount)
        if unit == "시간":
            return now - timedelta(hours=amount)
        if unit == "일":
            return now - timedelta(days=amount)
        if unit == "주":
            return now - timedelta(weeks=amount)
        if unit == "개월":
            return now - timedelta(days=amount * 30)
        if unit == "년":
            return now - timedelta(days=amount * 365)
    if raw.strip() in {"오늘", "방금 전", "방금전"}:
        return now
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        pass
    try:
        dt = parsedate_to_datetime(raw)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def format_basis(dt: datetime | None) -> str:
    if not dt:
        return "데이터 없음"
    local = dt.astimezone(timezone.utc)
    return local.strftime("%Y-%m-%d %H:%M UTC")


def filter_by_period(items: list[dict], date_key: str, days: int | None) -> list[dict]:
    if days is None:
        return items
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    filtered = []
    for item in items:
        dt = parse_any_datetime(item.get(date_key))
        if dt is None or dt >= cutoff:
            filtered.append(item)
    return filtered


def infer_news_provider(item: dict) -> str:
    provider = (item.get("provider") or "").lower()
    if provider in {"naver", "google"}:
        return provider
    source = (item.get("source") or "").lower()
    if "google" in source:
        return "google"
    return "naver"


def make_documents(*groups: tuple[str, list[dict]]) -> list[dict]:
    docs: list[dict] = []
    for source_id, items in groups:
        for item in items:
            title = item.get("title", "")
            keywords = list(dict.fromkeys(extract_nouns(title)))
            docs.append({"source": source_id, "title": title, "keywords": keywords})
    return docs


def build_keyword_universe(noun_freq: Counter, docs: list[dict]) -> list[str]:
    keywords = [keyword for keyword, _ in noun_freq.most_common(40)]
    seen = set(keywords)

    seed_hits = {kw for doc in docs for kw in doc["keywords"] if kw in CLUSTER_BY_KEYWORD}
    for hit in list(seed_hits):
        cluster = CLUSTER_BY_KEYWORD.get(hit)
        if not cluster:
            continue
        for keyword in KEYWORD_CLUSTERS[cluster]:
            if keyword not in seen:
                keywords.append(keyword)
                seen.add(keyword)

    for keyword in SUPPLEMENTAL_KEYWORDS:
        if len(keywords) >= 40:
            break
        if keyword not in seen:
            keywords.append(keyword)
            seen.add(keyword)

    return keywords[:40]


def build_keyword_map(docs: list[dict], keywords: list[str]) -> dict:
    per_keyword_sources: dict[str, Counter] = {keyword: Counter() for keyword in keywords}
    doc_sets: dict[str, set[int]] = {keyword: set() for keyword in keywords}

    for idx, doc in enumerate(docs):
        doc_keywords = set(doc["keywords"])
        for keyword in keywords:
            if keyword in doc_keywords:
                per_keyword_sources[keyword][doc["source"]] += 1
                doc_sets[keyword].add(idx)

    keyword_rows = []
    for keyword in keywords:
        sources = per_keyword_sources[keyword]
        total = sum(sources.values())
        cluster = CLUSTER_BY_KEYWORD.get(keyword, "기타")
        keyword_rows.append(
            {
                "keyword": keyword,
                "count": total,
                "sources": [source for source, count in sources.items() if count > 0],
                "naver": sources.get("naver", 0),
                "google": sources.get("google", 0),
                "youtube": sources.get("youtube", 0),
                "cluster": cluster,
                "source_score": len([1 for count in sources.values() if count > 0]),
            }
        )

    keyword_rows.sort(key=lambda row: (row["source_score"], row["count"], row["keyword"]), reverse=True)

    correlation_rows = []
    for source, target in combinations([row["keyword"] for row in keyword_rows], 2):
        source_docs = doc_sets[source]
        target_docs = doc_sets[target]
        if not source_docs and not target_docs:
            continue
        union = source_docs | target_docs
        if not union:
            continue
        intersection = source_docs & target_docs
        cluster_bonus = 0.15 if CLUSTER_BY_KEYWORD.get(source) == CLUSTER_BY_KEYWORD.get(target) else 0.0
        score = round(len(intersection) / len(union) + cluster_bonus, 3)
        if score > 0:
            correlation_rows.append(
                {
                    "source": source,
                    "target": target,
                    "score": score,
                    "cluster": CLUSTER_BY_KEYWORD.get(source) if CLUSTER_BY_KEYWORD.get(source) == CLUSTER_BY_KEYWORD.get(target) else "교차",
                }
            )

    if len(correlation_rows) < 10:
        seen_pairs = {(row["source"], row["target"]) for row in correlation_rows}
        for cluster, cluster_keywords in KEYWORD_CLUSTERS.items():
            active_keywords = [keyword for keyword in cluster_keywords if keyword in {row["keyword"] for row in keyword_rows[:30]}]
            for source, target in combinations(active_keywords[:6], 2):
                pair = (source, target)
                if pair in seen_pairs:
                    continue
                correlation_rows.append({"source": source, "target": target, "score": 0.25, "cluster": cluster})
                seen_pairs.add(pair)
                if len(correlation_rows) >= 12:
                    break
            if len(correlation_rows) >= 12:
                break

    correlation_rows.sort(key=lambda row: row["score"], reverse=True)

    clusters = []
    top_keywords = {row["keyword"] for row in keyword_rows[:30]}
    for cluster, cluster_keywords in KEYWORD_CLUSTERS.items():
        active = [keyword for keyword in cluster_keywords if keyword in top_keywords]
        if active:
            clusters.append({"name": cluster, "keywords": active[:8], "count": len(active)})

    return {
        "keywords": keyword_rows[:40],
        "correlations": correlation_rows[:20],
        "clusters": clusters[:6],
    }


def latest_basis(items: list[dict], key: str) -> str:
    dates = [parse_any_datetime(item.get(key)) for item in items]
    latest = max([dt for dt in dates if dt is not None], default=None)
    return format_basis(latest)


def compact_trend_item(item: dict) -> dict:
    return {
        "title": item.get("title", ""),
        "source": item.get("source", ""),
        "provider": item.get("provider") or infer_news_provider(item),
        "query": item.get("query", ""),
        "pub": item.get("pub"),
        "published": item.get("published"),
        "url": item.get("url") or item.get("link"),
        "link": item.get("link") or item.get("url"),
        "channel": item.get("channel"),
        "views": int(item.get("views") or 0),
    }


def item_matches_keyword(item: dict, keyword: str) -> bool:
    text = " ".join(str(item.get(key, "")) for key in ("title", "desc", "query", "source", "channel"))
    if keyword in text:
        return True
    cluster = CLUSTER_BY_KEYWORD.get(keyword)
    if not cluster:
        return False
    return any(cluster_keyword in text for cluster_keyword in KEYWORD_CLUSTERS.get(cluster, []))


def issue_title_for_keyword(keyword: str, cluster: str) -> str:
    templates = {
        "금리·대출": f"{keyword}, 지금 대출·전세 시장에서 놓치면 늦는 신호",
        "아파트·공급": f"{keyword}, 집값 방향이 갈리는 공급 신호 3가지",
        "전세·월세": f"{keyword}, 세입자와 집주인이 지금 봐야 할 반전 조건",
        "정책·세제": f"{keyword}, 정책 변화가 내 집값에 미칠 실제 영향",
        "지역·교통": f"{keyword}, 지역 가격을 움직일 수 있는 핵심 변수",
        "기타": f"{keyword}, 오늘 부동산·경제 영상으로 풀어야 할 핵심 이슈",
    }
    return templates.get(cluster, templates["기타"])


def content_angle_for_cluster(cluster: str) -> str:
    if cluster in {"금리·대출", "전세·월세"}:
        return "경고형"
    if cluster == "정책·세제":
        return "판단형"
    if cluster in {"아파트·공급", "지역·교통"}:
        return "구조해설형"
    return "기회형"


def richgo_signals_for_cluster(cluster: str) -> list[str]:
    signals = {
        "금리·대출": ["리치고 데이터로 월 상환액 변화 확인", "전세가율·매매가 대비 대출 부담 비교", "지역별 거래량 둔화 여부 확인"],
        "아파트·공급": ["리치고 데이터로 입주물량·미분양 확인", "청약 경쟁률과 실거래가 흐름 비교", "지역별 매물 증가 여부 확인"],
        "전세·월세": ["리치고 데이터로 전세가율 확인", "전월세 전환 흐름과 거래량 비교", "보증금 리스크 지역 확인"],
        "정책·세제": ["리치고 데이터로 정책 전후 가격 반응 확인", "실거래가·거래량·매물 변화 비교", "세금 부담 변화가 수요에 미치는 영향 확인"],
        "지역·교통": ["리치고 데이터로 지역별 실거래가 추세 확인", "교통 호재 전후 거래량 비교", "인접 지역 가격 전이 확인"],
    }
    return signals.get(cluster, ["리치고 데이터로 실거래가·거래량·전세가율 확인", "뉴스 이슈와 실제 숫자 차이 검증", "지역별 반응 차이 확인"])


def build_recommended_issues(*, naver_news: list[dict], google_news: list[dict], youtube_items: list[dict], keyword_map: dict) -> list[dict]:
    all_news = naver_news + google_news
    candidates: list[dict] = []
    seen_keywords: set[str] = set()

    for row in keyword_map.get("keywords", [])[:24]:
        keyword = row["keyword"]
        if keyword in seen_keywords:
            continue
        cluster = row.get("cluster") or CLUSTER_BY_KEYWORD.get(keyword, "기타")
        related_articles = [item for item in all_news if item_matches_keyword(item, keyword)]
        related_youtube = [item for item in youtube_items if item_matches_keyword(item, keyword)]
        if not related_articles and not related_youtube:
            continue

        recent_bonus = 0
        for item in related_articles[:6] + related_youtube[:4]:
            dt = parse_any_datetime(item.get("pub") or item.get("published"))
            if dt and (datetime.now(timezone.utc) - dt) <= timedelta(days=1):
                recent_bonus += 6

        youtube_views = sum(int(item.get("views") or 0) for item in related_youtube[:5])
        youtube_score = min(25, youtube_views // 50000)
        source_score = len(set(row.get("sources", []))) * 14
        policy_bonus = 12 if cluster in {"금리·대출", "정책·세제", "전세·월세"} else 6
        score = int(row.get("count", 0) * 8 + source_score + recent_bonus + youtube_score + policy_bonus)
        priority = "오늘 찍기" if score >= 55 else "3일 안에 찍기" if score >= 35 else "데이터 확인 후"
        sorted_youtube = sorted(related_youtube, key=lambda item: int(item.get("views") or 0), reverse=True)
        sorted_articles = sorted(
            related_articles,
            key=lambda item: parse_any_datetime(item.get("pub")) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        candidates.append(
            {
                "rank": 0,
                "title": issue_title_for_keyword(keyword, cluster),
                "keyword": keyword,
                "cluster": cluster,
                "score": score,
                "shooting_priority": priority,
                "content_angle": content_angle_for_cluster(cluster),
                "why_now": f"왜 지금 찍어야 하는가: {keyword}가 {', '.join(row.get('sources', []) or ['뉴스'])}에서 동시에 잡혔고, 기사 {len(sorted_articles)}건·관련 영상 {len(sorted_youtube)}건으로 확인됩니다.",
                "hook": f"지금 {keyword}만 보면 늦습니다. 실제로 갈리는 조건은 따로 있습니다.",
                "representative_articles": [compact_trend_item(item) for item in sorted_articles[:4]],
                "related_youtube": [compact_trend_item(item) for item in sorted_youtube[:3]],
                "keywords": list(dict.fromkeys([keyword] + KEYWORD_CLUSTERS.get(cluster, [])[:5])),
                "selection_titles": [item.get("title", "") for item in sorted_articles[:4]],
                "richgo_data_signals": richgo_signals_for_cluster(cluster),
            }
        )
        seen_keywords.add(keyword)

    candidates.sort(key=lambda item: (item["score"], len(item["representative_articles"]), len(item["related_youtube"])), reverse=True)

    diversified: list[dict] = []
    used_clusters: set[str] = set()
    for candidate in candidates:
        cluster = candidate["cluster"]
        if cluster in used_clusters and len(diversified) < 3:
            continue
        diversified.append(candidate)
        used_clusters.add(cluster)
        if len(diversified) == 3:
            break
    if len(diversified) < 3:
        for candidate in candidates:
            if candidate not in diversified:
                diversified.append(candidate)
            if len(diversified) == 3:
                break

    for index, candidate in enumerate(diversified[:3], start=1):
        candidate["rank"] = index
    return diversified[:3]


def build_source_sections(*, naver_news: list[dict], google_news: list[dict], youtube_items: list[dict], keyword_map: dict, timeline_source: str) -> list[dict]:
    top_keyword_names = [row["keyword"] for row in keyword_map["keywords"]]
    return [
        {
            "id": "naver",
            "label": "네이버 트렌드",
            "basis_label": "기준 날짜",
            "basis_value": latest_basis(naver_news, "pub"),
            "subtext": timeline_source or "네이버 뉴스/검색 기반",
            "keywords": [keyword for keyword in top_keyword_names if any(row["keyword"] == keyword and row["naver"] > 0 for row in keyword_map["keywords"])][:12],
            "items": naver_news[:8],
        },
        {
            "id": "google",
            "label": "구글 트렌드 시그널",
            "basis_label": "기준 날짜",
            "basis_value": latest_basis(google_news, "pub"),
            "subtext": "Google News RSS 기반 이슈 시그널",
            "keywords": [keyword for keyword in top_keyword_names if any(row["keyword"] == keyword and row["google"] > 0 for row in keyword_map["keywords"])][:12],
            "items": google_news[:8],
        },
        {
            "id": "youtube",
            "label": "유튜브 트렌드",
            "basis_label": "발행 기준",
            "basis_value": latest_basis(youtube_items, "published"),
            "subtext": "YouTube Data API 조회수/좋아요 기반",
            "keywords": [keyword for keyword in top_keyword_names if any(row["keyword"] == keyword and row["youtube"] > 0 for row in keyword_map["keywords"])][:12],
            "items": youtube_items[:8],
        },
    ]


@router.get("")
def trends_scan(period: str = Query("7d", enum=["today", "3d", "7d", "30d", "custom"]), start: str | None = None, end: str | None = None):
    snap = scan()
    benchmarks = fetch_all_benchmarks()

    days = PERIOD_MAP.get(period)
    if period == "custom" and start and end:
        try:
            s = datetime.fromisoformat(start)
            e = datetime.fromisoformat(end)
            days = (e - s).days or 7
        except ValueError:
            days = 7

    yt_filtered = filter_economic_items(filter_by_period(snap.youtube, "published", days))
    news_filtered = filter_economic_items(filter_by_period(snap.news, "pub", days))
    community_filtered = filter_economic_items(filter_by_period(snap.community, "pub", days))
    naver_news = [item for item in news_filtered if infer_news_provider(item) == "naver"]
    google_news = [item for item in news_filtered if infer_news_provider(item) == "google"]

    docs = make_documents(("naver", naver_news), ("google", google_news), ("youtube", yt_filtered), ("community", community_filtered))
    noun_freq: Counter = Counter()
    for doc in docs:
        for keyword in doc["keywords"]:
            noun_freq[keyword] += 1

    keyword_universe = build_keyword_universe(noun_freq, docs)
    keyword_chart = [{"keyword": keyword, "count": noun_freq.get(keyword, 0)} for keyword in keyword_universe[:30]]

    category_counts = [
        {"category": "경제 뉴스", "count": len([n for n in news_filtered if any(k in n.get("title", "") for k in ["금리", "경제", "CPI", "환율", "무역", "GDP"])])},
        {"category": "부동산", "count": len([n for n in news_filtered if any(k in n.get("title", "") for k in ["부동산", "집값", "아파트", "전세", "매매", "분양"])])},
        {"category": "정책/규제", "count": len([n for n in news_filtered if any(k in n.get("title", "") for k in ["정책", "규제", "정부", "법안", "대출", "세금"])])},
        {"category": "글로벌", "count": len([n for n in news_filtered if any(k in n.get("title", "") for k in ["미국", "중국", "글로벌", "연준", "Fed", "달러"])])},
    ]

    top3 = [item["keyword"] for item in keyword_chart[:3]]
    timeline_data = fetch_search_trend(top3, days=days or 7) if top3 else []
    timeline_source = "Naver DataLab 검색어 트렌드 API" if timeline_data else ""

    if not timeline_data and top3:
        daily: dict[str, dict[str, int]] = {}
        for item in yt_filtered + news_filtered:
            dt = parse_any_datetime(item.get("published") or item.get("pub"))
            if not dt:
                continue
            day = dt.strftime("%m/%d")
            if day not in daily:
                daily[day] = {kw: 0 for kw in top3}
            title = item.get("title", "")
            for kw in top3:
                if kw in title:
                    daily[day][kw] += 1
        today = datetime.now(timezone.utc)
        timeline_days = max(days or 7, 1)
        for i in range(timeline_days - 1, -1, -1):
            d = today - timedelta(days=i)
            day = d.strftime("%m/%d")
            entry: dict[str, str | int] = {"date": day}
            for kw in top3:
                entry[kw] = daily.get(day, {}).get(kw, 0)
            timeline_data.append(entry)
        timeline_source = "뉴스/YouTube 언급 빈도 (fallback)"

    keyword_map = build_keyword_map(docs, keyword_universe)
    source_sections = build_source_sections(
        naver_news=naver_news,
        google_news=google_news,
        youtube_items=yt_filtered,
        keyword_map=keyword_map,
        timeline_source=timeline_source,
    )
    recommended_issues = build_recommended_issues(
        naver_news=naver_news,
        google_news=google_news,
        youtube_items=yt_filtered,
        keyword_map=keyword_map,
    )

    period_label = {"today": "오늘", "3d": "최근 3일", "7d": "최근 7일", "30d": "최근 30일", "custom": f"{start}~{end}"}

    return {
        "period": period,
        "period_label": period_label.get(period, period),
        "youtube": yt_filtered[:15],
        "news": news_filtered[:15],
        "community": community_filtered[:5],
        "internal": snap.internal[:10],
        "keywords": [row["keyword"] for row in keyword_map["keywords"][:30]],
        "benchmarks": benchmarks[:20],
        "source_sections": source_sections,
        "recommended_issues": recommended_issues,
        "keyword_map": keyword_map,
        "charts": {
            "keyword_frequency": keyword_chart,
            "category_distribution": category_counts,
            "top3_timeline": timeline_data,
            "top3_keywords": top3,
            "timeline_source": timeline_source,
        },
    }


@router.get("/community")
def trends_community(limit: int = Query(30, ge=1, le=100)):
    """커뮤니티(네이버 카페 + 부동산 RSS) 트렌딩 키워드 전용 엔드포인트."""
    items = fetch_community()

    cafe_items = [i for i in items if i.get("type") == "cafe"]
    rss_items = [i for i in items if i.get("type") == "rss"]

    noun_freq: dict[str, int] = Counter()
    for item in items:
        for noun in extract_nouns(item.get("title", "")):
            noun_freq[noun] += 1

    keyword_chart = [
        {"keyword": k, "count": v}
        for k, v in sorted(noun_freq.items(), key=lambda x: -x[1])[:20]
    ]

    return {
        "total": len(items),
        "cafe": cafe_items[:limit],
        "rss": rss_items[:limit],
        "keywords": [kc["keyword"] for kc in keyword_chart],
        "charts": {
            "keyword_frequency": keyword_chart,
            "source_distribution": [
                {"source": s, "count": c}
                for s, c in Counter(i.get("source", "") for i in items).most_common()
            ],
        },
    }
