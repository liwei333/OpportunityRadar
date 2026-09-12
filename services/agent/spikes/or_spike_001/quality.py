"""Data quality assessment for OR-SPIKE-001.

Calculates quality metrics and generates the DataQualityReport.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from .models import (
    DataQualityReport,
    NormalizedAccount,
    NormalizedVideo,
)


class QualityAssessor:
    """Assess data quality of a collection run."""

    def __init__(self) -> None:
        self._start_time: float = 0.0
        self._errors: list[dict[str, Any]] = []

    def start_run(self) -> None:
        """Mark the start of a collection run."""
        self._start_time = time.time()
        self._errors = []

    def add_error(self, error: str, context: dict[str, Any] | None = None) -> None:
        """Record an error that occurred during collection."""
        self._errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "context": context or {},
        })

    def assess(
        self,
        queries: list[str],
        queries_completed: list[str],
        queries_failed: list[str],
        videos: list[NormalizedVideo],
        accounts: list[NormalizedAccount],
        raw_count: int,
        duplicate_video_count: int,
        duplicate_account_count: int,
        per_query_counts: dict[str, int],
    ) -> DataQualityReport:
        """Generate a DataQualityReport from collection results."""
        duration = time.time() - self._start_time if self._start_time else 0

        # Count extraction successes/failures
        extract_success = sum(1 for v in videos if v.title or v.author_name)
        extract_failure = len(videos) - extract_success

        # Count traceable URLs
        traceable = sum(1 for v in videos if v.video_url)

        # Count missing fields
        missing_title = sum(1 for v in videos if not v.title)
        missing_author = sum(1 for v in videos if not v.author_name)

        return DataQualityReport(
            run_started_at=datetime.fromtimestamp(
                self._start_time if self._start_time else time.time()
            ).isoformat(),
            run_finished_at=datetime.utcnow().isoformat(),
            duration_seconds=round(duration, 2),
            queries_requested=len(queries),
            queries_completed=len(queries_completed),
            queries_failed=len(queries_failed),
            raw_result_count=raw_count,
            unique_video_count=len(videos),
            unique_account_count=len(accounts),
            duplicate_video_count=duplicate_video_count,
            duplicate_account_count=duplicate_account_count,
            extract_success_count=extract_success,
            extract_failure_count=extract_failure,
            traceable_url_count=traceable,
            missing_title_count=missing_title,
            missing_author_count=missing_author,
            per_query_result_count=per_query_counts,
            errors=self._errors[:50],  # Cap at 50 errors
        )


def generate_review_sample(
    videos: list[NormalizedVideo],
    sample_size: int = 50,
    output_path: str | None = None,
) -> str:
    """Generate a review_sample.csv for manual relevance assessment.

    Randomly samples videos and creates a CSV with fields for
    human annotators to fill in.

    Args:
        videos: List of normalized videos.
        sample_size: Number of videos to sample.
        output_path: Path to save the CSV. If None, uses default.

    Returns:
        The file path of the generated CSV.
    """
    import csv
    import random

    if not videos:
        return ""

    # Sample videos (or use all if less than sample_size)
    sample = random.sample(videos, min(sample_size, len(videos)))

    if not output_path:
        output_path = "data/spikes/or-spike-001/review_sample.csv"

    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "video_url",
            "title",
            "author",
            "source_query",
            "manual_relevant",
            "manual_notes",
        ])
        for video in sample:
            writer.writerow([
                video.video_url or "",
                video.title or "",
                video.author_name or "",
                video.source_query or "",
                "",  # manual_relevant - left blank for human
                "",  # manual_notes - left blank for human
            ])

    return output_path
