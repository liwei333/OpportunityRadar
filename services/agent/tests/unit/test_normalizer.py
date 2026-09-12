"""Unit tests for URL normalizer and data cleaner."""


from app.application.normalizer import DataCleaner, URLNormalizer


class TestURLNormalizer:
    """Tests for URL normalization."""

    def test_remove_utm_params(self) -> None:
        """UTM tracking parameters should be removed."""
        url = "https://example.com/video?utm_source=google&utm_medium=cpc&id=123"
        result = URLNormalizer.normalize(url)
        assert "utm_source" not in result
        assert "utm_medium" not in result
        assert "id=123" in result

    def test_remove_noise_params(self) -> None:
        """Common tracking/noise parameters should be removed."""
        url = "https://www.douyin.com/video/123?from=share&share_app_id=1128"
        result = URLNormalizer.normalize(url)
        assert "from=" not in result
        assert "share_app_id=" not in result

    def test_preserve_essential_params(self) -> None:
        """Essential parameters should be preserved."""
        url = "https://example.com/page?category=tech&sort=newest"
        result = URLNormalizer.normalize(url)
        assert "category=tech" in result
        assert "sort=newest" in result

    def test_lowercase_scheme_and_host(self) -> None:
        """Scheme and host should be lowercased."""
        url = "HTTPS://WWW.Example.COM/path"
        result = URLNormalizer.normalize(url)
        assert result.startswith("https://www.example.com")

    def test_remove_trailing_slash(self) -> None:
        """Trailing slash should be removed from path."""
        url = "https://example.com/path/"
        result = URLNormalizer.normalize(url)
        assert result == "https://example.com/path"

    def test_empty_url(self) -> None:
        """Empty URL should return empty string."""
        assert URLNormalizer.normalize("") == ""

    def test_get_dedup_key(self) -> None:
        """Dedup key should combine platform + normalized URL."""
        key = URLNormalizer.get_dedup_key("douyin", "https://www.douyin.com/user/123?utm_source=x")
        assert key.startswith("douyin::")
        assert "utm_source" not in key

    def test_same_url_same_key(self) -> None:
        """Same URL with different tracking params should produce same dedup key."""
        key1 = URLNormalizer.get_dedup_key("douyin", "https://www.douyin.com/user/123?utm_source=a")
        key2 = URLNormalizer.get_dedup_key("douyin", "https://www.douyin.com/user/123?utm_medium=b")
        assert key1 == key2


class TestDataCleaner:
    """Tests for data cleaning utilities."""

    def test_clean_text_removes_extra_whitespace(self) -> None:
        """Multiple spaces and newlines should be collapsed."""
        text = "Hello   world\n\n  test"
        result = DataCleaner.clean_text(text)
        assert result == "Hello world test"

    def test_clean_text_strips(self) -> None:
        """Leading/trailing whitespace should be removed."""
        text = "  hello world  "
        result = DataCleaner.clean_text(text)
        assert result == "hello world"

    def test_clean_text_empty(self) -> None:
        """Empty text should return empty string."""
        assert DataCleaner.clean_text("") == ""

    def test_clean_account_name(self) -> None:
        """Account names should be cleaned."""
        name = "  星火  短视频  \n 获客  "
        result = DataCleaner.clean_account_name(name)
        assert result == "星火 短视频 获客"

    def test_clean_engagement_numeric_strings(self) -> None:
        """Numeric strings should be parsed to numbers."""
        engagement = {"likes": "1,234", "shares": "56.7", "invalid": "abc"}
        result = DataCleaner.clean_engagement(engagement)
        assert result["likes"] == 1234
        assert result["shares"] == 56.7
        assert "invalid" not in result
