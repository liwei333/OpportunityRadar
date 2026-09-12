"""Unit tests for deduplication services."""


from app.application.normalizer import AccountDeduplicator, ContentDeduplicator
from app.domain.opportunity.models import AccountCandidate, ContentCandidate


class TestAccountDeduplicator:
    """Tests for account deduplication."""

    def test_deduplicates_by_profile_url(self) -> None:
        """Accounts with same platform + profile_url should be deduplicated."""
        candidates = [
            AccountCandidate(
                platform="douyin",
                account_name="星火短视频",
                profile_url="https://www.douyin.com/user/123",
                bio="First",
                source_queries=["query1"],
            ),
            AccountCandidate(
                platform="douyin",
                account_name="星火短视频",
                profile_url="https://www.douyin.com/user/123?utm_source=x",
                bio="",
                source_queries=["query2"],
            ),
        ]
        result = AccountDeduplicator.deduplicate(candidates)
        assert len(result) == 1

    def test_merges_source_queries(self) -> None:
        """Deduplication should merge source_queries from duplicates."""
        candidates = [
            AccountCandidate(
                platform="douyin",
                account_name="星火短视频",
                profile_url="https://www.douyin.com/user/123",
                source_queries=["企业短视频获客"],
            ),
            AccountCandidate(
                platform="douyin",
                account_name="星火短视频",
                profile_url="https://www.douyin.com/user/123?from=share",
                source_queries=["短视频代运营"],
            ),
        ]
        result = AccountDeduplicator.deduplicate(candidates)
        assert len(result) == 1
        assert "企业短视频获客" in result[0].source_queries
        assert "短视频代运营" in result[0].source_queries

    def test_keeps_separate_urls(self) -> None:
        """Different profile URLs should remain separate."""
        candidates = [
            AccountCandidate(
                platform="douyin",
                account_name="Account A",
                profile_url="https://www.douyin.com/user/111",
            ),
            AccountCandidate(
                platform="douyin",
                account_name="Account B",
                profile_url="https://www.douyin.com/user/222",
            ),
        ]
        result = AccountDeduplicator.deduplicate(candidates)
        assert len(result) == 2

    def test_keeps_different_platforms(self) -> None:
        """Same URL on different platforms should remain separate."""
        candidates = [
            AccountCandidate(
                platform="douyin",
                account_name="Account A",
                profile_url="https://example.com/user/123",
            ),
            AccountCandidate(
                platform="kuaishou",
                account_name="Account A",
                profile_url="https://example.com/user/123",
            ),
        ]
        result = AccountDeduplicator.deduplicate(candidates)
        assert len(result) == 2


class TestContentDeduplicator:
    """Tests for content deduplication."""

    def test_deduplicates_by_content_url(self) -> None:
        """Content with same platform + URL should be deduplicated."""
        candidates = [
            ContentCandidate(
                platform="douyin",
                account_id="acc1",
                content_url="https://www.douyin.com/video/111",
            ),
            ContentCandidate(
                platform="douyin",
                account_id="acc1",
                content_url="https://www.douyin.com/video/111?utm_source=x",
            ),
        ]
        result = ContentDeduplicator.deduplicate(candidates)
        assert len(result) == 1

    def test_keeps_different_urls(self) -> None:
        """Different content URLs should remain separate."""
        candidates = [
            ContentCandidate(
                platform="douyin",
                content_url="https://www.douyin.com/video/111",
            ),
            ContentCandidate(
                platform="douyin",
                content_url="https://www.douyin.com/video/222",
            ),
        ]
        result = ContentDeduplicator.deduplicate(candidates)
        assert len(result) == 2
