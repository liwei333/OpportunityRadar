"""Data models for OR-SPIKE-001 Douyin Web Collector.

Defines the raw and normalized data structures for video candidates,
account candidates, and data quality reports.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawVideoCandidate(BaseModel):
    """Raw video data extracted from Douyin.

    All fields are optional because extraction may partially fail.
    No AI guessing — if data is not in the DOM, it stays null.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: str = "douyin"
    video_id: str | None = None
    video_url: str | None = None
    title: str | None = None
    description: str | None = None
    author_name: str | None = None
    author_profile_url: str | None = None
    published_at: str | None = None
    like_count_raw: str | None = None
    comment_count_raw: str | None = None
    view_count_raw: str | None = None
    share_count_raw: str | None = None
    duration: str | None = None
    source_query: str = ""
    collected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    raw_text: str | None = None
    extraction_method: str = ""
    extraction_success: bool = False


class RawAccountCandidate(BaseModel):
    """Raw account data extracted from Douyin."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: str = "douyin"
    account_id: str | None = None
    account_name: str | None = None
    profile_url: str | None = None
    bio: str | None = None
    follower_count_raw: str | None = None
    following_count_raw: str | None = None
    content_hits: int = 0
    source_queries: list[str] = Field(default_factory=list)
    collected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    raw_text: str | None = None


class NormalizedVideo(BaseModel):
    """Video after normalization and cleaning."""

    id: str
    platform: str = "douyin"
    video_id: str | None = None
    video_url: str | None = None
    title: str | None = None
    description: str | None = None
    author_name: str | None = None
    author_profile_url: str | None = None
    published_at: str | None = None
    like_count: int | None = None
    like_count_raw: str | None = None
    comment_count: int | None = None
    comment_count_raw: str | None = None
    view_count: int | None = None
    view_count_raw: str | None = None
    share_count: int | None = None
    share_count_raw: str | None = None
    duration: str | None = None
    source_query: str = ""
    collected_at: str
    dedup_key: str = ""


class NormalizedAccount(BaseModel):
    """Account after normalization and cleaning."""

    id: str
    platform: str = "douyin"
    account_id: str | None = None
    account_name: str | None = None
    profile_url: str | None = None
    bio: str | None = None
    follower_count: int | None = None
    follower_count_raw: str | None = None
    following_count: int | None = None
    following_count_raw: str | None = None
    content_hits: int = 0
    source_queries: list[str] = Field(default_factory=list)
    collected_at: str
    dedup_key: str = ""


class DataQualityReport(BaseModel):
    """Data quality assessment for a collection run."""

    # Run metadata
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_started_at: str = ""
    run_finished_at: str = ""
    duration_seconds: float = 0.0

    # Query stats
    queries_requested: int = 0
    queries_completed: int = 0
    queries_failed: int = 0

    # Raw results
    raw_result_count: int = 0

    # Unique counts
    unique_video_count: int = 0
    unique_account_count: int = 0

    # Duplicates
    duplicate_video_count: int = 0
    duplicate_account_count: int = 0

    # Extraction quality
    extract_success_count: int = 0
    extract_failure_count: int = 0

    # URL traceability
    traceable_url_count: int = 0

    # Missing fields
    missing_title_count: int = 0
    missing_author_count: int = 0

    # Per-query stats
    per_query_result_count: dict[str, int] = Field(default_factory=dict)

    # Errors
    errors: list[dict[str, Any]] = Field(default_factory=list)

    # Computed rates
    @property
    def extraction_success_rate(self) -> float:
        total = self.extract_success_count + self.extract_failure_count
        if total == 0:
            return 0.0
        return self.extract_success_count / total

    @property
    def traceable_url_rate(self) -> float:
        if self.raw_result_count == 0:
            return 0.0
        return self.traceable_url_count / self.raw_result_count

    @property
    def duplicate_rate(self) -> float:
        if self.raw_result_count == 0:
            return 0.0
        return self.duplicate_video_count / self.raw_result_count

    def to_markdown(self) -> str:
        """Generate a markdown report."""
        lines = [
            f"# Data Quality Report — Run {self.run_id[:8]}",
            "",
            "## Run Metadata",
            f"- Started: {self.run_started_at}",
            f"- Finished: {self.run_finished_at}",
            f"- Duration: {self.duration_seconds:.1f}s",
            "",
            "## Query Stats",
            f"- Requested: {self.queries_requested}",
            f"- Completed: {self.queries_completed}",
            f"- Failed: {self.queries_failed}",
            "",
            "## Results",
            f"- Raw candidates: {self.raw_result_count}",
            f"- Unique videos: {self.unique_video_count}",
            f"- Unique accounts: {self.unique_account_count}",
            f"- Duplicate videos: {self.duplicate_video_count}",
            f"- Duplicate accounts: {self.duplicate_account_count}",
            "",
            "## Quality Rates",
            f"- Extraction success: {self.extraction_success_rate:.1%} ({self.extract_success_count}/{self.extract_success_count + self.extract_failure_count})",
            f"- Traceable URL rate: {self.traceable_url_rate:.1%} ({self.traceable_url_count}/{self.raw_result_count})",
            f"- Duplicate rate: {self.duplicate_rate:.1%}",
            "",
            "## Missing Fields",
            f"- Missing title: {self.missing_title_count}",
            f"- Missing author: {self.missing_author_count}",
            "",
            "## Per-Query Results",
        ]
        for query, count in self.per_query_result_count.items():
            lines.append(f"- `{query}`: {count}")

        if self.errors:
            lines.extend(["", "## Errors"])
            for err in self.errors[:20]:
                lines.append(f"- {err}")

        return "\n".join(lines)
