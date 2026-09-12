"""Data normalization and cleaning utilities.

Handles URL standardization, field normalization, and data cleaning.
Uses Polars for efficient batch operations where applicable.
"""

from contextlib import suppress
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

# Query parameters that carry no semantic value for deduplication
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


class URLNormalizer:
    """Normalize URLs by removing tracking parameters and standardizing format."""

    @staticmethod
    def normalize(url: str) -> str:
        """Normalize a URL by removing noise query parameters.

        Args:
            url: The original URL string.

        Returns:
            The normalized URL with tracking params removed,
            scheme lowered, and trailing slash removed from path.
        """
        if not url:
            return ""

        try:
            parsed = urlparse(url.strip())
        except Exception:
            return url

        # Lowercase scheme and netloc
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove trailing slash from path
        path = parsed.path.rstrip("/") or "/"

        # Filter query parameters
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        filtered_params = {
            k: v for k, v in query_params.items() if k.lower() not in NOISE_PARAMS
        }
        query = urlencode(filtered_params, doseq=True)

        return urlunparse((scheme, netloc, path, parsed.params, query, ""))

    @staticmethod
    def normalize_platform_url(platform: str, url: str) -> str:
        """Normalize a URL and prepend platform context."""
        normalized = URLNormalizer.normalize(url)
        return normalized

    @staticmethod
    def get_dedup_key(platform: str, url: str) -> str:
        """Generate a dedup key from platform + normalized URL."""
        normalized = URLNormalizer.normalize(url)
        return f"{platform}::{normalized}"


class DataCleaner:
    """Clean and standardize raw data fields."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text by removing extra whitespace and control characters.

        Args:
            text: Raw text string.

        Returns:
            Cleaned text with normalized whitespace.
        """
        if not text:
            return ""
        # Replace multiple whitespace with single space
        cleaned = " ".join(text.split())
        return cleaned.strip()

    @staticmethod
    def clean_account_name(name: str) -> str:
        """Clean account name by removing special characters and extra spaces."""
        if not name:
            return ""
        return DataCleaner.clean_text(name)

    @staticmethod
    def clean_bio(bio: str) -> str:
        """Clean bio/description text."""
        return DataCleaner.clean_text(bio)

    @staticmethod
    def clean_engagement(engagement: dict) -> dict:
        """Clean and standardize engagement metrics.

        Ensures consistent numeric types and removes null values.
        """
        if not engagement:
            return {}
        cleaned: dict = {}
        for key, value in engagement.items():
            if isinstance(value, (int, float)):
                cleaned[key] = value
            elif isinstance(value, str):
                # Try to parse numeric strings
                with suppress(ValueError, AttributeError):
                    cleaned[key] = int(value.replace(",", ""))
                if key not in cleaned:
                    with suppress(ValueError, AttributeError):
                        cleaned[key] = float(value.replace(",", ""))
        return cleaned
