"""Platform adapter abstract interface.

This defines the contract that any platform adapter must implement.
Current implementations: MockPlatformAdapter.
Next phase: DouyinWebAdapter (requires Technical Spike 001).
"""

from typing import Protocol, runtime_checkable

from ...domain.opportunity.models import AccountCandidate, ContentCandidate


@runtime_checkable
class PlatformAdapter(Protocol):
    """Abstract interface for platform data collection.

    Implementations must provide search, account lookup, and content lookup.
    Platform-specific logic (selectors, anti-bot, scroll behavior) belongs
    in the adapter — never in the core business logic.
    """

    platform_name: str

    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[ContentCandidate]:
        """Search the platform and return content candidates.

        Args:
            query: Search keyword or phrase.
            limit: Maximum number of results to return.

        Returns:
            List of content candidates found for this query.
        """
        ...

    async def get_account(
        self,
        account_ref: str,
    ) -> AccountCandidate:
        """Retrieve account details by reference (URL, ID, or handle).

        Args:
            account_ref: Platform-specific account identifier.

        Returns:
            Populated account candidate.
        """
        ...

    async def get_content(
        self,
        content_ref: str,
    ) -> ContentCandidate:
        """Retrieve content details by reference (URL or ID).

        Args:
            content_ref: Platform-specific content identifier.

        Returns:
            Populated content candidate.
        """
        ...
