"""CLI runner for OR-SPIKE-001C Human-assisted Candidate Intake.

Usage:
    cd services/agent
    .venv/bin/python -m spikes.or_spike_001c.run --input data/intake/douyin_candidates.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import IntakeQualityReport, NormalizedCandidate, RawCandidateInput
from .normalizer import deduplicate_and_merge, normalize_candidate, normalize_row
from .validator import validate_row

logger = logging.getLogger(__name__)


def load_csv(input_path: str) -> list[dict[str, Any]]:
    """Load rows from a CSV file."""
    path = Path(input_path)
    if not path.exists():
        logger.error("Input file not found: %s", path)
        sys.exit(1)

    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))

    return rows


def run_intake(
    input_path: str,
    output_dir: str = "data/intake/runs",
) -> IntakeQualityReport:
    """Run the full intake pipeline."""
    run_id = str(uuid.uuid4())[:12]
    started_at = datetime.now(UTC).isoformat()

    # Setup output directory
    run_dir = Path(output_dir) / run_id
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / "normalized").mkdir(parents=True, exist_ok=True)

    # Load CSV
    rows = load_csv(input_path)
    logger.info("Loaded %d rows from %s", len(rows), input_path)

    # Validate
    valid_rows: list[RawCandidateInput] = []
    valid_count = 0
    partial_count = 0
    invalid_count = 0
    untraceable_count = 0

    for row in rows:
        result = validate_row(row)
        raw_input = normalize_row(result)
        valid_rows.append(raw_input)

        if result["status"] == "valid":
            valid_count += 1
        elif result["status"] == "partial":
            partial_count += 1
        elif result["status"] == "untraceable":
            untraceable_count += 1
        else:
            invalid_count += 1

    logger.info(
        "Validation: %d valid, %d partial, %d invalid, %d untraceable",
        valid_count, partial_count, invalid_count, untraceable_count,
    )

    # Save raw imported rows
    raw_path = run_dir / "raw" / "imported_rows.jsonl"
    with open(raw_path, "w", encoding="utf-8") as f:
        for raw in valid_rows:
            f.write(json.dumps(raw.model_dump(), ensure_ascii=False) + "\n")

    # Normalize
    normalized_candidates: list[NormalizedCandidate] = []
    for raw in valid_rows:
        candidate = normalize_candidate(raw)
        normalized_candidates.append(candidate)

    # Deduplicate and merge
    unique_candidates, duplicate_count, merged_count = deduplicate_and_merge(
        normalized_candidates
    )

    logger.info(
        "Dedup: %d unique, %d duplicates, %d cross-query merged",
        len(unique_candidates), duplicate_count, merged_count,
    )

    # Save normalized candidates
    norm_path = run_dir / "normalized" / "candidates.jsonl"
    with open(norm_path, "w", encoding="utf-8") as f:
        for candidate in unique_candidates:
            f.write(json.dumps(candidate.model_dump(), ensure_ascii=False) + "\n")

    # Save invalid rows
    invalid_path = run_dir / "invalid_rows.csv"
    with open(invalid_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source_query", "status", "errors"])
        for raw in valid_rows:
            if raw.validation_status in ("invalid", "untraceable"):
                writer.writerow([
                    raw.source_query,
                    raw.validation_status,
                    "; ".join(raw.validation_errors),
                ])

    # Calculate stats
    queries = set()
    per_query_count: dict[str, int] = {}
    traceable_count = 0
    untraceable_candidates = 0

    for candidate in unique_candidates:
        for q in candidate.source_queries:
            queries.add(q)
            per_query_count[q] = per_query_count.get(q, 0) + 1

        if candidate.is_traceable:
            traceable_count += 1
        else:
            untraceable_candidates += 1

    finished_at = datetime.now(UTC).isoformat()

    report = IntakeQualityReport(
        run_id=run_id,
        run_started_at=started_at,
        run_finished_at=finished_at,
        duration_seconds=0,  # Will be set below
        rows_received=len(rows),
        valid_rows=valid_count,
        partial_rows=partial_count,
        invalid_rows=invalid_count,
        untraceable_rows=untraceable_count,
        unique_candidates=len(unique_candidates),
        duplicate_rows=duplicate_count,
        cross_query_merged_candidates=merged_count,
        queries_covered=len(queries),
        per_query_candidate_count=per_query_count,
        traceable_candidates=traceable_count,
        untraceable_candidates=untraceable_candidates,
    )

    # Save report
    report_path = run_dir / "report.md"
    report_path.write_text(report.to_markdown(), encoding="utf-8")

    report_json_path = run_dir / "report.json"
    report_json_path.write_text(
        json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info("Report saved: %s", report_path)

    return report


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="OR-SPIKE-001C: Human-assisted Candidate Intake",
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input CSV file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/intake/runs",
        help="Output directory for intake results.",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("OR-SPIKE-001C: Human-assisted Candidate Intake")
    print("=" * 60)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print("=" * 60)

    started = time.time()
    report = run_intake(args.input, args.output)
    duration = time.time() - started

    print("\n" + "=" * 60)
    print("INTAKE COMPLETE")
    print("=" * 60)
    print(f"Run ID: {report.run_id}")
    print(f"Rows received: {report.rows_received}")
    print(f"Valid: {report.valid_rows} | Partial: {report.partial_rows}")
    print(f"Invalid: {report.invalid_rows} | Untraceable: {report.untraceable_rows}")
    print(f"Unique candidates: {report.unique_candidates}")
    print(f"Duplicates: {report.duplicate_rows}")
    print(f"Cross-query merged: {report.cross_query_merged_candidates}")
    print(f"Traceable rate: {report.traceable_rate:.1%}")
    print(f"Queries covered: {report.queries_covered}")
    print(f"Duration: {duration:.1f}s")
    print(f"Report: {args.output}/{report.run_id}/report.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
