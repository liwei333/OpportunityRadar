"""Douyin Web Adapter — STUB for Technical Spike 001.

This module reserves the interface for the real Douyin browser collector.
DO NOT implement actual scraping logic here during V0.

The real implementation will:
1. Use PlaywrightBrowserWorker to open douyin.com
2. Execute search queries
3. Scroll and extract video/account data
4. Return structured ContentCandidate and AccountCandidate objects

Until Technical Spike 001 validates the browser approach, this stub
raises NotImplementedError for all methods.
"""

from ...domain.opportunity.models import AccountCandidate, ContentCandidate


class DouyinWebAdapter:
    """Stub adapter for Douyin Web collection.

    WARNING: This is a V0 placeholder. Real implementation requires
    Technical Spike 001 to validate browser automation feasibility.
    """

    platform_name: str = "douyin"

    def __init__(self, browser_worker=None) -> None:
        self._browser = browser_worker

    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[ContentCandidate]:
        """Search Douyin for content matching the query.

        Raises:
            NotImplementedError: Always, until Spike 001 is complete.
        """
        raise NotImplementedError(
            "DouyinWebAdapter.search() requires Technical Spike 001. "
            "Use MockPlatformAdapter for V0 development."
        )

    async def get_account(
        self,
        account_ref: str,
    ) -> AccountCandidate:
        """Retrieve Douyin account details.

        Raises:
            NotImplementedError: Always, until Spike 001 is complete.
        """
        raise NotImplementedError(
            "DouyinWebAdapter.get_account() requires Technical Spike 001. "
            "Use MockPlatformAdapter for V0 development."
        )

    async def get_content(
        self,
        content_ref: str,
    ) -> ContentCandidate:
        """Retrieve Douyin content details.

        Raises:
            NotImplementedError: Always, until Spike 001 is complete.
        """
        raise NotImplementedError(
            "DouyinWebAdapter.get_content() requires Technical Spike 001. "
            "Use MockPlatformAdapter for V0 development."
        )
