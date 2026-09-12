"""Explore workarounds for Douyin search login requirement.

Findings so far:
- Homepage feed: accessible without login, contains video cards
- Direct search URL: triggers verification challenge
- Homepage search box: blocked by login dialog
- Mobile site: 404

This script tries:
1. Different search URL patterns
2. Whether verification passes on its own
3. Whether video pages are accessible directly
4. Whether we can get keyword content without search

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/explore_search_workarounds.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright

QUERY = "短视频代运营"


async def explore():
    """Try various workarounds."""
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

        # Test 1: Try direct search URL and wait longer for verification to pass
        print("\n" + "=" * 60)
        print("TEST 1: Direct search URL - does verification pass on its own?")
        print("=" * 60)

        url = f"https://www.douyin.com/search/{QUERY}?type=video"
        print(f"[*] Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        for i in range(18):  # Wait up to 90 seconds
            await asyncio.sleep(5)
            title = await page.title()
            is_verify = "验证" in title or "captcha" in title.lower()
            print(f"  [{(i+1)*5}s] Title: {title} | Verify: {is_verify}")
            if not is_verify:
                print("[!] Verification passed!")
                break
        else:
            print("[!] Verification did NOT pass after 90 seconds")

        # Take screenshot
        await page.screenshot(path=str(explore_dir / "test1_verification.png"), full_page=False)

        # Test 2: Try search without type=video parameter
        print("\n" + "=" * 60)
        print("TEST 2: Search without type=video parameter")
        print("=" * 60)

        url2 = f"https://www.douyin.com/search/{QUERY}"
        print(f"[*] Navigating to: {url2}")
        await page.goto(url2, wait_until="domcontentloaded", timeout=30000)

        for i in range(6):
            await asyncio.sleep(5)
            title = await page.title()
            is_verify = "验证" in title or "captcha" in title.lower()
            print(f"  [{(i+1)*5}s] Title: {title} | Verify: {is_verify}")
            if not is_verify:
                print("[!] Verification passed!")
                break
        else:
            print("[!] Verification still present after 30 seconds")

        await page.screenshot(path=str(explore_dir / "test2_search_no_param.png"), full_page=False)

        # Test 3: Try accessing a video page directly
        print("\n" + "=" * 60)
        print("TEST 3: Direct video page access")
        print("=" * 60)

        # Try a known video URL pattern
        test_video_url = "https://www.douyin.com/video/7000000000000000000"
        print(f"[*] Navigating to: {test_video_url}")
        await page.goto(test_video_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        title = await page.title()
        current_url = page.url
        is_verify = "验证" in title or "captcha" in title.lower()
        print(f"  Title: {title}")
        print(f"  URL: {current_url}")
        print(f"  Is verification: {is_verify}")

        await page.screenshot(path=str(explore_dir / "test3_video_page.png"), full_page=False)

        # Test 4: Try user profile page
        print("\n" + "=" * 60)
        print("TEST 4: User profile page access")
        print("=" * 60)

        test_user_url = "https://www.douyin.com/user/MS4wLjABAAAA"
        print(f"[*] Navigating to: {test_user_url}")
        await page.goto(test_user_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        title = await page.title()
        is_verify = "验证" in title or "captcha" in title.lower()
        print(f"  Title: {title}")
        print(f"  Is verification: {is_verify}")

        await page.screenshot(path=str(explore_dir / "test4_user_page.png"), full_page=False)

        # Test 5: Try the "discovery" or topic pages
        print("\n" + "=" * 60)
        print("TEST 5: Topic/discovery pages")
        print("=" * 60)

        topic_urls = [
            f"https://www.douyin.com/search/{QUERY}",
            f"https://www.douyin.com/topic/{QUERY}",
            f"https://www.douyin.com/hashtag/{QUERY}",
        ]

        for url in topic_urls:
            print(f"\n  Trying: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
            title = await page.title()
            is_verify = "验证" in title or "captcha" in title.lower()
            print(f"    Title: {title} | Verify: {is_verify}")

        # Test 6: Check if login dialog can be bypassed by removing the overlay
        print("\n" + "=" * 60)
        print("TEST 6: DOM manipulation to bypass login dialog")
        print("=" * 60)

        await page.goto("https://www.douyin.com/jingxuan", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # Try to remove the login panel via JS
        result = await page.evaluate("""() => {
            const result = { removed: false };

            // Remove login panel
            const loginPanel = document.querySelector('[id*="login-full-panel"]');
            if (loginPanel) {
                loginPanel.remove();
                result.removed = true;
            }

            // Remove any overlays
            document.querySelectorAll('[class*="overlay"], [class*="mask"]').forEach(el => {
                if (el.id !== 'some-important-overlay') {
                    el.remove();
                    result.removed = true;
                }
            });

            // Remove any fixed/absolute positioned elements that might block
            document.querySelectorAll('div[style*="position: fixed"], div[style*="position:fixed"]').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.zIndex > 100) {
                    el.remove();
                    result.removed = true;
                }
            });

            return result;
        }""")

        print(f"  Removed overlays: {result['removed']}")
        await asyncio.sleep(2)

        # Now try to use the search box
        try:
            search_input = await page.query_selector('input[placeholder*="搜索"]')
            if search_input:
                await search_input.click(timeout=5000)
                await page.keyboard.type(QUERY, delay=100)
                await page.keyboard.press("Enter")
                await asyncio.sleep(8)

                title = await page.title()
                is_verify = "验证" in title or "captcha" in title.lower()
                print(f"  After DOM manipulation - Title: {title} | Verify: {is_verify}")

                await page.screenshot(path=str(explore_dir / "test6_after_dom_manipulation.png"), full_page=False)

                if not is_verify:
                    structure = await page.evaluate("""() => {
                        return {
                            title: document.title,
                            url: window.location.href,
                            textContent: document.body?.innerText?.substring(0, 2000) || '',
                            videoLinks: Array.from(document.querySelectorAll('a[href*="/video/"], a[href*="/note/"]')).map(a => ({
                                href: a.getAttribute('href'),
                                text: a.textContent?.trim().substring(0, 100),
                            })),
                        };
                    }""")
                    print(f"  Content: {structure['textContent'][:500]}")
        except Exception as e:
            print(f"  Error: {e}")

        # Keep browser open
        print("\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(explore())
