"""Schema validation for candidate intake."""

from __future__ import annotations

import re
from typing import Any

# Valid URL patterns for Douyin
DOUYIN_URL_PATTERNS = [
    re.compile(r"^https?://(www\.)?douyin\.com/(user|video|note)/[\w\-/?=]+"),
    re.compile(r"^https?://(www\.)?iesdouyin\.com/"),
]


def _is_valid_url(url: str | None) -> bool:
    """Check if a URL looks like a valid Douyin URL."""
    if not url:
        return False
    url = url.strip()
    return any(pattern.match(url) for pattern in DOUYIN_URL_PATTERNS)


def _is_search_page_url(url: str | None) -> bool:
    """Check if URL is a search page URL (not sufficient as object evidence)."""
    if not url:
        return False
    return "/search/" in url


def validate_row(row: dict[str, Any]) -> dict[str, Any]:
    """Validate a raw CSV row.

    Returns a dict with validation results:
    - status: "valid" | "partial" | "invalid" | "untraceable"
    - errors: list of error messages
    - normalized: cleaned field values
    """
    errors: list[str] = []
    normalized: dict[str, Any] = {}

    # Required: source_query
    source_query = str(row.get("source_query", "")).strip()
    if not source_query:
        errors.append("Missing required field: source_query")
        normalized["source_query"] = ""
    else:
        normalized["source_query"] = source_query

    # Optional: account_name
    account_name = row.get("account_name")
    if account_name and str(account_name).strip():
        normalized["account_name"] = str(account_name).strip()
    else:
        normalized["account_name"] = None

    # Optional: profile_url
    profile_url = row.get("profile_url")
    if profile_url and str(profile_url).strip():
        url = str(profile_url).strip()
        if _is_valid_url(url):
            normalized["profile_url"] = url
        else:
            errors.append(f"Invalid profile_url: {url}")
            normalized["profile_url"] = None
    else:
        normalized["profile_url"] = None

    # Optional: video_title
    video_title = row.get("video_title")
    if video_title and str(video_title).strip():
        normalized["video_title"] = str(video_title).strip()
    else:
        normalized["video_title"] = None

    # Optional: video_url
    video_url = row.get("video_url")
    if video_url and str(video_url).strip():
        url = str(video_url).strip()
        if _is_valid_url(url):
            normalized["video_url"] = url
        else:
            errors.append(f"Invalid video_url: {url}")
            normalized["video_url"] = None
    else:
        normalized["video_url"] = None

    # Optional: evidence_text
    evidence_text = row.get("evidence_text")
    if evidence_text and str(evidence_text).strip():
        normalized["evidence_text"] = str(evidence_text).strip()
    else:
        normalized["evidence_text"] = None

    # Optional: evidence_url
    evidence_url = row.get("evidence_url")
    if evidence_url and str(evidence_url).strip():
        url = str(evidence_url).strip()
        if _is_valid_url(url):
            normalized["evidence_url"] = url
        else:
            errors.append(f"Invalid evidence_url: {url}")
            normalized["evidence_url"] = None
    else:
        normalized["evidence_url"] = None

    # Optional: source_page_url
    source_page_url = row.get("source_page_url")
    if source_page_url and str(source_page_url).strip():
        normalized["source_page_url"] = str(source_page_url).strip()
    else:
        normalized["source_page_url"] = None

    # Optional: captured_at
    captured_at = row.get("captured_at")
    if captured_at and str(captured_at).strip():
        normalized["captured_at"] = str(captured_at).strip()
    else:
        normalized["captured_at"] = None  # Will be set at import time

    # Optional: human_note
    human_note = row.get("human_note")
    if human_note and str(human_note).strip():
        normalized["human_note"] = str(human_note).strip()
    else:
        normalized["human_note"] = None

    # Determine status
    if errors and not source_query or not source_query:
        status = "invalid"
    else:
        # Check traceability: must have at least one object-level URL
        has_object_url = any([
            normalized.get("profile_url"),
            normalized.get("video_url"),
            normalized.get("evidence_url"),
        ])

        if not has_object_url:
            # Has search page URL but no object URL
            if normalized.get("source_page_url") and _is_search_page_url(normalized["source_page_url"]):
                status = "untraceable"
            elif errors:
                status = "partial"
            else:
                status = "untraceable"
        elif errors:
            status = "partial"
        else:
            status = "valid"

    return {
        "status": status,
        "errors": errors,
        "normalized": normalized,
    }
