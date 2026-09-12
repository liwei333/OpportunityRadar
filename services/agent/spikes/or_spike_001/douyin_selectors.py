"""Douyin DOM selectors — centralized selector management.

Strategy:
1. Prefer semantic locators (role, data-e2e, href pattern)
2. Use relative DOM structure over random CSS classes
3. Multiple fallback selectors for each target
4. NO single CSS class dependency

All selectors are Douyin business logic and belong in the adapter,
NOT in the generic browser worker.
"""

from __future__ import annotations


class DouyinSelectors:
    """Centralized selector management for Douyin Web.

    Each target has a primary selector and multiple fallbacks.
    The extraction code tries each in order until one matches.
    """

    # === Login Detection ===
    LOGIN_DIALOG = [
        '[id*="login-full-panel"]',
        '[class*="login-panel"]',
        '[class*="login-dialog"]',
        '[class*="login-modal"]',
    ]

    LOGIN_CLOSE_BUTTON = [
        '[id*="login-full-panel"] [class*="close"]',
        '[class*="login-panel"] [aria-label="关闭"]',
        '[class*="login-panel"] button[class*="close"]',
    ]

    # === Verification / Captcha Detection ===
    VERIFICATION_INDICATORS = [
        "验证码中间页",
        "验证码",
        "captcha",
        "challenge",
    ]

    CAPTCHA_CONTAINER = [
        '#captcha_container',
        '[id*="captcha"]',
        '[class*="captcha"]',
        '[id*="Captcha"]',
    ]

    # === Search Page ===
    SEARCH_INPUT = [
        'input[data-e2e="searchbar-input"]',
        'input[placeholder*="搜索"]',
        'input[type="text"]',
    ]

    SEARCH_BUTTON = [
        'button[class*="search"]',
        '[data-e2e="searchbar-button"]',
        'div[class*="search-btn"]',
    ]

    SEARCH_SCROLL_CONTAINER = [
        '[data-e2e="scroll-list"]',
        '[class*="scroll-list"]',
        '[class*="search-result"]',
    ]

    # === Video Item Containers ===
    # These are used in search results and feeds
    VIDEO_ITEM_CONTAINER = [
        '[data-e2e*="video-item"]',
        '[data-e2e*="search-video"]',
        '[class*="video-card"]',
        '[class*="VideoCard"]',
        '[class*="video-item"]',
        '[class*="search-result-item"]',
        'div[class*="item"]',
        'div[class*="card"]',
    ]

    # === Video Data Fields ===
    VIDEO_TITLE = [
        '[class*="title"]',
        '[class*="desc"]',
        '[class*="description"]',
        '[class*="text-content"]',
        'span[class*="title"]',
    ]

    VIDEO_AUTHOR = [
        '[class*="author"]',
        '[class*="nickname"]',
        '[class*="name"]',
        '[class*="creator"]',
        'a[class*="author"]',
        'span[class*="author"]',
    ]

    VIDEO_LIKE_COUNT = [
        '[class*="like"]',
        '[class*="digg"]',
        '[class*="count"]',
        '[data-e2e*="like"]',
    ]

    VIDEO_COMMENT_COUNT = [
        '[class*="comment"]',
        '[data-e2e*="comment"]',
    ]

    VIDEO_VIEW_COUNT = [
        '[class*="play"]',
        '[class*="view"]',
        '[class*="watch"]',
        '[data-e2e*="play"]',
    ]

    VIDEO_PUBLISH_DATE = [
        '[class*="date"]',
        '[class*="time"]',
        '[class*="publish"]',
        'time',
    ]

    VIDEO_DURATION = [
        '[class*="duration"]',
        '[class*="length"]',
        '[data-e2e*="duration"]',
    ]

    VIDEO_LINK = [
        'a[href*="/video/"]',
        'a[href*="/note/"]',
        'a[href*="aweme"]',
    ]

    # === Account Data Fields ===
    ACCOUNT_NAME = [
        '[class*="account-name"]',
        '[class*="nickname"]',
        '[class*="author-name"]',
    ]

    ACCOUNT_PROFILE_LINK = [
        'a[href*="/user/"]',
        'a[href*="/@"]',
    ]

    ACCOUNT_BIO = [
        '[class*="bio"]',
        '[class*="signature"]',
        '[class*="intro"]',
        '[class*="description"]',
    ]

    ACCOUNT_FOLLOWER_COUNT = [
        '[class*="follower"]',
        '[class*="fans"]',
        '[data-e2e*="follower"]',
    ]

    ACCOUNT_FOLLOWING_COUNT = [
        '[class*="following"]',
        '[class*="follow"]',
    ]


class DouyinSearchDetector:
    """Pure functions for detecting search page state.

    These are separated from the extractor so they can be unit tested
    without a browser.
    """

    @staticmethod
    def is_search_results_loaded(
        search_result_cards: int,
        video_links: int,
    ) -> bool:
        """Strict detection: search results are loaded only if actual
        result cards or video links are present.

        Login overlay, captcha, and empty page shells return False.
        """
        # Must have actual search result cards
        if search_result_cards > 0:
            return True
        # Must have video links (feed mode)
        return video_links > 0

    @staticmethod
    def is_login_overlay_present(body_text: str) -> bool:
        """Check if the search page login overlay is present."""
        return "登录后即可搜索更多精彩视频" in body_text

    @staticmethod
    def is_captcha_present(captcha_elements: int) -> bool:
        """Check if a captcha overlay is blocking interaction."""
        return captcha_elements > 0


class DouyinUrls:
    """URL patterns for Douyin Web."""

    HOMEPAGE = "https://www.douyin.com/jingxuan"
    SEARCH = "https://www.douyin.com/search/{query}"
    VIDEO = "https://www.douyin.com/video/{video_id}"
    USER = "https://www.douyin.com/user/{user_id}"

    @staticmethod
    def is_verification_page(title: str) -> bool:
        """Check if the current page is a verification challenge."""
        title_lower = title.lower()
        return any(
            indicator.lower() in title_lower
            for indicator in DouyinSelectors.VERIFICATION_INDICATORS
        )

    @staticmethod
    def is_login_page(url: str, title: str) -> bool:
        """Check if the current page is a login page."""
        return (
            "login" in url.lower()
            or "passport" in url.lower()
            or "登录" in title
        )
