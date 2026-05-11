from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.routes import trends as trends_route
from app.modules.trend import scanner as trend_scanner
from app.modules.trend.scanner import TrendSnapshot


def _pub(days_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def test_trends_scan_excludes_political_items_and_keywords(monkeypatch):
    snap = TrendSnapshot(
        youtube=[
            {"title": "서울 아파트 전세대출 금리 분석", "published": _pub(1), "source": "youtube_fallback"},
            {"title": "이재명 후보 선거 유세 현장", "published": _pub(1), "source": "youtube_fallback"},
        ],
        news=[
            {"title": "서울 아파트 전세대출 금리 다시 오른다", "pub": _pub(1), "source": "경제신문", "provider": "google", "query": "부동산"},
            {"title": "장동혁 후보 선거사무소 개소", "pub": _pub(1), "source": "정치신문", "provider": "naver", "query": "정치"},
        ],
        community=[
            {"title": "강남 전세 월세 전환 증가", "pub": _pub(1), "source": "커뮤니티"},
            {"title": "국민의힘 대선 공약 발표", "pub": _pub(1), "source": "커뮤니티"},
        ],
        internal=[],
    )
    monkeypatch.setattr(trends_route, "scan", lambda: snap)
    monkeypatch.setattr(trends_route, "fetch_all_benchmarks", lambda: [])
    monkeypatch.setattr(trends_route, "fetch_search_trend", lambda keywords, days=30: [])

    result = trends_route.trends_scan(period="7d")
    serialized = str(result)

    assert "서울 아파트 전세대출" in serialized
    for banned in ["장동혁", "이재명", "후보", "선거", "국민의힘", "대선"]:
        assert banned not in serialized


def test_trends_scan_recommends_top3_editor_issues(monkeypatch):
    snap = TrendSnapshot(
        youtube=[
            {"title": "전세대출 금리 상승이 전세 시장에 미치는 영향", "published": _pub(0), "source": "youtube_fallback", "views": 210000, "url": "https://youtu.be/rent-loan"},
            {"title": "서울 아파트 공급 부족과 청약 전략", "published": _pub(0), "source": "youtube_fallback", "views": 160000, "url": "https://youtu.be/supply"},
            {"title": "코스피 연준 금리 전망과 주식 대응", "published": _pub(0), "source": "youtube_fallback", "views": 110000, "url": "https://youtu.be/stock"},
        ],
        news=[
            {"title": "서울 아파트 전세대출 금리 다시 오른다", "pub": _pub(0), "source": "경제신문", "provider": "naver", "query": "전세대출"},
            {"title": "전세대출 금리 상승에 세입자 월 상환액 부담 커진다", "pub": _pub(0), "source": "부동산신문", "provider": "google", "query": "금리"},
            {"title": "서울 아파트 공급 부족에 청약 경쟁률 상승", "pub": _pub(1), "source": "경제신문", "provider": "naver", "query": "청약"},
            {"title": "정부 공급 대책에도 미분양 지역 온도차", "pub": _pub(1), "source": "경제신문", "provider": "google", "query": "공급"},
            {"title": "연준 금리 전망에 코스피 주식 시장 출렁", "pub": _pub(1), "source": "증권신문", "provider": "google", "query": "주식"},
        ],
        community=[],
        internal=[],
    )
    monkeypatch.setattr(trends_route, "scan", lambda: snap)
    monkeypatch.setattr(trends_route, "fetch_all_benchmarks", lambda: [])
    monkeypatch.setattr(trends_route, "fetch_search_trend", lambda keywords, days=30: [])

    result = trends_route.trends_scan(period="3d")
    recommendations = result["recommended_issues"]

    assert len(recommendations) == 3
    first = recommendations[0]
    assert first["rank"] == 1
    assert "전세대출" in first["title"] or "금리" in first["title"]
    assert first["score"] >= recommendations[1]["score"] >= recommendations[2]["score"]
    assert first["shooting_priority"] in {"오늘 찍기", "3일 안에 찍기", "데이터 확인 후"}
    assert first["content_angle"] in {"경고형", "판단형", "기회형", "구조해설형"}
    assert first["representative_articles"]
    assert first["related_youtube"]
    assert first["related_youtube"][0]["views"] >= first["related_youtube"][-1]["views"]
    assert first["selection_titles"]
    assert any("리치고" in signal for signal in first["richgo_data_signals"])
    assert "왜 지금 찍어야" in first["why_now"]


def test_trends_period_controls_naver_and_fallback_timeline(monkeypatch):
    snap = TrendSnapshot(
        youtube=[{"title": "금리 대출 아파트", "published": "1일 전", "source": "youtube_fallback"}],
        news=[{"title": "금리 대출 아파트", "pub": _pub(1), "source": "경제신문", "provider": "google", "query": "금리"}],
        community=[],
        internal=[],
    )
    requested_days: list[int] = []

    def fake_fetch_search_trend(keywords, days=30):
        requested_days.append(days)
        return []

    monkeypatch.setattr(trends_route, "scan", lambda: snap)
    monkeypatch.setattr(trends_route, "fetch_all_benchmarks", lambda: [])
    monkeypatch.setattr(trends_route, "fetch_search_trend", fake_fetch_search_trend)

    result = trends_route.trends_scan(period="7d")

    assert requested_days == [7]
    assert len(result["charts"]["top3_timeline"]) == 7
    assert result["source_sections"][2]["basis_value"] != "데이터 없음"


def test_fetch_news_keeps_google_rss_when_naver_credentials_exist(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "items": [
                    {
                        "title": "서울 아파트 금리 뉴스",
                        "originallink": "https://naver.example/news",
                        "description": "대출 금리 기사",
                        "pubDate": _pub(0),
                    }
                ]
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, *args, **kwargs):
            return FakeResponse()

    fake_feed = SimpleNamespace(
        entries=[
            SimpleNamespace(
                title="구글 부동산 금리 이슈 - 경제신문",
                link="https://news.google.com/rss/articles/google-1",
                published=_pub(0),
                source={"title": "경제신문"},
            )
        ]
    )

    monkeypatch.setattr(trend_scanner.settings, "naver_client_id", "naver-id")
    monkeypatch.setattr(trend_scanner.settings, "naver_client_secret", "naver-secret")
    monkeypatch.setattr(trend_scanner.httpx, "Client", FakeClient)
    monkeypatch.setattr(trend_scanner.feedparser, "parse", lambda *args, **kwargs: fake_feed)

    result = trend_scanner.fetch_news()
    providers = {item.get("provider") for item in result}

    assert "naver" in providers
    assert "google" in providers
