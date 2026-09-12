"""Try homepage first, then search.

Sometimes visiting the homepage first establishes a session that
allows search results to render without login.

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/diagnose_home_then_search.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright


QUERY = "短视频代运营"
PROFILE_DIR = Path("data/browser_profile/douyin-spike-001-fresh")


async def diagnose():
    """Homepage first, then search."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    explore_dir = Path(__file__).resolve().parent / "_diagnose"
    explore_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        print("[*] Launching Chromium (fresh profile)")
        context = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Step 1: Visit homepage first
        print("[*] Step 1: Visiting homepage to establish session...")
        await page.goto("https://www.douyin.com/jingxuan", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(8)

        # Check homepage state
        home_title = await page.title()
        home_login = await page.evaluate("""() => {
            const text = document.body?.innerText || '';
            return text.includes('登录后即可搜索更多精彩视频') || text.includes('扫码登录');
        }""")
        print(f"  Homepage title: {home_title}")
        print(f"  Homepage login visible: {home_login}")

        # Step 2: Navigate to search
        print(f"\n[*] Step 2: Navigating to search: {QUERY}")
        search_url = f"https://www.douyin.com/search/{QUERY}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(10)

        # Check search state
        search_title = await page.title()
        search_body = await page.evaluate("""() => {
            const text = document.body?.innerText || '';
            return {
                title: document.title,
                hasLoginOverlay: text.includes('登录后即可搜索更多精彩视频'),
                hasScanLogin: text.includes('扫码登录'),
                videoLinks: document.querySelectorAll('[href*="/video/"]').length,
                searchCards: document.querySelectorAll('[class*="search-result-card"]').length,
                bodyLen: text.length,
                bodySample: text.substring(0, 1500),
            };
        }""")

        print(f"\n  Search title: {search_title}")
        print(f"  Login overlay: {search_body['hasLoginOverlay']}")
        print(f"  Video links: {search_body['videoLinks']}")
        print(f"  Search cards: {search_body['searchCards']}")
        print(f"  Body length: {search_body['bodyLen']}")

        if search_body['searchCards'] > 0:
            print(f"\n[!] SUCCESS! Search results rendered!")
            print(f"Body sample: {search_body['bodySample'][:500]}")
        elif search_body['hasLoginOverlay']:
            print(f"\n[!] Login overlay detected. Waiting for user to login...")
            print("Please complete login in the browser window.")
            print("Waiting 120 seconds...")

            start = time.time()
            while (time.time() - start) < 120:
                await asyncio.sleep(5)
                state = await page.evaluate("""() => {
                    const text = document.body?.innerText || '';
                    return {
                        hasLogin: text.includes('登录后即可搜索更多精彩视频'),
                        cards: document.querySelectorAll('[class*="search-result-card"]').length,
                        videoLinks: document.querySelectorAll('[href*="/video/"]').length,
                    };
                }""")
                elapsed = int(time.time() - start)
                print(f"  [{elapsed}s] login={state['hasLogin']}, cards={state['cards']}, videos={state['videoLinks']}")

                if not state['hasLogin'] or state['cards'] > 0:
                    print("[!] Login cleared or results appeared!")
                    break
            else:
                print("[!] Timed out")

        # Screenshot
        await page.screenshot(path=str(explore_dir / "home_then_search.png"), full_page=False)

        # Keep browser open
        print(f"\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(diagnose())
