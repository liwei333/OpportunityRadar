"""CLI runner for OR-SPIKE-001 Douyin Web Collector.

Usage:
    cd services/agent
    .venv/bin/python -m spikes.or_spike_001.run --queries-file queries.txt --headed
    .venv/bin/python -m spikes.or_spike_001.run --query "短视频代运营" --headed
    .venv/bin/python -m spikes.or_spike_001.run --feed-only --headed
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Default search queries for the spike
DEFAULT_QUERIES = [
    "短视频代运营",
    "企业短视频获客",
    "工业品短视频",
    "制造业短视频运营",
    "B2B短视频获客",
    "抖音企业获客",
    "工业品抖音运营",
    "制造业抖音获客",
    "短视频精准获客",
    "企业抖音代运营",
]


def load_queries(args) -> list[str]:
    """Load queries from file or command line."""
    if args.queries_file:
        path = Path(args.queries_file)
        if not path.exists():
            logger.error("Queries file not found: %s", path)
            sys.exit(1)
        queries = [
            line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        return queries

    if args.query:
        return [args.query]

    return DEFAULT_QUERIES


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="OR-SPIKE-001: Douyin Web Real Data Collector",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Single search query (for testing).",
    )
    parser.add_argument(
        "--queries-file",
        type=str,
        help="File with one query per line.",
    )
    parser.add_argument(
        "--limit-per-query",
        type=int,
        default=20,
        help="Target videos per query (default: 20).",
    )
    parser.add_argument(
        "--max-scrolls",
        type=int,
        default=10,
        help="Maximum scroll actions per query (default: 10).",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        default=False,
        help="Run browser in headed mode (visible).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/spikes/or-spike-001",
        help="Output directory for collected data.",
    )
    parser.add_argument(
        "--profile-dir",
        type=str,
        default="data/browser_profile",
        help="Browser profile directory for session persistence.",
    )
    parser.add_argument(
        "--feed-only",
        action="store_true",
        default=False,
        help="Only collect from homepage feed (no search, no login required).",
    )
    parser.add_argument(
        "--use-search",
        action="store_true",
        default=False,
        help="Use search (requires login).",
    )

    args = parser.parse_args()

    # Import here to avoid import errors if module structure is wrong
    from .collector import DouyinCollector

    queries = load_queries(args)
    headless = args.headless and not args.headed

    print("=" * 60)
    print("OR-SPIKE-001: Douyin Web Real Data Collector")
    print("=" * 60)
    print(f"Queries: {len(queries)}")
    print(f"Limit per query: {args.limit_per_query}")
    print(f"Max scrolls: {args.max_scrolls}")
    print(f"Headless: {headless}")
    print(f"Output: {args.output_dir}")
    print(f"Profile: {args.profile_dir}")
    print(f"Mode: {'feed-only' if args.feed_only else 'search' if args.use_search else 'feed-only'}")
    print("=" * 60)

    collector = DouyinCollector(
        headless=headless,
        user_data_dir=args.profile_dir,
        output_dir=args.output_dir,
    )

    use_search = args.use_search and not args.feed_only

    report = await collector.collect(
        queries=queries,
        limit_per_query=args.limit_per_query,
        max_scrolls=args.max_scrolls,
        use_search=use_search,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("COLLECTION COMPLETE")
    print("=" * 60)
    print(f"Run ID: {report.run_id}")
    print(f"Queries: {report.queries_completed}/{report.queries_requested} completed")
    print(f"Raw results: {report.raw_result_count}")
    print(f"Unique videos: {report.unique_video_count}")
    print(f"Unique accounts: {report.unique_account_count}")
    print(f"Extraction success: {report.extraction_success_rate:.1%}")
    print(f"Traceable URL rate: {report.traceable_url_rate:.1%}")
    print(f"Duplicate rate: {report.duplicate_rate:.1%}")
    print(f"Duration: {report.duration_seconds:.1f}s")
    print(f"Report: {args.output_dir}/{collector.run_id}/report.md")
    print("=" * 60)

    # Save summary
    summary_path = Path(args.output_dir) / f"run_{collector.run_id}_summary.json"
    summary_path.write_text(
        json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Summary saved: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
