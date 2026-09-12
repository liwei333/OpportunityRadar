"""Data normalization and deduplication for OR-SPIKE-001.

Handles:
- URL normalization (remove tracking params)
- Text normalization (whitespace, noise removal)
- Metric normalization (1.2万 → 12000)
- Video deduplication (by video_id or normalized URL)
- Account deduplication (by account_id or profile_url)
- Cross-query source merging
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from .models import (
    NormalizedAccount,
    NormalizedVideo,
    RawAccountCandidate,
    RawVideoCandidate,
)

# Tracking parameters to remove from URLs
NOISE_PARAMS: set[str] = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "from",
    "share_app_id",
    "share_link_id",
    "share_track_info",
    "timestamp",
    "_signature",
    "tt_from",
    "enter_from",
    "enter_method",
    "previous_page",
}


def normalize_url(url: str | None) -> str | None:
    """Normalize a URL by removing tracking parameters.

    Preserves the essential path and ID components.
    """
    if not url:
        return None

    url = url.strip()

    # Handle relative URLs - make them absolute
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = "https://www.douyin.com" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return url

    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower() or "www.douyin.com"

    # Remove trailing slash from path (except root)
    path = parsed.path.rstrip("/") or "/"

    # Rebuild URL without query params (Douyin video URLs are path-based)
    # Keep query only if it has non-noise params
    if parsed.query:
        from urllib.parse import parse_qs, urlencode

        params = parse_qs(parsed.query, keep_blank_values=False)
        filtered = {k: v for k, v in params.items() if k.lower() not in NOISE_PARAMS}
        query = urlencode(filtered, doseq=True)
    else:
        query = ""

    # Rebuild
    from urllib.parse import urlunparse

    return urlunparse((scheme, netloc, path, "", query, ""))


def normalize_text(text: str | None) -> str | None:
    """Clean and normalize text fields."""
    if not text:
        return None

    # Normalize whitespace
    cleaned = " ".join(text.split())
    # Remove common UI noise
    cleaned = cleaned.strip()

    return cleaned if cleaned else None


def normalize_metric(value: str | None) -> int | None:
    """Convert Chinese metric strings to integers.

    Examples:
        "1.2万" → 12000
        "3.5w" → 35000
        "1200" → 1200
        "444.4万" → 4444000
    """
    if not value:
        return None

    value = value.strip().replace(",", "")

    try:
        # Handle "万" (10k) and "w" suffix
        match = re.match(r"^([\d.]+)\s*([万w])?$", value, re.IGNORECASE)
        if match:
            number = float(match.group(1))
            suffix = match.group(2)
            if suffix and suffix.lower() in ("万", "w"):
                number *= 10000
            return int(number)
        # Plain number
        return int(float(value))
    except (ValueError, TypeError):
        return None


def normalize_video(raw: RawVideoCandidate) -> NormalizedVideo:
    """Normalize a raw video candidate."""
    video_url = normalize_url(raw.video_url)
    title = normalize_text(raw.title)
    author = normalize_text(raw.author_name)

    # Generate dedup key
    dedup_key = _make_video_dedup_key(raw.video_id, video_url)

    return NormalizedVideo(
        id=raw.id,
        platform=raw.platform,
        video_id=raw.video_id,
        video_url=video_url,
        title=title,
        description=normalize_text(raw.description),
        author_name=author,
        author_profile_url=normalize_url(raw.author_profile_url),
        published_at=raw.published_at,
        like_count=normalize_metric(raw.like_count_raw),
        like_count_raw=raw.like_count_raw,
        comment_count=normalize_metric(raw.comment_count_raw),
        comment_count_raw=raw.comment_count_raw,
        view_count=normalize_metric(raw.view_count_raw),
        view_count_raw=raw.view_count_raw,
        share_count=normalize_metric(raw.share_count_raw),
        share_count_raw=raw.share_count_raw,
        duration=raw.duration,
        source_query=raw.source_query,
        collection_mode=raw.collection_mode,
        source_page_url=raw.source_page_url,
        collected_at=raw.collected_at,
        dedup_key=dedup_key,
    )


def normalize_account(raw: RawAccountCandidate) -> NormalizedAccount:
    """Normalize a raw account candidate."""
    profile_url = normalize_url(raw.profile_url)
    name = normalize_text(raw.account_name)

    dedup_key = _make_account_dedup_key(raw.account_id, profile_url, name)

    return NormalizedAccount(
        id=raw.id,
        platform=raw.platform,
        account_id=raw.account_id,
        account_name=name,
        profile_url=profile_url,
        bio=normalize_text(raw.bio),
        follower_count=normalize_metric(raw.follower_count_raw),
        follower_count_raw=raw.follower_count_raw,
        following_count=normalize_metric(raw.following_count_raw),
        following_count_raw=raw.following_count_raw,
        content_hits=raw.content_hits,
        source_queries=raw.source_queries,
        collected_at=raw.collected_at,
        dedup_key=dedup_key,
    )


def _make_video_dedup_key(
    video_id: str | None,
    video_url: str | None,
) -> str:
    """Generate dedup key for a video.

    Priority: video_id > normalized URL > empty.
    """
    if video_id:
        return f"douyin::video::{video_id}"
    if video_url:
        # Extract video ID from URL if present
        match = re.search(r"/(?:video|note)/(\d+)", video_url)
        if match:
            return f"douyin::video::{match.group(1)}"
        return f"douyin::url::{video_url}"
    return ""


def _make_account_dedup_key(
    account_id: str | None,
    profile_url: str | None,
    account_name: str | None,
) -> str:
    """Generate dedup key for an account.

    Priority: account_id > profile URL > name (last resort).
    """
    if account_id:
        return f"douyin::account::{account_id}"
    if profile_url:
        # Extract user ID from URL if present
        match = re.search(r"/user/([^/]+)", profile_url)
        if match:
            return f"douyin::account::{match.group(1)}"
        return f"douyin::url::{profile_url}"
    if account_name:
        return f"douyin::name::{account_name}"
    return ""


def deduplicate_videos(
    videos: list[NormalizedVideo],
) -> tuple[list[NormalizedVideo], int]:
    """Deduplicate videos by dedup_key.

    Returns:
        Tuple of (unique videos, duplicate count).
    """
    seen: dict[str, NormalizedVideo] = {}
    duplicates = 0

    for video in videos:
        key = video.dedup_key
        if not key:
            # Can't dedup without a key, keep as-is
            seen[f"nokey_{id(video)}"] = video
            continue

        if key in seen:
            duplicates += 1
            # Keep the one with more data
            existing = seen[key]
            if not existing.title and video.title:
                seen[key] = video
        else:
            seen[key] = video

    return list(seen.values()), duplicates


def deduplicate_accounts(
    accounts: list[NormalizedAccount],
) -> tuple[list[NormalizedAccount], int]:
    """Deduplicate accounts by dedup_key.

    When duplicates are found, merges source_queries and increments content_hits.

    Returns:
        Tuple of (unique accounts, duplicate count).
    """
    seen: dict[str, NormalizedAccount] = {}
    duplicates = 0

    for account in accounts:
        key = account.dedup_key
        if not key:
            seen[f"nokey_{id(account)}"] = account
            continue

        if key in seen:
            duplicates += 1
            existing = seen[key]
            # Merge source queries
            existing_queries = set(existing.source_queries)
            new_queries = set(account.source_queries)
            existing.source_queries = sorted(existing_queries | new_queries)
            # Merge content hits
            existing.content_hits += account.content_hits
            # Keep more complete data
            if not existing.bio and account.bio:
                existing.bio = account.bio
            if not existing.follower_count and account.follower_count:
                existing.follower_count = account.follower_count
            if not existing.profile_url and account.profile_url:
                existing.profile_url = account.profile_url
        else:
            seen[key] = account

    return list(seen.values()), duplicates
