from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from app.modules.trend.benchmark import fetch_all_benchmarks
from app.modules.trend.naver_trend import fetch_search_trend
from app.modules.trend.scanner import fetch_community, scan

router = APIRouter()

STOPWORDS = {
    # 용언/부사/조사/접속사
    "있는", "하는", "되는", "있다", "없다", "한다", "된다", "했다", "됐다", "됩니다",
    "이렇게", "앞으로", "그래서", "하지만", "그러나", "그리고", "때문에", "하면서",
    "이번", "대한", "통해", "위한", "관련", "따른", "관한", "대해", "결국", "어떻게",
    "하고", "되고", "하며", "으로", "에서", "까지", "부터", "이상", "이하", "해야",
    "것은", "것이", "것을", "것에", "중인", "가능", "예정", "이런", "저런", "어떤",
    "지난", "올해", "오늘", "내일", "현재", "최근", "아직", "벌써", "이미", "다시",
    "진짜", "정말", "매우", "많은", "모든", "각종", "다양한", "또한", "과연", "역시",
    "돼요", "해요", "있어", "없어", "합니다", "입니다", "습니다", "겠습", "보겠",
    "알아", "봤더", "봤습", "했습", "됐습", "다만", "만약", "여전", "그냥", "조금",
    # 미디어/기능어/동사파편
    "기자", "뉴스", "보도", "속보", "영상", "전문가", "시청자", "오르고",
    "올라", "내려", "떨어", "나오는", "들어", "시작", "계속", "발생", "나온다",
    "연합뉴스", "한겨레", "중앙일보", "조선일보", "매일경제", "한국경제", "머니투데이",
    "the", "and", "for", "with", "from", "that", "this", "are", "was", "has",
    "you", "the", "your", "how", "what", "why", "who", "which", "will",
}

NOUN_PATTERN = re.compile(r"[가-힣]{2,6}|[A-Z]{2,}")


def extract_nouns(text: str) -> list[str]:
    tokens = NOUN_PATTERN.findall(text)
    return [t for t in tokens if t not in STOPWORDS]


def filter_by_period(items: list[dict], date_key: str, days: int | None) -> list[dict]:
    if days is None:
        return items
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    filtered = []
    for item in items:
        raw = item.get(date_key, "")
        if not raw:
            filtered.append(item)
            continue
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if dt >= cutoff:
                filtered.append(item)
        except (ValueError, TypeError):
            filtered.append(item)
    return filtered


PERIOD_MAP = {"today": 1, "3d": 3, "7d": 7, "30d": 30}


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

    yt_filtered = filter_by_period(snap.youtube, "published", days)
    news_filtered = filter_by_period(snap.news, "pub", days)

    # 명사 키워드만 추출
    all_titles = (
        [x.get("title", "") for x in yt_filtered]
        + [x.get("title", "") for x in news_filtered]
        + [x.get("title", "") for x in snap.community]
    )
    noun_freq: dict[str, int] = Counter()
    for t in all_titles:
        for noun in extract_nouns(t):
            noun_freq[noun] += 1

    keyword_chart = [{"keyword": k, "count": v} for k, v in sorted(noun_freq.items(), key=lambda x: -x[1])[:20]]

    category_counts = [
        {"category": "경제 뉴스", "count": len([n for n in news_filtered if any(k in n.get("title", "") for k in ["금리", "경제", "CPI", "환율", "무역", "GDP"])])},
        {"category": "부동산", "count": len([n for n in news_filtered if any(k in n.get("title", "") for k in ["부동산", "집값", "아파트", "전세", "매매", "분양"])])},
        {"category": "정책/규제", "count": len([n for n in news_filtered if any(k in n.get("title", "") for k in ["정책", "규제", "정부", "법안", "대출", "세금"])])},
        {"category": "글로벌", "count": len([n for n in news_filtered if any(k in n.get("title", "") for k in ["미국", "중국", "글로벌", "연준", "Fed", "달러"])])},
    ]

    # Top 3 키워드의 30일 검색 트렌드
    top3 = [kc["keyword"] for kc in keyword_chart[:3]]
    timeline_data = fetch_search_trend(top3, days=30)
    timeline_source = "Naver DataLab 검색어 트렌드 API" if timeline_data else ""

    # Naver DataLab 없으면 뉴스 발행일 기반 fallback
    if not timeline_data and top3:
        all_items = snap.youtube + snap.news
        daily: dict[str, dict[str, int]] = {}
        for item in all_items:
            raw = item.get("published") or item.get("pub") or ""
            if not raw:
                continue
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(raw)
                except Exception:
                    continue
            day = dt.strftime("%m/%d")
            if day not in daily:
                daily[day] = {kw: 0 for kw in top3}
            title = item.get("title", "")
            for kw in top3:
                if kw in title:
                    daily[day][kw] += 1
        today = datetime.now(timezone.utc)
        for i in range(30, -1, -1):
            d = today - timedelta(days=i)
            day = d.strftime("%m/%d")
            entry: dict[str, str | int] = {"date": day}
            for kw in top3:
                entry[kw] = daily.get(day, {}).get(kw, 0)
            timeline_data.append(entry)
        timeline_source = "뉴스/YouTube 언급 빈도 (fallback)"
    else:
        timeline_source = "Naver DataLab 검색어 트렌드 API"

    period_label = {"today": "오늘", "3d": "최근 3일", "7d": "최근 7일", "30d": "최근 30일", "custom": f"{start}~{end}"}

    return {
        "period": period,
        "period_label": period_label.get(period, period),
        "youtube": yt_filtered[:15],
        "news": news_filtered[:15],
        "community": snap.community[:5],
        "internal": snap.internal[:10],
        "keywords": [kc["keyword"] for kc in keyword_chart[:20]],
        "benchmarks": benchmarks[:20],
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

    # 소스별 분류
    cafe_items = [i for i in items if i.get("type") == "cafe"]
    rss_items = [i for i in items if i.get("type") == "rss"]

    # 커뮤니티 제목에서 명사 키워드 추출
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
