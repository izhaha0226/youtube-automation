from app.modules.trend.youtube_fallback import analyze_creative, parse_youtube_initial_data


def test_parse_youtube_initial_data_extracts_video_cards_and_analysis():
    html = '''
    <html><script>var ytInitialData = {"contents":{"twoColumnSearchResultsRenderer":{"primaryContents":{"sectionListRenderer":{"contents":[{"itemSectionRenderer":{"contents":[{"videoRenderer":{"videoId":"abc123xyz00","title":{"runs":[{"text":"집값 폭락 전 반드시 봐야 할 3가지 신호"}]},"ownerText":{"runs":[{"text":"리치고"}]},"publishedTimeText":{"simpleText":"1일 전"},"viewCountText":{"simpleText":"조회수 12만회"},"thumbnail":{"thumbnails":[{"url":"https://i.ytimg.com/vi/abc123xyz00/hqdefault.jpg"}]}}}]}}]}}}}};</script></html>
    '''

    items = parse_youtube_initial_data(html, query="부동산")

    assert len(items) == 1
    assert items[0]["video_id"] == "abc123xyz00"
    assert items[0]["title"] == "집값 폭락 전 반드시 봐야 할 3가지 신호"
    assert items[0]["channel"] == "리치고"
    assert items[0]["views"] == 120000
    assert items[0]["query"] == "부동산"
    assert items[0]["source"] == "youtube_fallback"
    assert items[0]["thumbnail_url"].startswith("https://i.ytimg.com")
    assert items[0]["creative_analysis"]["hook_type"] == "warning"
    assert "numbered" in items[0]["creative_analysis"]["patterns"]


def test_analyze_creative_classifies_title_patterns():
    analysis = analyze_creative("서울 아파트, 지금 사도 될까? 전문가가 공개한 체크리스트")

    assert analysis["hook_type"] == "question"
    assert "expert_authority" in analysis["patterns"]
    assert "checklist" in analysis["patterns"]
    assert analysis["score"] >= 3
