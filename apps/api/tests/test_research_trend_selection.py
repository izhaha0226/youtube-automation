from sqlmodel import SQLModel, create_engine

from app.models import ArticleRecord, ResearchSession, VideoReferenceRecord
from app.modules.research import service


def test_create_from_trend_selection_uses_selected_article_keywords_for_youtube(monkeypatch):
    monkeypatch.setattr(service, "_persist_session", lambda mode, category, source: "sess-trend")
    captured = {}

    def fake_replace(session_id, articles, videos):
        captured["session_id"] = session_id
        captured["articles"] = articles
        captured["videos"] = videos

    monkeypatch.setattr(service, "_replace_candidates", fake_replace)
    monkeypatch.setattr(service, "fetch_youtube_trending", lambda: [
        {"video_id": "v1", "title": "서울 집값 반등 분석", "channel": "A", "url": "https://youtu.be/v1", "views": 200000, "published": "1일 전", "creative_analysis": {"score": 8}},
        {"video_id": "v2", "title": "요리 브이로그", "channel": "B", "url": "https://youtu.be/v2", "views": 900000, "published": "1일 전"},
    ])

    result = service.create_from_trend_selection(
        selected_articles=["서울 집값 반등, 지금 사도 되나", "금리 인하 기대와 부동산"],
        trend_keywords=["서울", "집값", "금리"],
        category="부동산",
    )

    assert result.session_id == "sess-trend"
    assert result.mode == "trend"
    assert result.source.title == "선택 뉴스 기반 유튜브 분석"
    assert [a.title for a in result.articles] == ["서울 집값 반등, 지금 사도 되나", "금리 인하 기대와 부동산"]
    assert result.videos[0].title == "서울 집값 반등 분석"
    assert result.videos[0].creative_analysis == {"score": 8}
    assert captured["session_id"] == "sess-trend"


def test_expand_session_reuses_existing_news_without_fetching_news(monkeypatch, tmp_path):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'research.db'}")
    SQLModel.metadata.create_all(test_engine)
    monkeypatch.setattr(service, "engine", test_engine)

    session_id = "sess-reuse"
    with service.Session(test_engine) as s:
        s.add(
            ResearchSession(
                id=session_id,
                mode="trend",
                category="부동산",
                source_title="선택 뉴스 기반 유튜브 분석",
                source_keywords=["서울", "집값"],
            )
        )
        s.add(
            ArticleRecord(
                id="article-1",
                session_id=session_id,
                title="처음 스캔에서 확인한 서울 집값 뉴스",
                source="구글",
                url="https://news.example/a1",
                keywords=["서울", "집값"],
                related_score=1.0,
            )
        )
        s.add(
            VideoReferenceRecord(
                id="video-1",
                session_id=session_id,
                youtube_video_id="v1",
                title="기존 벤치마크 영상",
                channel="A",
                url="https://youtu.be/v1",
                views=100,
                relevance_score=1.0,
            )
        )
        s.commit()

    def fail_fetch_news():
        raise AssertionError("뉴스는 첫 스캔 결과를 재사용해야 하며 재검색하면 안 됩니다.")

    monkeypatch.setattr(service, "fetch_news", fail_fetch_news)
    monkeypatch.setattr(
        service,
        "fetch_youtube_trending",
        lambda: [
            {"video_id": "v2", "title": "서울 집값 후속 분석", "channel": "B", "url": "https://youtu.be/v2", "views": 200000, "published": "1일 전"}
        ],
    )

    result = service.expand_session(session_id, article_ids=["article-1"], video_ids=["video-1"])

    assert [article.title for article in result.articles] == ["처음 스캔에서 확인한 서울 집값 뉴스"]
    assert result.articles[0].selected is True
    assert result.videos[0].id == "video-1"
    assert result.videos[0].selected is True
    assert any(video.youtube_video_id == "v2" for video in result.videos)
