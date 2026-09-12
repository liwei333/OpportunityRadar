"""Mock Collector — executes search queries and returns candidates.

V0 returns data from MockPlatformAdapter.
Future: real platform adapters (DouyinWebAdapter, etc.) will be injected.
"""

import logging

from ...adapters.platforms.mock import MockPlatformAdapter
from ...domain.opportunity.models import AccountCandidate, ContentCandidate
from ...domain.research.models import ResearchTask, SearchQuery

logger = logging.getLogger(__name__)


class MockCollector:
    """Collects candidate data by executing search queries.

    V0: uses MockPlatformAdapter exclusively.
    Future: injects real platform adapters based on configuration.
    """

    def __init__(self, adapter: MockPlatformAdapter | None = None) -> None:
        self._adapter = adapter or MockPlatformAdapter()

    async def collect(
        self,
        task: ResearchTask,
        queries: list[SearchQuery],
    ) -> tuple[list[AccountCandidate], list[ContentCandidate]]:
        """Execute all search queries and collect candidates.

        Args:
            task: The research task being executed.
            queries: List of search queries to execute.

        Returns:
            Tuple of (account_candidates, content_candidates).
        """
        all_accounts: dict[str, AccountCandidate] = {}
        all_content: list[ContentCandidate] = []

        for query in queries:
            logger.debug("Collecting for query: %s", query.query)
            try:
                content_results = await self._adapter.search(
                    query=query.query,
                    limit=30,
                )
                for content in content_results:
                    content.source_query = query.query
                    all_content.append(content)

                    # Derive account from content
                    if content.account_id:
                        if content.account_id not in all_accounts:
                            account = await self._adapter.get_account(
                                content.account_id
                            )
                            account.source_queries = [query.query]
                            all_accounts[content.account_id] = account
                        else:
                            existing = all_accounts[content.account_id]
                            if query.query not in existing.source_queries:
                                existing.source_queries.append(query.query)

                query.status = "COMPLETED"
            except Exception as e:
                logger.warning("Query failed: %s — %s", query.query, e)
                query.status = "FAILED"

        accounts = list(all_accounts.values())
        logger.info(
            "Collected %d accounts and %d content items from %d queries",
            len(accounts),
            len(all_content),
            len(queries),
        )
        return accounts, all_content
