"""Playwright browser worker for platform adapters.

This module provides generic browser automation capabilities.
NO platform-specific logic (selectors, flows) belongs here.

Platform-specific logic (e.g., Douyin search, scroll, extract)
must live in the respective adapter (e.g., DouyinWebAdapter).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class PlaywrightBrowserWorker:
    """Generic browser worker wrapping Playwright lifecycle.

    Provides:
    - Start/stop Chromium with persistent context
    - Open URLs and get page content
    - Screenshot capability

    Reserved for future (NOT implemented in V0):
    - click, fill, scroll
    - wait_for_content, extract
    """

    def __init__(
        self,
        headless: bool = True,
        user_data_dir: str | Path | None = None,
    ) -> None:
        self._headless = headless
        self._user_data_dir = str(user_data_dir) if user_data_dir else None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._playwright = None

    @property
    def is_running(self) -> bool:
        """Check if the browser is currently running."""
        return self._browser is not None and self._browser.is_connected()

    async def start(self) -> None:
        """Start the Chromium browser with persistent context."""
        if self.is_running:
            logger.debug("Browser already running")
            return

        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        launch_args: dict = {"headless": self._headless}

        if self._user_data_dir:
            Path(self._user_data_dir).mkdir(parents=True, exist_ok=True)
            self._context = await self._playwright.chromium.launch_persistent_context(
                self._user_data_dir,
                headless=self._headless,
            )
            self._browser = self._context.browser
        else:
            self._browser = await self._playwright.chromium.launch(**launch_args)
            self._context = await self._browser.new_context()

        logger.info("Browser started (headless=%s)", self._headless)

    async def open_url(self, url: str, timeout: int = 30000) -> Page:
        """Open a URL in a new page and return it.

        Args:
            url: The URL to navigate to.
            timeout: Navigation timeout in milliseconds.

        Returns:
            The Playwright Page object.

        Raises:
            RuntimeError: If browser is not running.
        """
        if not self.is_running:
            await self.start()

        page = await self._context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        logger.debug("Opened URL: %s", url)
        return page

    async def get_page_content(self, page: Page) -> str:
        """Get the full HTML content of a page.

        Args:
            page: The Playwright Page object.

        Returns:
            The page HTML content.
        """
        return await page.content()

    async def screenshot(
        self,
        page: Page,
        path: str | Path | None = None,
    ) -> bytes:
        """Take a screenshot of the page.

        Args:
            page: The Playwright Page object.
            path: Optional file path to save the screenshot.

        Returns:
            The screenshot as bytes.
        """
        screenshot_args: dict = {"full_page": True}
        if path:
            screenshot_args["path"] = str(path)
        return await page.screenshot(**screenshot_args)

    async def stop(self) -> None:
        """Stop the browser and clean up resources."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser stopped")

    async def __aenter__(self) -> PlaywrightBrowserWorker:
        await self.start()
        return self

    async def __aexit__(self, *args) -> None:
        await self.stop()
