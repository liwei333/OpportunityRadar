"""Mock platform adapter for V0 development.

Returns pre-defined candidate data without any real network calls.
This adapter validates the full pipeline while Technical Spike 001
develops the real DouyinWebAdapter.
"""

from datetime import UTC, datetime, timedelta

from ...domain.opportunity.models import AccountCandidate, ContentCandidate
from .mock_data import get_mock_candidates


class MockPlatformAdapter:
    """Mock adapter that returns the embedded candidate dataset."""

    platform_name: str = "douyin"

    def __init__(self) -> None:
        self._candidates = get_mock_candidates()
        self._content_cache: dict[str, list[ContentCandidate]] = {}

    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[ContentCandidate]:
        """Return mock content candidates filtered by query relevance.

        In V0, all candidates are returned for any query (with source_query set).
        The real adapter will filter by actual search results.
        """
        results: list[ContentCandidate] = []
        for candidate in self._candidates[:limit]:
            content = ContentCandidate(
                platform=self.platform_name,
                account_id=candidate.id,
                account_name=candidate.account_name,
                content_url=candidate.profile_url,
                title=candidate.account_name,
                description=candidate.bio,
                published_at=datetime.now(UTC) - timedelta(days=7),
                engagement={"followers": candidate.follower_count or 0},
                source_query=query,
                raw_data=candidate.raw_data,
            )
            results.append(content)
        return results

    async def get_account(
        self,
        account_ref: str,
    ) -> AccountCandidate:
        """Look up a mock account by profile URL or ID."""
        for candidate in self._candidates:
            if candidate.profile_url == account_ref or candidate.id == account_ref:
                return candidate
        # Return a default if not found
        return AccountCandidate(
            platform=self.platform_name,
            account_name="Unknown",
            profile_url=account_ref,
            raw_data={},
        )

    async def get_content(
        self,
        content_ref: str,
    ) -> ContentCandidate:
        """Return mock content for a given reference."""
        return ContentCandidate(
            platform=self.platform_name,
            content_url=content_ref,
            title="Mock Content",
            raw_data={},
        )
