"""Douyin DOM extraction logic.

Extracts structured video and account data from Douyin pages.
Uses multi-strategy fallback for each field.

Key principle: Extract what's available. No guessing.
If a field can't be found, it stays null.

Key finding: Feed cards are DIV elements with href attributes like:
  //www.douyin.com/video/7681239375384055086
They are NOT <a> tags. The card text contains duration, view count, title, author.
"""

from __future__ import annotations

import re
from typing import Any

from playwright.async_api import Page

from .douyin_selectors import DouyinSelectors, DouyinUrls
from .models import RawAccountCandidate, RawVideoCandidate


class DouyinExtractor:
    """Extract video and account data from Douyin pages."""

    def __init__(self, page: Page) -> None:
        self._page = page

    async def extract_videos_from_feed(
        self,
        source_query: str = "",
        collection_mode: str = "feed",
        source_page_url: str = "",
    ) -> list[RawVideoCandidate]:
        """Extract video candidates from the current feed/page.

        Uses multiple strategies:
        1. Extract from search-result-card elements (search mode)
        2. Extract from feed card DIV elements with href attributes (feed mode)
        3. Parse body text for video card patterns
        4. Try structured DOM selectors

        Args:
            source_query: The search query that led to this page.
            collection_mode: "search" or "feed".
            source_page_url: The actual URL where data was extracted.

        Returns:
            List of raw video candidates extracted from the page.
        """
        videos: list[RawVideoCandidate] = []

        # Strategy 1: Extract from search-result-card elements (search mode)
        search_cards = await self._extract_from_search_cards(
            source_query, source_page_url
        )
        videos.extend(search_cards)

        # Strategy 2: Extract from feed card elements with href attributes
        if not videos:
            videos.extend(
                await self._extract_from_feed_cards(source_query)
            )

        # Strategy 3: Parse body text for video card patterns
        if not videos:
            body_text = await self._page.evaluate(
                "() => document.body?.innerText?.substring(0, 5000) || ''"
            )
            if body_text:
                videos.extend(
                    self._parse_feed_text(body_text, source_query)
                )

        # Strategy 4: Try structured DOM selectors
        if not videos:
            videos.extend(
                await self._extract_structured_videos(source_query)
            )

        return videos

    async def _extract_from_search_cards(
        self,
        source_query: str,
        source_page_url: str,
    ) -> list[RawVideoCandidate]:
        """Extract videos from search-result-card elements.

        Search result cards have the structure:
        div.search-result-card
          - text: [duration][view_count][title] [@author] · [date]

        Unlike feed cards, search cards do NOT have href attributes with video URLs.
        Video IDs are not in the DOM. We parse the text content for metadata.
        """
        videos: list[RawVideoCandidate] = []

        # Get all search-result-card elements
        cards = await self._page.evaluate("""() => {
            const cards = document.querySelectorAll('[class*="search-result-card"]');
            return Array.from(cards).map(c => c.textContent?.trim() || '');
        }""")

        for card_text in cards:
            if not card_text or len(card_text) < 20:
                continue

            video = self._parse_search_card_text(
                card_text, source_query, source_page_url
            )
            if video:
                videos.append(video)

        return videos

    def _parse_search_card_text(
        self,
        card_text: str,
        source_query: str,
        source_page_url: str,
    ) -> RawVideoCandidate | None:
        """Parse search result card text into a RawVideoCandidate.

        Search card text format (single line):
        [duration][view_count][title] [@author] · [date]

        Example:
        29:416489代运营怎么和老板谈单#短视频创作 #代运营@靳兴的运营速成指南 · 2月15日
        """
        # Parse the card content
        duration = None
        view_count = None
        title = None
        author = None
        date = None

        # Working copy of the text
        remaining = card_text.strip()

        # Extract duration: MM:SS or H:MM:SS at the start
        dur_match = re.match(r"^(\d{1,2}:\d{2}(?::\d{2})?)", remaining)
        if dur_match:
            duration = dur_match.group(1)
            remaining = remaining[dur_match.end():]

        # Extract view count: number + optional 万/w suffix
        view_match = re.match(r"([\d.]+[万w]?)", remaining)
        if view_match:
            view_count = view_match.group(1)
            remaining = remaining[view_match.end():]

        # Extract date at the end
        date_patterns = [
            r"[·\s]*(\d+月\d+日)\s*$",
            r"[·\s]*(\d+天前)\s*$",
            r"[·\s]*(\d+小时前)\s*$",
            r"[·\s]*(\d+分钟前)\s*$",
            r"[·\s]*(刚刚)\s*$",
            r"[·\s]*(\d+/\d+/\d+)\s*$",
            r"[·\s]*(\d{4}年\d+月\d+日)\s*$",
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, remaining)
            if date_match:
                date = date_match.group(1)
                remaining = remaining[:date_match.start()]
                break

        # Extract author: @username
        author_match = re.search(r"@([^\s@][^@]*?)(?:\s*$|\s*[·])", remaining)
        if not author_match:
            author_match = re.search(r"@(\S+)", remaining)
        if author_match:
            author = "@" + author_match.group(1).strip()
            remaining = remaining[:author_match.start()]

        # Whatever remains is the title
        title = remaining.strip()
        if len(title) < 3:
            title = None

        # Only create candidate if we have BOTH title and author
        # This filters out "相关搜索" sections and other non-video content
        if not title or not author:
            return None

        return RawVideoCandidate(
            title=title,
            author_name=author,
            view_count_raw=view_count,
            duration=duration,
            published_at=date,
            source_query=source_query,
            raw_text=card_text[:500],
            extraction_method="search_result_card",
            extraction_success=bool(title and author),
        )

    async def _extract_from_feed_cards(
        self,
        source_query: str,
    ) -> list[RawVideoCandidate]:
        """Extract videos from feed card elements.

        Feed cards are DIV elements with href attributes containing /video/ URLs.
        The card text contains: duration, view count, title, author, date.
        """
        videos: list[RawVideoCandidate] = []

        # Find all elements with href containing /video/
        cards = await self._page.evaluate("""() => {
            const results = [];

            // Find all elements with href containing /video/
            const allElements = document.querySelectorAll('[href*="/video/"]');

            for (const el of allElements) {
                const href = el.getAttribute('href') || '';
                const text = el.textContent?.trim() || '';

                // Skip if no meaningful text
                if (text.length < 10) continue;

                // Get the video ID from the href
                const videoIdMatch = href.match(/\\/video\\/(\\d+)/);
                const videoId = videoIdMatch ? videoIdMatch[1] : null;

                results.push({
                    href: href,
                    videoId: videoId,
                    text: text.substring(0, 500),
                    className: (el.className || '').toString().substring(0, 80),
                    tagName: el.tagName,
                });
            }

            return results;
        }""")

        for card in cards:
            video = self._parse_feed_card(card, source_query)
            if video:
                videos.append(video)

        return videos

    def _parse_feed_card(
        self,
        card: dict[str, Any],
        source_query: str,
    ) -> RawVideoCandidate | None:
        """Parse a single feed card into a RawVideoCandidate.

        Card text format (single line):
        [duration][view_count][title] [@author] · [date]

        Example:
        09:1717.5万我要爬上这座充满巨蛇的高塔！ROBLOX @麟麟七的游戏日常 · 5天前
        """
        text = card.get("text", "")
        if not text:
            return None

        # Parse the single-line card content using regex
        # Pattern: duration + view_count + title + author + date
        duration = None
        view_count = None
        title = None
        author = None
        date = None

        # Working copy of the text
        remaining = text

        # Extract duration: MM:SS or H:MM:SS at the start
        dur_match = re.match(r"^(\d{1,2}:\d{2}(?::\d{2})?)", remaining)
        if dur_match:
            duration = dur_match.group(1)
            remaining = remaining[dur_match.end():]

        # Extract view count: number + optional 万/w suffix
        view_match = re.match(r"([\d.]+[万w]?)", remaining)
        if view_match:
            view_count = view_match.group(1)
            remaining = remaining[view_match.end():]

        # Extract date at the end: · [date] or standalone date
        date_patterns = [
            r"[·\s]*(\d+月\d+日)\s*$",
            r"[·\s]*(\d+天前)\s*$",
            r"[·\s]*(\d+小时前)\s*$",
            r"[·\s]*(\d+分钟前)\s*$",
            r"[·\s]*(刚刚)\s*$",
            r"[·\s]*(\d+/\d+/\d+)\s*$",
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, remaining)
            if date_match:
                date = date_match.group(1)
                remaining = remaining[:date_match.start()]
                break

        # Extract author: @username (may contain spaces, ends before date or end)
        author_match = re.search(r"@([^\s@][^@]*?)(?:\s*$|\s*[·])", remaining)
        if not author_match:
            # Try simpler pattern: @ followed by non-space chars
            author_match = re.search(r"@(\S+)", remaining)
        if author_match:
            author = "@" + author_match.group(1).strip()
            remaining = remaining[:author_match.start()]

        # Whatever remains is the title
        title = remaining.strip()
        if len(title) < 3:
            title = None

        # Build video URL from ID
        video_id = card.get("videoId")
        video_url = None
        if video_id:
            video_url = f"https://www.douyin.com/video/{video_id}"

        # Only create candidate if we have meaningful data
        if not (title or author or video_id):
            return None

        return RawVideoCandidate(
            video_id=video_id,
            video_url=video_url,
            title=title,
            author_name=author,
            view_count_raw=view_count,
            duration=duration,
            published_at=date,
            source_query=source_query,
            raw_text=text[:500],
            extraction_method="feed_card_href",
            extraction_success=bool(title and author),
        )

    def _parse_feed_text(
        self,
        body_text: str,
        source_query: str,
    ) -> list[RawVideoCandidate]:
        """Parse video data from feed text content.

        The Douyin homepage feed shows videos in a pattern like:
        [duration]
        [view_count]
        [title/text]
        [@author]
        · [date]

        This parser identifies these patterns and extracts structured data.
        """
        videos: list[RawVideoCandidate] = []
        lines = [line.strip() for line in body_text.split("\n") if line.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Look for a duration pattern (MM:SS or H:MM:SS)
            duration_match = re.match(
                r"^(\d{1,2}:\d{2}(?::\d{2})?)$", line
            )

            if duration_match and i + 1 < len(lines):
                duration = duration_match.group(1)

                # Next line might be view count
                view_count = None
                j = i + 1

                # Check if next line is a view count
                if j < len(lines):
                    view_match = re.match(
                        r"^([\d.]+[万w]?)$", lines[j]
                    )
                    if view_match:
                        view_count = view_match.group(1)
                        j += 1

                # The line after duration/views is likely the title
                title = None
                if j < len(lines):
                    candidate = lines[j]
                    # Skip if it's just a number or too short
                    if len(candidate) > 3 and not re.match(r"^[\d.]+[万w]?$", candidate):
                        title = candidate
                        j += 1

                # Look for author (starts with @)
                author = None
                if j < len(lines):
                    author_match = re.match(
                        r"^@([^\s·]+)", lines[j]
                    )
                    if author_match:
                        author = "@" + author_match.group(1)
                        j += 1

                # Look for date
                date = None
                if j < len(lines):
                    date_match = re.match(
                        r"^[·\s]*(\d+月\d+日|\d+天前|\d+小时前|\d+分钟前|刚刚|\d+/\d+/\d+)",
                        lines[j],
                    )
                    if date_match:
                        date = date_match.group(1)
                        j += 1

                # Only create a candidate if we have at least title or author
                if title or author:
                    video = RawVideoCandidate(
                        title=title,
                        author_name=author,
                        view_count_raw=view_count,
                        duration=duration,
                        published_at=date,
                        source_query=source_query,
                        raw_text="\n".join(lines[i:j]),
                        extraction_method="feed_text_parse",
                        extraction_success=bool(title and author),
                    )
                    videos.append(video)

                i = j
            else:
                i += 1

        return videos

    async def _extract_structured_videos(
        self,
        source_query: str,
    ) -> list[RawVideoCandidate]:
        """Extract videos using structured DOM selectors."""
        videos: list[RawVideoCandidate] = []

        # Try to find video item containers
        for selector in DouyinSelectors.VIDEO_ITEM_CONTAINER:
            elements = await self._page.query_selector_all(selector)
            if elements:
                for el in elements[:50]:  # Limit to 50 per selector
                    video = await self._extract_single_video(el, source_query)
                    if video and (video.title or video.author_name):
                        videos.append(video)

                if videos:
                    break  # Found videos with this selector

        return videos

    async def _extract_single_video(
        self,
        element: Any,
        source_query: str,
    ) -> RawVideoCandidate | None:
        """Extract data from a single video element."""
        data = await element.evaluate("""(el) => {
            const result = {
                title: null,
                author: null,
                likeCount: null,
                commentCount: null,
                viewCount: null,
                date: null,
                duration: null,
                videoUrl: null,
                authorUrl: null,
                textContent: '',
            };

            // Get all text content
            result.textContent = el.innerText?.substring(0, 500) || '';

            // Try to find video link
            const videoLink = el.querySelector('a[href*="/video/"], a[href*="/note/"]');
            if (videoLink) {
                result.videoUrl = videoLink.getAttribute('href');
            }

            // Try to find author link
            const authorLink = el.querySelector('a[href*="/user/"]');
            if (authorLink) {
                result.authorUrl = authorLink.getAttribute('href');
                result.author = authorLink.textContent?.trim();
            }

            return result;
        }""")

        if not data or not data.get("textContent"):
            return None

        return RawVideoCandidate(
            title=data.get("title"),
            author_name=data.get("author"),
            like_count_raw=data.get("likeCount"),
            comment_count_raw=data.get("commentCount"),
            view_count_raw=data.get("viewCount"),
            published_at=data.get("date"),
            duration=data.get("duration"),
            video_url=data.get("videoUrl"),
            author_profile_url=data.get("authorUrl"),
            source_query=source_query,
            raw_text=data.get("textContent", ""),
            extraction_method="structured_dom",
            extraction_success=bool(data.get("title") or data.get("author")),
        )

    async def extract_accounts_from_videos(
        self,
        videos: list[RawVideoCandidate],
    ) -> list[RawAccountCandidate]:
        """Extract unique accounts from video candidates.

        Groups videos by author and creates account candidates.
        Preserves source_queries for cross-query merging.
        """
        accounts: dict[str, RawAccountCandidate] = {}

        for video in videos:
            if not video.author_name:
                continue

            # Use author name as dedup key (best effort)
            key = video.author_name.strip()

            if key in accounts:
                # Merge source queries
                if video.source_query and video.source_query not in accounts[key].source_queries:
                    accounts[key].source_queries.append(video.source_query)
                accounts[key].content_hits += 1
            else:
                accounts[key] = RawAccountCandidate(
                    account_name=video.author_name,
                    profile_url=video.author_profile_url,
                    source_queries=[video.source_query] if video.source_query else [],
                    content_hits=1,
                    raw_text=video.raw_text,
                )

        return list(accounts.values())

    async def check_login_required(self) -> bool:
        """Check if the page is showing a login dialog or overlay."""
        # Check standard login dialog selectors
        for selector in DouyinSelectors.LOGIN_DIALOG:
            try:
                element = await self._page.query_selector(selector)
                if element and await element.is_visible():
                    return True
            except Exception:
                continue

        # Check for search page login overlay (z-index 9999, text-based)
        try:
            body_text = await self._page.evaluate("() => document.body?.innerText || ''")
            if "登录后即可搜索更多精彩视频" in body_text:
                return True
        except Exception:
            pass

        return False

    async def check_verification_required(self) -> bool:
        """Check if the page is showing a verification challenge."""
        title = await self._page.title()
        if DouyinUrls.is_verification_page(title):
            return True

        # Also check for captcha container
        for selector in DouyinSelectors.CAPTCHA_CONTAINER:
            try:
                element = await self._page.query_selector(selector)
                if element and await element.is_visible():
                    return True
            except Exception:
                continue
        return False

    async def check_captcha_required(self) -> bool:
        """Check if a captcha overlay is blocking interaction."""
        for selector in DouyinSelectors.CAPTCHA_CONTAINER:
            try:
                element = await self._page.query_selector(selector)
                if element and await element.is_visible():
                    return True
            except Exception:
                continue
        return False

    async def wait_for_captcha(self, timeout_ms: int = 180000) -> bool:
        """Wait for user to solve captcha challenge.

        Args:
            timeout_ms: Maximum time to wait in milliseconds.

        Returns:
            True if captcha was solved, False if timed out.
        """
        import asyncio
        import time

        print("\n" + "=" * 60)
        print("CAPTCHA REQUIRED")
        print("=" * 60)
        print("Douyin is showing a captcha challenge.")
        print("Please solve it in the browser window.")
        print(f"Waiting up to {timeout_ms // 1000} seconds...")
        print("=" * 60 + "\n")

        start = time.time()
        while (time.time() - start) * 1000 < timeout_ms:
            if not await self.check_captcha_required():
                print("[!] Captcha solved, continuing...")
                return True
            await asyncio.sleep(3)

        print("[!] Captcha wait timed out.")
        return False

    async def wait_for_login(self, timeout_ms: int = 180000) -> bool:
        """Wait for user to complete login.

        Prints a clear message and waits for the login dialog/overlay to disappear.

        Args:
            timeout_ms: Maximum time to wait in milliseconds.

        Returns:
            True if login was completed, False if timed out.
        """
        import asyncio
        import time

        print("\n" + "=" * 60)
        print("LOGIN REQUIRED")
        print("=" * 60)
        print("Douyin requires login to access search results.")
        print("Please complete login in the browser window.")
        print("(扫码登录 / 验证码登录 / 密码登录)")
        print(f"Waiting up to {timeout_ms // 1000} seconds...")
        print("=" * 60 + "\n")

        start = time.time()
        while (time.time() - start) * 1000 < timeout_ms:
            # Check if login overlay is gone AND results are loading
            login_gone = not await self.check_login_required()
            captcha_gone = not await self.check_captcha_required()

            if login_gone and captcha_gone:
                # Double check by looking for results or absence of login text
                body_text = await self._page.evaluate("() => document.body?.innerText || ''")
                if "登录后即可搜索更多精彩视频" not in body_text:
                    print("[!] Login completed, continuing...")
                    return True

            await asyncio.sleep(3)

        print("[!] Login wait timed out.")
        return False

    async def wait_for_verification(self, timeout_ms: int = 120000) -> bool:
        """Wait for user to solve verification challenge.

        Args:
            timeout_ms: Maximum time to wait in milliseconds.

        Returns:
            True if verification was solved, False if timed out.
        """
        import asyncio
        import time

        print("\n" + "=" * 60)
        print("VERIFICATION REQUIRED")
        print("=" * 60)
        print("Douyin is showing a verification challenge.")
        print("Please solve it in the browser window.")
        print(f"Waiting up to {timeout_ms // 1000} seconds...")
        print("=" * 60 + "\n")

        start = time.time()
        while (time.time() - start) * 1000 < timeout_ms:
            if not await self.check_verification_required() and not await self.check_login_required():
                print("[!] Verification solved, continuing...")
                return True
            await asyncio.sleep(3)

        print("[!] Verification wait timed out.")
        return False
