"""Deduplication services for accounts and content.

Uses Polars DataFrames for efficient batch deduplication.
Preserves source_queries as a list since multiple query hits
are a relevance signal for later scoring.
"""

from ...domain.opportunity.models import AccountCandidate, ContentCandidate
from .normalizer import URLNormalizer


class AccountDeduplicator:
    """Deduplicate account candidates by platform + profile_url.

    When duplicates are found, merges source_queries to preserve
    the multi-query-hit signal.
    """

    @staticmethod
    def deduplicate(candidates: list[AccountCandidate]) -> list[AccountCandidate]:
        """Deduplicate account candidates.

        Priority: platform + normalized profile_url.
        Merges source_queries when duplicates are found.

        Args:
            candidates: List of account candidates (may contain duplicates).

        Returns:
            Deduplicated list with merged source queries.
        """
        seen: dict[str, AccountCandidate] = {}

        for candidate in candidates:
            key = URLNormalizer.get_dedup_key(
                candidate.platform, candidate.profile_url
            )
            if key in seen:
                # Merge source queries
                existing = seen[key]
                existing_queries = set(existing.source_queries)
                new_queries = set(candidate.source_queries)
                merged = existing_queries | new_queries
                existing.source_queries = sorted(merged)
                # Keep the one with more complete data
                if not existing.bio and candidate.bio:
                    existing.bio = candidate.bio
                if not existing.follower_count and candidate.follower_count:
                    existing.follower_count = candidate.follower_count
            else:
                seen[key] = candidate.model_copy()

        return list(seen.values())

    @staticmethod
    def count_unique(candidates: list[AccountCandidate]) -> int:
        """Count unique accounts without full deduplication."""
        keys = set()
        for c in candidates:
            key = URLNormalizer.get_dedup_key(c.platform, c.profile_url)
            keys.add(key)
        return len(keys)


class ContentDeduplicator:
    """Deduplicate content candidates by platform + normalized content_url.

    Preserves source_query from the first occurrence.
    """

    @staticmethod
    def deduplicate(candidates: list[ContentCandidate]) -> list[ContentCandidate]:
        """Deduplicate content candidates.

        Priority: platform + normalized content_url.

        Args:
            candidates: List of content candidates.

        Returns:
            Deduplicated list.
        """
        seen: dict[str, ContentCandidate] = {}

        for candidate in candidates:
            key = URLNormalizer.get_dedup_key(
                candidate.platform, candidate.content_url
            )
            if key not in seen:
                seen[key] = candidate.model_copy()

        return list(seen.values())

    @staticmethod
    def count_unique(candidates: list[ContentCandidate]) -> int:
        """Count unique content items."""
        keys = set()
        for c in candidates:
            key = URLNormalizer.get_dedup_key(c.platform, c.content_url)
            keys.add(key)
        return len(keys)
