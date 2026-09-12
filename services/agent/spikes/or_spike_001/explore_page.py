"""Douyin search page structure exploration script.

Opens a real Douyin search page and dumps the DOM structure
to understand how to extract video and account data.

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/explore_page.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import contextlib

from playwright.async_api import async_playwright

SEARCH_URL_TEMPLATE = "https://www.douyin.com/search/{query}?type=video"
QUERY = "短视频代运营"


async def explore():
    """Open Douyin search page and explore its structure."""
    async with async_playwright() as p:
        # Use persistent context with a dedicated profile
        profile_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "browser_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        print(f"[*] Launching Chromium (headed mode, profile: {profile_dir})")
        print("[*] If not logged in, please login in the browser window...")

        context = await p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )

        page = context.pages[0] if context.pages else await context.new_page()

        url = SEARCH_URL_TEMPLATE.format(query=QUERY)
        print(f"[*] Navigating to: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        print("[*] Waiting 8 seconds for initial render...")
        await asyncio.sleep(8)

        # Take screenshot
        screenshot_dir = Path(__file__).resolve().parent / "_explore"
        screenshot_dir.mkdir(exist_ok=True)
        await page.screenshot(path=str(screenshot_dir / "page_initial.png"), full_page=False)
        print(f"[*] Screenshot saved: {screenshot_dir / 'page_initial.png'}")

        # Dump page title and URL
        title = await page.title()
        current_url = page.url
        print(f"[*] Page title: {title}")
        print(f"[*] Current URL: {current_url}")

        # Explore the page structure
        print("\n" + "=" * 80)
        print("EXPLORING PAGE STRUCTURE")
        print("=" * 80)

        # Check if there's a search results container
        structure = await page.evaluate("""() => {
            const result = {
                title: document.title,
                url: window.location.href,
                bodyClasses: document.body.className,
                searchInputs: [],
                videoItems: [],
                resultContainers: [],
                allRoles: {},
                linksWithVideo: [],
            };

            // Find search inputs
            const inputs = document.querySelectorAll('input');
            inputs.forEach((el, i) => {
                result.searchInputs.push({
                    index: i,
                    type: el.type,
                    placeholder: el.placeholder,
                    className: el.className.substring(0, 100),
                    id: el.id,
                    name: el.name,
                    value: el.value,
                    role: el.getAttribute('role'),
                    ariaLabel: el.getAttribute('aria-label'),
                });
            });

            // Find elements with role attributes
            document.querySelectorAll('[role]').forEach(el => {
                const role = el.getAttribute('role');
                if (!result.allRoles[role]) result.allRoles[role] = 0;
                result.allRoles[role]++;
            });

            // Find links that look like video links
            document.querySelectorAll('a[href]').forEach(el => {
                const href = el.getAttribute('href') || '';
                if (href.includes('/video/') || href.includes('note/')) {
                    result.linksWithVideo.push({
                        href: href.substring(0, 200),
                        text: el.textContent?.trim().substring(0, 100) || '',
                        parentTag: el.parentElement?.tagName,
                        parentClass: (el.parentElement?.className || '').toString().substring(0, 80),
                    });
                }
            });

            // Find common video container patterns
            const containerSelectors = [
                '[data-e2e="search-result-container"]',
                '[data-e2e="scroll-list"]',
                '[class*="search-result"]',
                '[class*="video-list"]',
                '[class*="scroll-list"]',
                '[class*="content-list"]',
                'ul[class*="list"]',
                'div[class*="Item"]',
            ];

            containerSelectors.forEach(sel => {
                const els = document.querySelectorAll(sel);
                if (els.length > 0) {
                    result.resultContainers.push({
                        selector: sel,
                        count: els.length,
                        firstClass: (els[0].className || '').toString().substring(0, 100),
                        childCount: els[0].children.length,
                    });
                }
            });

            // Find video-item-like structures
            const itemPatterns = [
                'div[class*="video"]',
                'div[class*="Video"]',
                'div[class*="item"]',
                'div[class*="Item"]',
                'div[class*="card"]',
                'div[class*="Card"]',
                'li[class*="item"]',
                'div[data-e2e*="video"]',
                'div[data-e2e*="search"]',
            ];

            itemPatterns.forEach(sel => {
                const els = document.querySelectorAll(sel);
                if (els.length > 0) {
                    result.videoItems.push({
                        selector: sel,
                        count: els.length,
                        sampleClass: (els[0].className || '').toString().substring(0, 100),
                        sampleText: els[0].textContent?.trim().substring(0, 200) || '',
                        sampleHTML: els[0].outerHTML.substring(0, 500),
                    });
                }
            });

            return result;
        }""")

        print(json.dumps(structure, ensure_ascii=False, indent=2))

        # Save full structure to file
        explore_file = screenshot_dir / "structure.json"
        explore_file.write_text(json.dumps(structure, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[*] Full structure saved: {explore_file}")

        # Now scroll and observe
        print("\n" + "=" * 80)
        print("SCROLLING TO OBSERVE DYNAMIC LOADING")
        print("=" * 80)

        for i in range(3):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(3)
            await page.screenshot(path=str(screenshot_dir / f"scroll_{i+1}.png"), full_page=False)
            print(f"[*] Scroll {i+1}/3 done, screenshot saved")

        # Final DOM snapshot
        final_html = await page.content()
        html_file = screenshot_dir / "page.html"
        html_file.write_text(final_html, encoding="utf-8")
        print(f"[*] Full HTML saved: {html_file} ({len(final_html)} chars)")

        print("\n[*] Exploration complete.")
        print("[*] Close the browser window or press Ctrl+C to exit.")
        print("[*] Keeping browser open for 30 seconds for manual inspection...")

        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.sleep(30)

        await context.close()


if __name__ == "__main__":
    asyncio.run(explore())
