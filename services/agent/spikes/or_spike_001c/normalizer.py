"""Normalization and deduplication for candidate intake."""

from __future__ import annotations

from typing import Any

from .models import NormalizedCandidate, RawCandidateInput


def _normalize_url(url: str | None) -> str | None:
    """Normalize a URL by removing tracking parameters."""
    if not url:
        return None

    url = url.strip()

    # Handle relative URLs
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = "https://www.douyin.com" + url

    try:
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

        parsed = urlparse(url)
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower() or "www.douyin.com"
        path = parsed.path.rstrip("/") or "/"

        # Remove tracking params
        noise_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term",
            "utm_content", "from", "share_app_id", "share_link_id",
            "share_track_info", "timestamp", "_signature", "tt_from",
            "enter_from", "enter_method", "previous_page", "from_tab_name",
        }

        if parsed.query:
            params = parse_qs(parsed.query, keep_blank_values=False)
            filtered = {k: v for k, v in params.items() if k.lower() not in noise_params}
            query = urlencode(filtered, doseq=True)
        else:
            query = ""

        return urlunparse((scheme, netloc, path, "", query, ""))
    except Exception:
        return url


def _normalize_text(text: str | None) -> str | None:
    """Clean and normalize text fields."""
    if not text:
        return None
    cleaned = " ".join(text.split())
    return cleaned if cleaned else None


def _make_candidate_dedup_key(
    profile_url: str | None,
    account_name: str | None,
) -> str:
    """Generate dedup key for a candidate.

    Priority: profile_url > normalized account_name.
    """
    if profile_url:
        normalized = _normalize_url(profile_url)
        if normalized:
            return f"douyin::profile::{normalized}"

    if account_name:
        normalized = account_name.strip().lower()[:80]
        return f"douyin::name::{normalized}"

    return ""


def _is_traceable(normalized: dict[str, Any]) -> tuple[bool, str | None]:
    """Check if a candidate has object-level traceability.

    Returns (is_traceable, source).
    """
    if normalized.get("profile_url"):
        return True, "profile_url"
    if normalized.get("video_url"):
        return True, "video_url"
    if normalized.get("evidence_url"):
        return True, "evidence_url"
    return False, None


def normalize_row(validated: dict[str, Any]) -> RawCandidateInput:
    """Create a RawCandidateInput from validated data."""
    norm = validated["normalized"]
    from datetime import UTC, datetime

    captured_at = norm.get("captured_at") or datetime.now(UTC).isoformat()

    return RawCandidateInput(
        source_query=norm["source_query"],
        account_name=norm.get("account_name"),
        profile_url=norm.get("profile_url"),
        video_title=norm.get("video_title"),
        video_url=norm.get("video_url"),
        evidence_text=norm.get("evidence_text"),
        evidence_url=norm.get("evidence_url"),
        source_page_url=norm.get("source_page_url"),
        captured_at=captured_at,
        human_note=norm.get("human_note"),
        validation_status=validated["status"],
        validation_errors=validated["errors"],
    )


def normalize_candidate(raw: RawCandidateInput) -> NormalizedCandidate:
    """Normalize a raw candidate input."""
    profile_url = _normalize_url(raw.profile_url)
    video_url = _normalize_url(raw.video_url)
    evidence_url = _normalize_url(raw.evidence_url)
    source_page_url = _normalize_url(raw.source_page_url)
    account_name = _normalize_text(raw.account_name)
    video_title = _normalize_text(raw.video_title)
    evidence_text = _normalize_text(raw.evidence_text)

    dedup_key = _make_candidate_dedup_key(profile_url, account_name)
    is_traceable, traceability_source = _is_traceable({
        "profile_url": profile_url,
        "video_url": video_url,
        "evidence_url": evidence_url,
    })

    return NormalizedCandidate(
        id=raw.id,
        source_query=raw.source_query,
        account_name=account_name,
        profile_url=profile_url,
        video_title=video_title,
        video_url=video_url,
        evidence_text=evidence_text,
        evidence_url=evidence_url,
        source_page_url=source_page_url,
        captured_at=raw.captured_at or "",
        human_note=raw.human_note,
        platform="douyin",
        collection_mode="human_assisted",
        dedup_key=dedup_key,
        is_traceable=is_traceable,
        traceability_source=traceability_source,
        source_queries=[raw.source_query] if raw.source_query else [],
    )


def deduplicate_and_merge(
    candidates: list[NormalizedCandidate],
) -> tuple[list[NormalizedCandidate], int, int]:
    """Deduplicate candidates and merge source_queries.

    Returns:
        Tuple of (unique candidates, duplicate count, merged count).
    """
    seen: dict[str, NormalizedCandidate] = {}
    duplicate_count = 0
    merged_count = 0

    for candidate in candidates:
        key = candidate.dedup_key
        if not key:
            # Can't dedup without a key, keep as-is
            seen[f"nokey_{id(candidate)}"] = candidate
            continue

        # Ensure source_queries includes the primary source_query
        if candidate.source_query and candidate.source_query not in candidate.source_queries:
            candidate.source_queries.insert(0, candidate.source_query)

        if key in seen:
            duplicate_count += 1
            existing = seen[key]

            # Merge source queries
            existing_queries = set(existing.source_queries)
            new_queries = set(candidate.source_queries)
            merged_queries = existing_queries | new_queries
            if merged_queries != existing_queries:
                existing.source_queries = sorted(merged_queries)
                merged_count += 1

            # Keep more complete data
            if not existing.profile_url and candidate.profile_url:
                existing.profile_url = candidate.profile_url
            if not existing.account_name and candidate.account_name:
                existing.account_name = candidate.account_name
            if not existing.evidence_text and candidate.evidence_text:
                existing.evidence_text = candidate.evidence_text
            if not existing.evidence_url and candidate.evidence_url:
                existing.evidence_url = candidate.evidence_url
        else:
            seen[key] = candidate

    return list(seen.values()), duplicate_count, merged_count
