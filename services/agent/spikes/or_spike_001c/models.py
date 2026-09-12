"""Models for OR-SPIKE-001C Human-assisted Candidate Intake."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    """Get current UTC time as ISO string with timezone offset."""
    return datetime.now(UTC).isoformat()


class RawCandidateInput(BaseModel):
    """Raw candidate data from CSV input."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_query: str = ""
    account_name: str | None = None
    profile_url: str | None = None
    video_title: str | None = None
    video_url: str | None = None
    evidence_text: str | None = None
    evidence_url: str | None = None
    source_page_url: str | None = None
    captured_at: str = Field(default_factory=_utc_now_iso)
    human_note: str | None = None

    # Validation result
    validation_status: str = "pending"
    validation_errors: list[str] = Field(default_factory=list)


class NormalizedCandidate(BaseModel):
    """Normalized candidate after validation and cleaning."""

    id: str
    source_query: str
    account_name: str | None = None
    profile_url: str | None = None
    video_title: str | None = None
    video_url: str | None = None
    evidence_text: str | None = None
    evidence_url: str | None = None
    source_page_url: str | None = None
    captured_at: str = ""
    human_note: str | None = None

    # Metadata
    platform: str = "douyin"
    collection_mode: str = "human_assisted"
    dedup_key: str = ""

    # Traceability
    is_traceable: bool = False
    traceability_source: str | None = None  # "profile_url", "video_url", "evidence_url"

    # Cross-query merge
    source_queries: list[str] = Field(default_factory=list)


class IntakeQualityReport(BaseModel):
    """Quality report for an intake run."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_started_at: str = ""
    run_finished_at: str = ""
    duration_seconds: float = 0.0

    # Input stats
    rows_received: int = 0

    # Validation stats
    valid_rows: int = 0
    partial_rows: int = 0
    invalid_rows: int = 0
    untraceable_rows: int = 0

    # Dedup stats
    unique_candidates: int = 0
    duplicate_rows: int = 0
    cross_query_merged_candidates: int = 0

    # Query stats
    queries_covered: int = 0
    per_query_candidate_count: dict[str, int] = Field(default_factory=dict)

    # Traceability
    traceable_candidates: int = 0
    untraceable_candidates: int = 0

    # Computed rates
    @property
    def traceable_rate(self) -> float:
        if self.unique_candidates == 0:
            return 0.0
        return self.traceable_candidates / self.unique_candidates

    @property
    def valid_rate(self) -> float:
        if self.rows_received == 0:
            return 0.0
        return (self.valid_rows + self.partial_rows) / self.rows_received

    def to_markdown(self) -> str:
        """Generate a markdown report."""
        lines = [
            f"# Intake Quality Report — Run {self.run_id[:8]}",
            "",
            "## Run Metadata",
            f"- Started: {self.run_started_at}",
            f"- Finished: {self.run_finished_at}",
            f"- Duration: {self.duration_seconds:.1f}s",
            "",
            "## Input Stats",
            f"- Rows received: {self.rows_received}",
            "",
            "## Validation",
            f"- Valid: {self.valid_rows}",
            f"- Partial: {self.partial_rows}",
            f"- Invalid: {self.invalid_rows}",
            f"- Untraceable: {self.untraceable_rows}",
            f"- Valid rate: {self.valid_rate:.1%}",
            "",
            "## Deduplication",
            f"- Unique candidates: {self.unique_candidates}",
            f"- Duplicate rows: {self.duplicate_rows}",
            f"- Cross-query merged: {self.cross_query_merged_candidates}",
            "",
            "## Traceability",
            f"- Traceable candidates: {self.traceable_candidates}",
            f"- Untraceable candidates: {self.untraceable_candidates}",
            f"- Traceable rate: {self.traceable_rate:.1%}",
            "",
            "## Queries",
            f"- Queries covered: {self.queries_covered}",
            "",
            "## Per-Query Candidate Count",
        ]
        for query, count in sorted(
            self.per_query_candidate_count.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            lines.append(f"- `{query}`: {count}")

        return "\n".join(lines)
