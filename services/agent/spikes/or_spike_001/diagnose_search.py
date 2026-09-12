"""Diagnose Douyin search page state.

Navigates to a search page and dumps detailed diagnostics:
- Page title and URL
- Login dialog detection
- Verification detection
- Video elements found
- DOM structure
- Screenshot

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/diagnose_search.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright


QUERY = "短视频代运营"
PROFILE_DIR = Path("data/browser_profile/douyin-spike-001")


async def diagnose():
    """Run diagnostics on search page."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    explore_dir = Path(__file__).resolve().parent / "_diagnose"
    explore_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        print("[*] Launching Chromium (headed mode, fresh profile)")
        context = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to search
        url = f"https://www.douyin.com/search/{QUERY}"
        print(f"[*] Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Wait for initial render
        print("[*] Waiting 8 seconds for initial render...")
        await asyncio.sleep(8)

        # Diagnostics
        title = await page.title()
        current_url = page.url
        print(f"\n{'='*60}")
        print("DIAGNOSTICS")
        print(f"{'='*60}")
        print(f"Title: {title}")
        print(f"URL: {current_url}")

        # Check for login dialog
        login_dialog = await page.query_selector('[id*="login-full-panel"]')
        login_visible = await login_dialog.is_visible() if login_dialog else False
        print(f"Login dialog visible: {login_visible}")

        # Check for verification
        is_verify = "验证" in title or "captcha" in title.lower()
        print(f"Is verification page: {is_verify}")

        # Take screenshot
        await page.screenshot(path=str(explore_dir / "search_page.png"), full_page=False)
        print(f"Screenshot saved: {explore_dir / 'search_page.png'}")

        # Check for video elements
        print(f"\n{'='*60}")
        print("ELEMENT ANALYSIS")
        print(f"{'='*60}")

        element_counts = await page.evaluate("""() => {
            const result = {
                // Links
                linksWithVideoHref: document.querySelectorAll('[href*="/video/"]').length,
                linksWithVideoA: document.querySelectorAll('a[href*="/video/"]').length,
                linksWithNote: document.querySelectorAll('[href*="/note/"]').length,
                allLinks: document.querySelectorAll('a[href]').length,

                // Data attributes
                scrollList: document.querySelectorAll('[data-e2e="scroll-list"]').length,
                searchResult: document.querySelectorAll('[data-e2e*="search"]').length,
                videoItems: document.querySelectorAll('[data-e2e*="video"]').length,
                searchbarInput: document.querySelectorAll('[data-e2e="searchbar-input"]').length,

                // Classes
                videoCards: document.querySelectorAll('[class*="video-card"]').length,
                searchResults: document.querySelectorAll('[class*="search-result"]').length,
                resultItems: document.querySelectorAll('[class*="result-item"]').length,

                // Text content
                bodyTextLength: (document.body?.innerText || '').length,
                bodyTextSample: (document.body?.innerText || '').substring(0, 1000),

                // Document
                docHeight: document.documentElement.scrollHeight,
                windowHeight: window.innerHeight,
            };

            // Sample href values
            const videoHrefs = document.querySelectorAll('[href*="/video/"]');
            result.sampleVideoHrefs = Array.from(videoHrefs).slice(0, 5).map(el => ({
                href: el.getAttribute('href'),
                tag: el.tagName,
                text: el.textContent?.trim().substring(0, 80),
            }));

            // Sample link hrefs
            const allLinks = document.querySelectorAll('a[href]');
            result.sampleLinks = Array.from(allLinks).slice(0, 10).map(el => ({
                href: el.getAttribute('href'),
                text: el.textContent?.trim().substring(0, 50),
            }));

            return result;
        }""")

        print(json.dumps(element_counts, ensure_ascii=False, indent=2))

        # Check if there's content but our selectors miss it
        print(f"\n{'='*60}")
        print("CONTENT ANALYSIS")
        print(f"{'='*60}")

        # Look for any elements that might contain video data
        content_analysis = await page.evaluate("""() => {
            const result = {
                // Look for aweme IDs (19-digit numbers) in the DOM
                awemeIds: [],
                // Look for any clickable cards
                clickableCards: [],
                // Look for role attributes
                roles: {},
            };

            // Find all 19-digit numbers (aweme IDs)
            const allText = document.body?.innerText || '';
            const idMatches = allText.match(/\\b\\d{19}\\b/g);
            if (idMatches) {
                result.awemeIds = [...new Set(idMatches)].slice(0, 10);
            }

            // Check roles
            document.querySelectorAll('[role]').forEach(el => {
                const role = el.getAttribute('role');
                if (!result.roles[role]) result.roles[role] = 0;
                result.roles[role]++;
            });

            // Look for clickable divs with video-like content
            document.querySelectorAll('div').forEach(el => {
                const text = el.textContent?.trim() || '';
                if (text.includes('@') && text.length > 20 && text.length < 500) {
                    const href = el.getAttribute('href');
                    if (href && href.includes('/video/')) {
                        result.clickableCards.push({
                            href: href,
                            text: text.substring(0, 100),
                        });
                    }
                }
            });

            return result;
        }""")

        print(json.dumps(content_analysis, ensure_ascii=False, indent=2))

        # Wait for user to login if needed
        if login_visible or is_verify:
            print(f"\n{'='*60}")
            print("LOGIN/VERIFICATION REQUIRED")
            print(f"{'='*60}")
            print("Please complete login in the browser window.")
            print("Waiting 120 seconds...")

            import time
            start = time.time()
            while (time.time() - start) < 120:
                await asyncio.sleep(5)
                title = await page.title()
                login_dialog = await page.query_selector('[id*="login-full-panel"]')
                login_visible = await login_dialog.is_visible() if login_dialog else False
                is_verify = "验证" in title

                print(f"  [{int(time.time()-start)}s] title={title}, login={login_visible}, verify={is_verify}")

                if not login_visible and not is_verify:
                    print("[!] Login/verification cleared!")
                    break
            else:
                print("[!] Timed out waiting for login")

            # After login, wait for content
            print("[*] Waiting 10 seconds for content to load...")
            await asyncio.sleep(10)

            # Re-check
            post_login = await page.evaluate("""() => {
                return {
                    title: document.title,
                    url: window.location.href,
                    videoHrefs: document.querySelectorAll('[href*="/video/"]').length,
                    bodyText: (document.body?.innerText || '').substring(0, 500),
                    docHeight: document.documentElement.scrollHeight,
                };
            }""")
            print(f"\nPost-login state:")
            print(json.dumps(post_login, ensure_ascii=False, indent=2))

            await page.screenshot(path=str(explore_dir / "post_login.png"), full_page=False)

        # Keep browser open for inspection
        print(f"\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(diagnose())
