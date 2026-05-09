from app.modules.trend import benchmark


def test_fetch_channel_top_videos_uses_channel_fallback_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(benchmark.settings, "google_api_key", None)
    monkeypatch.setattr(benchmark.settings, "youtube_api_key", None)

    def fake_channel_fallback(channel_id: str, channel_name: str, max_results: int = 10):
        return [
            {
                "video_id": "abc123xyz00",
                "title": "부동산 위기 신호",
                "channel": channel_name,
                "published": "1일 전",
                "views": 30000,
                "likes": 0,
                "comments": 0,
                "url": "https://youtube.com/watch?v=abc123xyz00",
                "source": "youtube_fallback",
                "creative_analysis": {"hook_type": "warning", "patterns": ["risk_warning"], "score": 3},
            }
        ]

    monkeypatch.setattr(benchmark, "fetch_youtube_channel_fallback", fake_channel_fallback)

    items = benchmark.fetch_channel_top_videos("UCxxx", "리치고", max_results=1)

    assert len(items) == 1
    assert items[0]["channel"] == "리치고"
    assert items[0]["source"] == "youtube_fallback"
    assert items[0]["creative_analysis"]["hook_type"] == "warning"
