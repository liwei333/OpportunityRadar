"""Explore Douyin search API calls and dynamic content loading.

The search page is a Next.js app that loads results via client-side API.
This script:
1. Intercepts network requests to find the search API
2. Waits for content to load dynamically
3. Explores the rendered DOM after JS execution

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/explore_search_api.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright

QUERY = "短视频代运营"
API_REQUESTS = []


async def handle_route(route):
    """Intercept API requests."""
    url = route.request.url
    if "/api/" in url or "/web/" in url or "search" in url.lower():
        API_REQUESTS.append({
            "url": url[:300],
            "method": route.request.method,
            "headers": dict(route.request.headers),
        })
    await route.continue_()


async def explore():
    """Explore search API and dynamic content."""
    profile_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "browser_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    explore_dir = Path(__file__).resolve().parent / "_explore"
    explore_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        print("[*] Launching Chromium (headed mode)")
        context = await p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Intercept network requests
        await page.route("**/*", handle_route)

        # Navigate to search page
        url = f"https://www.douyin.com/search/{QUERY}"
        print(f"[*] Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Wait for network to be idle
        print("[*] Waiting for network idle...")
        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
            print("  Network idle reached")
        except Exception as e:
            print(f"  Network idle timeout: {e}")

        # Wait extra time for rendering
        print("[*] Waiting 10 seconds for rendering...")
        await asyncio.sleep(10)

        # Report API requests
        print(f"\n[*] API requests captured: {len(API_REQUESTS)}")
        for req in API_REQUESTS[:20]:
            print(f"  {req['method']} {req['url'][:100]}")

        # Take screenshot
        await page.screenshot(path=str(explore_dir / "search_after_idle.png"), full_page=False)

        # Check if content has loaded
        print("\n" + "=" * 60)
        print("CHECKING FOR LOADED CONTENT")
        print("=" * 60)

        content_check = await page.evaluate("""() => {
            const result = {
                scrollListChildren: 0,
                videoLinksCount: 0,
                allLinksCount: 0,
                documentHeight: document.documentElement.scrollHeight,
                bodyText: '',
                hasVideoCards: false,
                sampleVideoCards: [],
            };

            // Check scroll list
            const scrollList = document.querySelector('[data-e2e="scroll-list"]');
            if (scrollList) {
                result.scrollListChildren = scrollList.children.length;
                result.scrollListHTML = scrollList.outerHTML.substring(0, 1000);
            }

            // Check video links
            const videoLinks = document.querySelectorAll('a[href*="/video/"], a[href*="/note/"]');
            result.videoLinksCount = videoLinks.length;

            // All links
            result.allLinksCount = document.querySelectorAll('a[href]').length;

            // Body text
            result.bodyText = document.body?.innerText?.substring(0, 2000) || '';

            // Check for video card patterns
            const cardSelectors = [
                '[class*="video-card"]',
                '[class*="VideoCard"]',
                '[class*="video-card"]',
                '[class*="search-video"]',
                '[class*="video-item"]',
                '[class*="VideoItem"]',
            ];

            for (const sel of cardSelectors) {
                const els = document.querySelectorAll(sel);
                if (els.length > 0) {
                    result.hasVideoCards = true;
                    result.sampleVideoCards.push({
                        selector: sel,
                        count: els.length,
                        firstHTML: els[0].outerHTML.substring(0, 400),
                    });
                }
            }

            return result;
        }""")

        print(f"  Scroll list children: {content_check['scrollListChildren']}")
        print(f"  Video links: {content_check['videoLinksCount']}")
        print(f"  All links: {content_check['allLinksCount']}")
        print(f"  Document height: {content_check['documentHeight']}")
        print(f"  Has video cards: {content_check['hasVideoCards']}")
        print(f"  Body text preview: {content_check['bodyText'][:500]}")

        if content_check.get('scrollListHTML'):
            print(f"  Scroll list HTML: {content_check['scrollListHTML'][:500]}")

        # Try scrolling
        print("\n" + "=" * 60)
        print("SCROLLING TEST")
        print("=" * 60)

        for i in range(5):
            await page.evaluate("window.scrollBy(0, 600)")
            await asyncio.sleep(2)

            counts = await page.evaluate("""() => {
                return {
                    videoLinks: document.querySelectorAll('a[href*="/video/"], a[href*="/note/"]').length,
                    docHeight: document.documentElement.scrollHeight,
                    scrollListChildren: document.querySelector('[data-e2e="scroll-list"]')?.children.length || 0,
                };
            }""")
            print(f"  Scroll {i+1}: videoLinks={counts['videoLinks']}, docHeight={counts['docHeight']}, scrollListChildren={counts['scrollListChildren']}")

        # Try waiting for a specific selector
        print("\n" + "=" * 60)
        print("WAITING FOR VIDEO CONTENT")
        print("=" * 60)

        try:
            # Wait for any video-related content to appear
            await page.wait_for_selector('a[href*="/video/"], a[href*="/note/"]', timeout=15000)
            print("  Video links appeared!")
        except Exception:
            print("  No video links appeared after 15 seconds")

        # Final state
        final_check = await page.evaluate("""() => {
            return {
                videoLinks: document.querySelectorAll('a[href*="/video/"], a[href*="/note/"]').length,
                allLinks: Array.from(document.querySelectorAll('a[href]')).slice(0, 30).map(a => ({
                    href: a.getAttribute('href'),
                    text: a.textContent?.trim().substring(0, 80),
                })),
                textContent: document.body?.innerText?.substring(0, 2000) || '',
            };
        }""")

        print(f"\n  Final video links: {final_check['videoLinks']}")
        print("  All links sample:")
        for link in final_check['allLinks'][:20]:
            print(f"    {link['href'][:80]} | {link['text'][:40]}")

        # Save results
        results = {
            "api_requests": API_REQUESTS,
            "content_check": content_check,
            "final_check": final_check,
        }

        results_file = explore_dir / "search_api_analysis.json"
        results_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[*] Results saved: {results_file}")

        # Keep browser open
        print("\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(explore())
