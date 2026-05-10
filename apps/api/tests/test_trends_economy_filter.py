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
