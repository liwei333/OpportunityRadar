"""Main collector for OR-SPIKE-001 Douyin Web.

Orchestrates the collection pipeline:
1. Open browser with persistent profile
2. Handle login/verification (manual intervention)
3. Navigate to search or feed
4. Scroll and extract video/account data
5. Save raw data
6. Normalize and deduplicate
7. Generate quality report
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from .douyin_selectors import DouyinUrls
from .extractors import DouyinExtractor
from .models import (
    DataQualityReport,
    NormalizedAccount,
    NormalizedVideo,
    RawAccountCandidate,
    RawVideoCandidate,
)
from .normalizer import (
    deduplicate_accounts,
    deduplicate_videos,
    normalize_account,
    normalize_video,
)
from .quality import QualityAssessor, generate_review_sample

logger = logging.getLogger(__name__)


class DouyinCollector:
    """Collects video and account data from Douyin Web."""

    def __init__(
        self,
        headless: bool = False,
        user_data_dir: str | Path | None = None,
        output_dir: str | Path = "data/spikes/or-spike-001",
    ) -> None:
        self._headless = headless
        self._user_data_dir = Path(user_data_dir) if user_data_dir else None
        self._output_dir = Path(output_dir)
        self._run_id = str(uuid.uuid4())[:12]
        self._profile_dir: Path | None = None

    @property
    def run_id(self) -> str:
        return self._run_id

    def _ensure_dirs(self) -> None:
        """Create output directories for this run."""
        self._run_dir = self._output_dir / self._run_id
        (self._run_dir / "raw").mkdir(parents=True, exist_ok=True)
        (self._run_dir / "normalized").mkdir(parents=True, exist_ok=True)
        (self._run_dir / "screenshots").mkdir(parents=True, exist_ok=True)

    async def collect(
        self,
        queries: list[str],
        limit_per_query: int = 20,
        max_scrolls: int = 10,
        use_search: bool = True,
    ) -> DataQualityReport:
        """Run the full collection pipeline.

        Args:
            queries: List of search keywords.
            limit_per_query: Target number of videos per query.
            max_scrolls: Maximum scroll actions per query.
            use_search: If True, try search (requires login).
                       If False, use homepage feed only.

        Returns:
            DataQualityReport with quality metrics.
        """
        self._ensure_dirs()
        assessor = QualityAssessor()
        assessor.start_run()

        all_raw_videos: list[RawVideoCandidate] = []
        all_raw_accounts: list[RawAccountCandidate] = []
        queries_completed: list[str] = []
        queries_failed: list[str] = []
        per_query_counts: dict[str, int] = {}

        async with async_playwright() as p:
            # Launch browser with persistent context
            if self._user_data_dir:
                self._profile_dir = self._user_data_dir
                self._profile_dir.mkdir(parents=True, exist_ok=True)
                context = await p.chromium.launch_persistent_context(
                    str(self._profile_dir),
                    headless=self._headless,
                    viewport={"width": 1440, "height": 900},
                    locale="zh-CN",
                )
            else:
                context = await p.chromium.launch(
                    headless=self._headless,
                )

            page = context.pages[0] if context.pages else await context.new_page()
            extractor = DouyinExtractor(page)

            try:
                if use_search:
                    # Try search-based collection
                    for query in queries:
                        try:
                            videos = await self._collect_from_search(
                                page, extractor, query, limit_per_query, max_scrolls
                            )
                            all_raw_videos.extend(videos)
                            per_query_counts[query] = len(videos)
                            if videos:
                                queries_completed.append(query)
                            else:
                                queries_failed.append(query)
                        except Exception as e:
                            logger.error("Error collecting for '%s': %s", query, e)
                            assessor.add_error(str(e), {"query": query})
                            queries_failed.append(query)
                            per_query_counts[query] = 0
                else:
                    # Feed-based collection (no login required)
                    videos = await self._collect_from_feed(
                        page, extractor, queries, max_scrolls
                    )
                    all_raw_videos.extend(videos)
                    # All queries get the same feed results
                    for q in queries:
                        per_query_counts[q] = len(videos) if videos else 0
                    if videos:
                        queries_completed = queries[:]
                    else:
                        queries_failed = queries[:]

                # Extract accounts from videos
                all_raw_accounts = await extractor.extract_accounts_from_videos(
                    all_raw_videos
                )

            finally:
                await context.close()

        # Save raw data
        self._save_raw_data(all_raw_videos, all_raw_accounts)

        # Normalize
        normalized_videos = [normalize_video(v) for v in all_raw_videos]
        normalized_accounts = [normalize_account(a) for a in all_raw_accounts]

        # Deduplicate
        unique_videos, dup_videos = deduplicate_videos(normalized_videos)
        unique_accounts, dup_accounts = deduplicate_accounts(normalized_accounts)

        # Save normalized data
        self._save_normalized_data(unique_videos, unique_accounts)

        # Generate quality report
        report = assessor.assess(
            queries=queries,
            queries_completed=queries_completed,
            queries_failed=queries_failed,
            videos=unique_videos,
            accounts=unique_accounts,
            raw_count=len(all_raw_videos),
            duplicate_video_count=dup_videos,
            duplicate_account_count=dup_accounts,
            per_query_counts=per_query_counts,
        )

        # Save report
        self._save_report(report, unique_videos)

        return report

    async def _collect_from_search(
        self,
        page: Any,
        extractor: DouyinExtractor,
        query: str,
        limit: int,
        max_scrolls: int,
    ) -> list[RawVideoCandidate]:
        """Collect videos from search results for a single query."""
        videos: list[RawVideoCandidate] = []

        # Navigate to search page (without ?type=video to avoid verification)
        url = DouyinUrls.SEARCH.format(query=query)
        logger.info("Searching: %s", url)
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Check for verification
        if await extractor.check_verification_required():
            verified = await extractor.wait_for_verification(timeout_ms=120000)
            if not verified:
                logger.warning("Verification not solved for query: %s", query)
                return videos

        # Check for login
        if await extractor.check_login_required():
            logged_in = await extractor.wait_for_login(timeout_ms=120000)
            if not logged_in:
                logger.warning("Login not completed for query: %s", query)
                return videos

        # Wait for content to load
        await asyncio.sleep(5)

        # Scroll and extract
        videos = await self._scroll_and_extract(
            page, extractor, query, limit, max_scrolls
        )

        return videos

    async def _collect_from_feed(
        self,
        page: Any,
        extractor: DouyinExtractor,
        queries: list[str],
        max_scrolls: int,
    ) -> list[RawVideoCandidate]:
        """Collect videos from the homepage feed (no login required)."""
        videos: list[RawVideoCandidate] = []

        # Navigate to homepage feed
        url = DouyinUrls.HOMEPAGE
        logger.info("Loading feed: %s", url)
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # Try to close login dialog if it appears
        if await extractor.check_login_required():
            logger.info("Login dialog detected, trying to close...")
            await page.keyboard.press("Escape")
            await asyncio.sleep(2)

        # Extract initial feed content
        feed_videos = await extractor.extract_videos_from_feed(
            source_query=queries[0] if queries else "feed"
        )
        videos.extend(feed_videos)

        # Scroll to load more
        for _i in range(max_scrolls):
            if len(videos) >= len(queries) * 20:
                break

            prev_count = len(videos)
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(3)

            # Extract new content
            new_videos = await extractor.extract_videos_from_feed(
                source_query=queries[0] if queries else "feed"
            )

            # Only add new unique videos
            existing_texts = {v.raw_text for v in videos if v.raw_text}
            for v in new_videos:
                if v.raw_text and v.raw_text not in existing_texts:
                    videos.append(v)

            if len(videos) == prev_count:
                # No new content loaded
                break

        return videos

    async def _scroll_and_extract(
        self,
        page: Any,
        extractor: DouyinExtractor,
        query: str,
        limit: int,
        max_scrolls: int,
    ) -> list[RawVideoCandidate]:
        """Scroll a page and extract video data."""
        videos: list[RawVideoCandidate] = []

        for _i in range(max_scrolls):
            if len(videos) >= limit:
                break

            # Extract current content
            new_videos = await extractor.extract_videos_from_feed(
                source_query=query
            )

            # Add unique videos
            existing_texts = {v.raw_text for v in videos if v.raw_text}
            for v in new_videos:
                if v.raw_text and v.raw_text not in existing_texts:
                    videos.append(v)

            # Scroll
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(3)

        return videos[:limit]

    def _save_raw_data(
        self,
        videos: list[RawVideoCandidate],
        accounts: list[RawAccountCandidate],
    ) -> None:
        """Save raw data to JSONL files."""
        # Save videos
        video_path = self._run_dir / "raw" / "search_results.jsonl"
        with open(video_path, "w", encoding="utf-8") as f:
            for v in videos:
                f.write(json.dumps(v.model_dump(), ensure_ascii=False) + "\n")

        # Save accounts
        account_path = self._run_dir / "raw" / "accounts.jsonl"
        with open(account_path, "w", encoding="utf-8") as f:
            for a in accounts:
                f.write(json.dumps(a.model_dump(), ensure_ascii=False) + "\n")

        logger.info(
            "Saved %d raw videos, %d raw accounts",
            len(videos), len(accounts),
        )

    def _save_normalized_data(
        self,
        videos: list[NormalizedVideo],
        accounts: list[NormalizedAccount],
    ) -> None:
        """Save normalized data to JSONL files."""
        # Save videos
        video_path = self._run_dir / "normalized" / "videos.jsonl"
        with open(video_path, "w", encoding="utf-8") as f:
            for v in videos:
                f.write(json.dumps(v.model_dump(), ensure_ascii=False) + "\n")

        # Save accounts
        account_path = self._run_dir / "normalized" / "accounts.jsonl"
        with open(account_path, "w", encoding="utf-8") as f:
            for a in accounts:
                f.write(json.dumps(a.model_dump(), ensure_ascii=False) + "\n")

        # Save query hits
        query_hits: dict[str, list[str]] = {}
        for v in videos:
            if v.source_query:
                query_hits.setdefault(v.source_query, []).append(v.id)
        hits_path = self._run_dir / "normalized" / "query_hits.jsonl"
        with open(hits_path, "w", encoding="utf-8") as f:
            for query, ids in query_hits.items():
                f.write(json.dumps({"query": query, "video_ids": ids}, ensure_ascii=False) + "\n")

        logger.info(
            "Saved %d normalized videos, %d normalized accounts",
            len(videos), len(accounts),
        )

    def _save_report(
        self,
        report: DataQualityReport,
        videos: list[NormalizedVideo],
    ) -> None:
        """Save quality report and review sample."""
        # Save report as markdown
        report_path = self._run_dir / "report.md"
        report_path.write_text(report.to_markdown(), encoding="utf-8")

        # Save report as JSON
        report_json_path = self._run_dir / "report.json"
        report_json_path.write_text(
            json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Generate review sample
        sample_path = generate_review_sample(
            videos,
            sample_size=50,
            output_path=str(self._run_dir / "review_sample.csv"),
        )
        logger.info("Review sample saved: %s", sample_path)

        logger.info("Report saved: %s", report_path)
