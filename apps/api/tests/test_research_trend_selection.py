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
