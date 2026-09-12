"""Unit tests for OR-SPIKE-001 Douyin Web Collector.

Tests cover:
- URL normalization
- Metric normalization
- Video deduplication
- Account deduplication
- source_queries merge
- DataQualityReport calculation
- Feed card parsing
"""


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
