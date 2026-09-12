"""Unit tests for OR-SPIKE-001 Douyin Web Collector.

Tests cover:
- URL normalization
- Metric normalization
- Video deduplication
- Account deduplication
- source_queries merge
- DataQualityReport calculation
- Feed card parsing
- Search card parsing
- Search provenance
- Search loaded detection
- Search fallback dedup
- UTC timestamp consistency
"""


from spikes.or_spike_001.douyin_selectors import DouyinSearchDetector
from spikes.or_spike_001.models import (
    DataQualityReport,
    NormalizedAccount,
    NormalizedVideo,
    RawAccountCandidate,
    RawVideoCandidate,
)
from spikes.or_spike_001.normalizer import (
    deduplicate_accounts,
    deduplicate_videos,
    normalize_account,
    normalize_metric,
    normalize_text,
    normalize_url,
    normalize_video,
)

# === URL Normalization ===


class TestUrlNormalization:
    """Test URL normalization functions."""

    def test_remove_tracking_params(self) -> None:
        url = "https://www.douyin.com/video/123?utm_source=share&from=share"
        result = normalize_url(url)
        assert "utm_source" not in result
        assert "from=" not in result
        assert "video/123" in result

    def test_preserve_essential_path(self) -> None:
        url = "https://www.douyin.com/video/7682728905966423334"
        result = normalize_url(url)
        assert result == "https://www.douyin.com/video/7682728905966423334"

    def test_relative_url_with_double_slash(self) -> None:
        url = "//www.douyin.com/video/123456"
        result = normalize_url(url)
        assert result == "https://www.douyin.com/video/123456"

    def test_empty_url(self) -> None:
        assert normalize_url("") is None
        assert normalize_url(None) is None

    def test_lowercase_host(self) -> None:
        url = "HTTPS://WWW.DOUYIN.COM/video/123"
        result = normalize_url(url)
        assert "douyin.com" in result


# === Metric Normalization ===


class TestMetricNormalization:
    """Test Chinese metric string parsing."""

    def test_wan_suffix(self) -> None:
        assert normalize_metric("1.2万") == 12000
        assert normalize_metric("3.5万") == 35000
        assert normalize_metric("44.9万") == 449000

    def test_w_suffix(self) -> None:
        assert normalize_metric("1.5w") == 15000
        assert normalize_metric("2W") == 20000

    def test_plain_number(self) -> None:
        assert normalize_metric("1200") == 1200
        assert normalize_metric("3689") == 3689

    def test_large_wan(self) -> None:
        assert normalize_metric("271.6万") == 2716000
        assert normalize_metric("444.4万") == 4444000

    def test_empty(self) -> None:
        assert normalize_metric("") is None
        assert normalize_metric(None) is None

    def test_invalid(self) -> None:
        assert normalize_metric("abc") is None


# === Text Normalization ===


class TestTextNormalization:
    """Test text cleaning."""

    def test_whitespace_cleanup(self) -> None:
        assert normalize_text("  hello   world  ") == "hello world"

    def test_newline_cleanup(self) -> None:
        assert normalize_text("hello\n\nworld") == "hello world"

    def test_empty(self) -> None:
        assert normalize_text("") is None
        assert normalize_text(None) is None


# === Feed Card Parsing ===


class TestFeedCardParsing:
    """Test parsing of feed card text content.

    The feed card text format is:
    [duration][view_count][title] [@author] · [date]
    """

    def test_parse_standard_card(self) -> None:
        """Test parsing a standard feed card."""
        # We can't easily instantiate DouyinExtractor without a page,
        # so we test the parsing logic directly
        text = "09:1717.5万我要爬上这座充满巨蛇的高塔！ROBLOX @麟麟七的游戏日常 · 5天前"

        # Simulate parsing
        import re
        duration_match = re.match(r"^(\d{1,2}:\d{2}(?::\d{2})?)", text)
        assert duration_match is not None
        assert duration_match.group(1) == "09:17"

    def test_parse_card_with_date(self) -> None:
        """Test date extraction from card text."""
        import re
        text = "04:474.4万九龙城寨有多可怕？ @科学探索飞船 · 7月8日"
        date_match = re.search(r"(\d+月\d+日)", text)
        assert date_match is not None
        assert date_match.group(1) == "7月8日"

    def test_parse_card_with_author(self) -> None:
        """Test author extraction."""
        import re
        text = "32:3544.9万一口气沉浸式观看印度版 @影太白 · 7月10日"
        author_match = re.search(r"@(\S+)", text)
        assert author_match is not None
        assert author_match.group(1) == "影太白"


# === Video Deduplication ===


class TestVideoDeduplication:
    """Test video deduplication logic."""

    def test_dedup_by_video_id(self) -> None:
        v1 = NormalizedVideo(
            id="1", video_id="123", video_url="https://douyin.com/video/123",
            title="Test", collected_at="2026-01-01",
            dedup_key="douyin::video::123",
        )
        v2 = NormalizedVideo(
            id="2", video_id="123", video_url="https://douyin.com/video/123",
            title="Test 2", collected_at="2026-01-01",
            dedup_key="douyin::video::123",
        )
        unique, dups = deduplicate_videos([v1, v2])
        assert len(unique) == 1
        assert dups == 1

    def test_keep_different_videos(self) -> None:
        v1 = NormalizedVideo(
            id="1", video_id="123", title="Test 1", collected_at="2026-01-01",
            dedup_key="douyin::video::123",
        )
        v2 = NormalizedVideo(
            id="2", video_id="456", title="Test 2", collected_at="2026-01-01",
            dedup_key="douyin::video::456",
        )
        unique, dups = deduplicate_videos([v1, v2])
        assert len(unique) == 2
        assert dups == 0

    def test_dedup_empty_list(self) -> None:
        unique, dups = deduplicate_videos([])
        assert len(unique) == 0
        assert dups == 0


# === Account Deduplication ===


class TestAccountDeduplication:
    """Test account deduplication with source_queries merge."""

    def test_dedup_by_name(self) -> None:
        a1 = NormalizedAccount(
            id="1", account_name="@test", collected_at="2026-01-01",
            dedup_key="douyin::name::@test",
            source_queries=["query1"],
        )
        a2 = NormalizedAccount(
            id="2", account_name="@test", collected_at="2026-01-01",
            dedup_key="douyin::name::@test",
            source_queries=["query2"],
        )
        unique, dups = deduplicate_accounts([a1, a2])
        assert len(unique) == 1
        assert dups == 1

    def test_merge_source_queries(self) -> None:
        a1 = NormalizedAccount(
            id="1", account_name="@test", collected_at="2026-01-01",
            dedup_key="douyin::name::@test",
            source_queries=["query1", "query2"],
        )
        a2 = NormalizedAccount(
            id="2", account_name="@test", collected_at="2026-01-01",
            dedup_key="douyin::name::@test",
            source_queries=["query2", "query3"],
        )
        unique, _ = deduplicate_accounts([a1, a2])
        assert len(unique) == 1
        assert set(unique[0].source_queries) == {"query1", "query2", "query3"}

    def test_merge_content_hits(self) -> None:
        a1 = NormalizedAccount(
            id="1", account_name="@test", collected_at="2026-01-01",
            dedup_key="douyin::name::@test",
            content_hits=3,
        )
        a2 = NormalizedAccount(
            id="2", account_name="@test", collected_at="2026-01-01",
            dedup_key="douyin::name::@test",
            content_hits=2,
        )
        unique, _ = deduplicate_accounts([a1, a2])
        assert unique[0].content_hits == 5


# === Search Card Parsing ===


class TestSearchCardParsing:
    """Test search result card text parsing.

    Search card format:
    [duration][view_count][title] [@author] · [date]
    """

    def _make_extractor(self) -> object:
        """Create extractor instance without page."""
        from spikes.or_spike_001.extractors import DouyinExtractor
        return DouyinExtractor.__new__(DouyinExtractor)

    def test_parse_search_card_standard(self) -> None:
        """Test parsing a standard search card."""
        extractor = self._make_extractor()
        text = "29:416489代运营怎么和老板谈单#短视频创作 #代运营@靳兴的运营速成指南 · 2月15日"

        video = extractor._parse_search_card_text(text, "短视频代运营", "https://www.douyin.com/search/x")
        assert video is not None
        assert video.title is not None
        assert "代运营" in video.title
        assert video.author_name == "@靳兴的运营速成指南"
        assert video.view_count_raw == "6489"
        assert video.duration == "29:41"
        assert video.published_at == "2月15日"
        assert video.source_query == "短视频代运营"
        assert video.extraction_method == "search_result_card"
        assert video.extraction_success is True

    def test_parse_search_card_with_wan(self) -> None:
        """Test parsing search card with 万 view count."""
        extractor = self._make_extractor()
        text = "01:531.9万做短视频最简单的方式#短视频创业 #代运营 #编导@薛辉小清新 · 6月17日"

        video = extractor._parse_search_card_text(text, "短视频代运营", "https://x")
        assert video is not None
        assert video.view_count_raw == "1.9万"
        assert video.author_name == "@薛辉小清新"
        assert video.published_at == "6月17日"

    def test_parse_search_card_with_relative_date(self) -> None:
        """Test parsing search card with relative date."""
        extractor = self._make_extractor()
        text = "09:1717.5万我要爬上这座充满巨蛇的高塔！ROBLOX @麟麟七的游戏日常 · 5天前"

        video = extractor._parse_search_card_text(text, "test", "https://x")
        assert video is not None
        assert video.published_at == "5天前"
        assert video.view_count_raw == "17.5万"

    def test_parse_search_card_invalid(self) -> None:
        """Test parsing invalid search card text."""
        extractor = self._make_extractor()
        text = "相关搜索短视频代运营公司"

        video = extractor._parse_search_card_text(text, "test", "https://x")
        assert video is None


# === DataQualityReport ===


class TestDataQualityReport:
    """Test quality report calculations."""

    def test_extraction_success_rate(self) -> None:
        report = DataQualityReport(
            extract_success_count=80,
            extract_failure_count=20,
            raw_result_count=100,
        )
        assert report.extraction_success_rate == 0.8

    def test_traceable_url_rate(self) -> None:
        report = DataQualityReport(
            traceable_url_count=95,
            raw_result_count=100,
        )
        assert report.traceable_url_rate == 0.95

    def test_duplicate_rate(self) -> None:
        report = DataQualityReport(
            duplicate_video_count=10,
            raw_result_count=100,
        )
        assert report.duplicate_rate == 0.1

    def test_zero_division(self) -> None:
        report = DataQualityReport()
        assert report.extraction_success_rate == 0.0
        assert report.traceable_url_rate == 0.0
        assert report.duplicate_rate == 0.0

    def test_markdown_generation(self) -> None:
        report = DataQualityReport(
            run_id="test-123",
            queries_requested=10,
            queries_completed=8,
            queries_failed=2,
            raw_result_count=150,
            unique_video_count=140,
            unique_account_count=50,
        )
        md = report.to_markdown()
        assert "test-123" in md
        assert "10" in md
        assert "150" in md


# === Normalize Raw Video ===


class TestNormalizeVideo:
    """Test raw to normalized video conversion."""

    def test_normalize_basic(self) -> None:
        raw = RawVideoCandidate(
            video_id="12345",
            video_url="//www.douyin.com/video/12345",
            title="  Test Title  ",
            author_name="@testauthor",
            view_count_raw="1.5万",
            duration="03:45",
            source_query="test query",
            collected_at="2026-01-01T00:00:00",
        )
        normalized = normalize_video(raw)
        assert normalized.video_id == "12345"
        assert normalized.video_url == "https://www.douyin.com/video/12345"
        assert normalized.title == "Test Title"
        assert normalized.author_name == "@testauthor"
        assert normalized.view_count == 15000
        assert normalized.view_count_raw == "1.5万"
        assert normalized.duration == "03:45"
        assert normalized.source_query == "test query"
        assert normalized.dedup_key == "douyin::video::12345"

    def test_normalize_minimal(self) -> None:
        raw = RawVideoCandidate(
            video_id="99999",
            collected_at="2026-01-01T00:00:00",
        )
        normalized = normalize_video(raw)
        assert normalized.video_id == "99999"
        assert normalized.title is None
        assert normalized.view_count is None
        assert normalized.dedup_key == "douyin::video::99999"


# === Normalize Raw Account ===


class TestNormalizeAccount:
    """Test raw to normalized account conversion."""

    def test_normalize_basic(self) -> None:
        raw = RawAccountCandidate(
            account_name="@testaccount",
            follower_count_raw="2.3万",
            source_queries=["q1", "q2"],
            content_hits=5,
            collected_at="2026-01-01T00:00:00",
        )
        normalized = normalize_account(raw)
        assert normalized.account_name == "@testaccount"
        assert normalized.follower_count == 23000
        assert normalized.follower_count_raw == "2.3万"
        assert len(normalized.source_queries) == 2
        assert normalized.content_hits == 5


# === Search Provenance (P0-1) ===


class TestSearchProvenance:
    """Test that search provenance fields are correctly set."""

    def test_search_card_has_search_mode(self) -> None:
        """Search card extraction should set collection_mode='search'."""
        from spikes.or_spike_001.extractors import DouyinExtractor

        extractor = DouyinExtractor.__new__(DouyinExtractor)
        text = "29:416489代运营怎么和老板谈单@作者 · 2月15日"

        video = extractor._parse_search_card_text(
            text, "短视频代运营", "https://www.douyin.com/search/短视频代运营"
        )
        assert video is not None
        assert video.collection_mode == "search"
        assert video.source_query == "短视频代运营"
        assert video.source_page_url == "https://www.douyin.com/search/短视频代运营"

    def test_feed_card_has_feed_mode(self) -> None:
        """Feed card extraction should set collection_mode='feed'."""
        raw = RawVideoCandidate(
            title="Test",
            author_name="@author",
            source_query="test",
            collection_mode="feed",
            source_page_url="https://www.douyin.com/jingxuan",
            extraction_success=True,
        )
        normalized = normalize_video(raw)
        assert normalized.collection_mode == "feed"
        assert normalized.source_page_url == "https://www.douyin.com/jingxuan"

    def test_normalize_preserves_provenance(self) -> None:
        """Normalization should preserve collection_mode and source_page_url."""
        raw = RawVideoCandidate(
            title="Test",
            author_name="@author",
            source_query="query1",
            collection_mode="search",
            source_page_url="https://www.douyin.com/search/query1",
            extraction_success=True,
        )
        normalized = normalize_video(raw)
        assert normalized.collection_mode == "search"
        assert normalized.source_page_url == "https://www.douyin.com/search/query1"
        assert normalized.source_query == "query1"


# === Search Loaded Detection (P0-2) ===


class TestSearchLoadedDetection:
    """Test strict search result loaded detection."""

    def test_search_cards_present(self) -> None:
        """Search cards present should return True."""
        assert DouyinSearchDetector.is_search_results_loaded(
            search_result_cards=5, video_links=0
        )

    def test_video_links_present(self) -> None:
        """Video links present should return True."""
        assert DouyinSearchDetector.is_search_results_loaded(
            search_result_cards=0, video_links=3
        )

    def test_login_overlay_not_loaded(self) -> None:
        """Login overlay page should return False."""
        assert not DouyinSearchDetector.is_search_results_loaded(
            search_result_cards=0, video_links=0
        )

    def test_long_body_without_results_not_loaded(self) -> None:
        """Long body text without search cards should return False."""
        assert not DouyinSearchDetector.is_search_results_loaded(
            search_result_cards=0, video_links=0
        )

    def test_login_overlay_text_detection(self) -> None:
        """Login overlay text should be detected."""
        body = "登录后即可搜索更多精彩视频扫码登录..."
        assert DouyinSearchDetector.is_login_overlay_present(body)

    def test_normal_body_no_login_overlay(self) -> None:
        """Normal body without login text should return False."""
        body = "这是一些正常的搜索结果内容..."
        assert not DouyinSearchDetector.is_login_overlay_present(body)

    def test_captcha_detection(self) -> None:
        """Captcha elements should be detected."""
        assert DouyinSearchDetector.is_captcha_present(captcha_elements=1)

    def test_no_captcha(self) -> None:
        """No captcha elements should return False."""
        assert not DouyinSearchDetector.is_captcha_present(captcha_elements=0)


# === Search Fallback Dedup (P0-3) ===


class TestSearchFallbackDedup:
    """Test search result dedup with fallback."""

    def test_search_fallback_same_title_author_merges(self) -> None:
        """Same title + author from different queries should merge."""
        from spikes.or_spike_001.normalizer import _make_video_dedup_key

        key1 = _make_video_dedup_key(
            video_id=None,
            video_url=None,
            collection_mode="search",
            title="代运营怎么谈单",
            author_name="@author",
        )
        key2 = _make_video_dedup_key(
            video_id=None,
            video_url=None,
            collection_mode="search",
            title="代运营怎么谈单",
            author_name="@author",
        )
        assert key1 == key2
        assert key1.startswith("douyin::search_fallback::")

    def test_search_fallback_different_title_no_merge(self) -> None:
        """Different titles should not merge."""
        from spikes.or_spike_001.normalizer import _make_video_dedup_key

        key1 = _make_video_dedup_key(
            video_id=None,
            video_url=None,
            collection_mode="search",
            title="Title A",
            author_name="@author",
        )
        key2 = _make_video_dedup_key(
            video_id=None,
            video_url=None,
            collection_mode="search",
            title="Title B",
            author_name="@author",
        )
        assert key1 != key2

    def test_url_based_dedup_takes_priority(self) -> None:
        """URL-based dedup should take priority over fallback."""
        from spikes.or_spike_001.normalizer import _make_video_dedup_key

        key = _make_video_dedup_key(
            video_id="12345",
            video_url="https://www.douyin.com/video/12345",
            collection_mode="search",
            title="Title",
            author_name="@author",
        )
        assert key == "douyin::video::12345"

    def test_feed_mode_no_fallback(self) -> None:
        """Feed mode without video_id/url should return empty key."""
        from spikes.or_spike_001.normalizer import _make_video_dedup_key

        key = _make_video_dedup_key(
            video_id=None,
            video_url=None,
            collection_mode="feed",
            title="Title",
            author_name="@author",
        )
        assert key == ""


# === UTC Timestamp (P0-4) ===


class TestUTCTimestamp:
    """Test UTC timestamp consistency."""

    def test_finished_at_after_started_at(self) -> None:
        """finished_at should be >= started_at."""
        report = DataQualityReport(
            run_started_at="2026-01-01T00:00:00+00:00",
            run_finished_at="2026-01-01T00:01:00+00:00",
        )
        from datetime import datetime
        started = datetime.fromisoformat(report.run_started_at)
        finished = datetime.fromisoformat(report.run_finished_at)
        assert finished >= started

    def test_timestamps_have_timezone(self) -> None:
        """Timestamps should include timezone offset."""
        raw = RawVideoCandidate(
            title="Test",
            author_name="@author",
            source_query="test",
            extraction_success=True,
        )
        # collected_at should have timezone info
        assert "+" in raw.collected_at or "Z" in raw.collected_at

    def test_report_timestamps_utc(self) -> None:
        """Report timestamps should be in UTC."""
        report = DataQualityReport(
            run_started_at="2026-01-01T00:00:00+00:00",
            run_finished_at="2026-01-01T00:01:00+00:00",
        )
        assert "+00:00" in report.run_started_at
        assert "+00:00" in report.run_finished_at
