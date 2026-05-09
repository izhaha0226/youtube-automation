from app.modules.trend import scanner


def test_fetch_youtube_trending_uses_fallback_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(scanner.settings, "google_api_key", None)
    monkeypatch.setattr(scanner.settings, "youtube_api_key", None)
    monkeypatch.setattr(scanner, "ECON_QUERIES", ["부동산", "금리"])

    def fake_fallback(query: str, max_results: int = 10):
        return [
            {
                "title": f"{query} 경고 신호",
                "channel": "리치고",
                "query": query,
                "video_id": f"vid-{query}",
                "url": f"https://youtube.com/watch?v=vid-{query}",
                "views": 10,
                "likes": 0,
                "source": "youtube_fallback",
                "creative_analysis": {"hook_type": "warning", "patterns": ["risk_warning"], "score": 3},
            }
        ]

    monkeypatch.setattr(scanner, "fetch_youtube_search_fallback", fake_fallback)

    items = scanner.fetch_youtube_trending()

    assert [item["query"] for item in items] == ["부동산", "금리"]
    assert all(item["source"] == "youtube_fallback" for item in items)
    assert items[0]["creative_analysis"]["hook_type"] == "warning"
