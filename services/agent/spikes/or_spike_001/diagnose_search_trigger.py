"""Diagnose what triggers search results to load.

Sometimes search results don't render. This script tests:
1. Waiting longer
2. Scrolling
3. Clicking tabs
4. Checking network requests

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/diagnose_search_trigger.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright


QUERY = "短视频代运营"
PROFILE_DIR = Path("data/browser_profile/douyin-spike-001")


async def diagnose():
    """Test what triggers search results."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    explore_dir = Path(__file__).resolve().parent / "_diagnose"
    explore_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        print("[*] Launching Chromium")
        context = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Track API calls
        search_api_calls = []

        async def handle_response(response):
            url = response.url
            if "search" in url.lower() and "aweme" in url.lower():
                if not any(ext in url for ext in [".js", ".css", ".woff", ".png", ".jpg", ".svg"]):
                    try:
                        body = await response.text()
                        search_api_calls.append({
                            "url": url[:200],
                            "status": response.status,
                            "bodyLen": len(body),
                            "hasVideoData": "aweme_id" in body or "video_id" in body or "/video/" in body,
                        })
                    except Exception:
                        pass

        page.on("response", handle_response)

        url = f"https://www.douyin.com/search/{QUERY}"
        print(f"[*] Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Test 1: Wait and check periodically
        print("\n--- Test 1: Periodic checking ---")
        for wait_time in [5, 10, 15, 20, 30]:
            await asyncio.sleep(5 if wait_time == 5 else 5)
            cards = await page.query_selector_all('[class*="search-result-card"]')
            body_len = await page.evaluate("() => (document.body?.innerText || '').length")
            print(f"  After {wait_time}s: {len(cards)} cards, bodyLen={body_len}")

            if cards:
                print(f"[!] Results appeared at {wait_time}s!")
                break

        # Test 2: Scroll to trigger loading
        if not cards:
            print("\n--- Test 2: Scroll to trigger ---")
            for i in range(5):
                await page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(2)
                cards = await page.query_selector_all('[class*="search-result-card"]')
                print(f"  Scroll {i+1}: {len(cards)} cards")
                if cards:
                    break

        # Test 3: Click on tabs (综合/视频/用户)
        if not cards:
            print("\n--- Test 3: Click tabs ---")
            tabs = await page.query_selector_all('[role="tab"]')
            print(f"  Found {len(tabs)} tabs")
            for i, tab in enumerate(tabs):
                tab_text = await tab.evaluate("el => el.textContent?.trim()")
                print(f"  Tab {i}: {tab_text}")
                if tab_text == "视频":
                    await tab.click()
                    await asyncio.sleep(5)
                    cards = await page.query_selector_all('[class*="search-result-card"]')
                    print(f"  After clicking '视频': {len(cards)} cards")
                    if cards:
                        break

        # Test 4: Check search input and submit
        if not cards:
            print("\n--- Test 4: Search input ---")
            search_input = await page.query_selector('input[data-e2e="searchbar-input"]')
            if search_input:
                # Get current value
                value = await search_input.evaluate("el => el.value")
                print(f"  Search input value: {value}")

                # Clear and type
                await search_input.click()
                await search_input.fill(QUERY)
                await page.keyboard.press("Enter")
                await asyncio.sleep(8)

                cards = await page.query_selector_all('[class*="search-result-card"]')
                print(f"  After search submit: {len(cards)} cards")

        # Report API calls
        print(f"\n--- Search API Calls: {len(search_api_calls)} ---")
        for call in search_api_calls:
            print(f"  {call['status']} {call['url'][:100]} (hasVideoData={call['hasVideoData']})")

        # Screenshot
        await page.screenshot(path=str(explore_dir / "search_trigger.png"), full_page=False)

        # Keep browser open
        print(f"\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(diagnose())
