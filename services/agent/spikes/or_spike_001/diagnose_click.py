"""Click on search result cards to get video URLs.

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/diagnose_click.py
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
    """Click cards to get video URLs."""
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

        url = f"https://www.douyin.com/search/{QUERY}"
        print(f"[*] Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(12)

        # Check if results are loaded
        cards = await page.query_selector_all('[class*="search-result-card"]')
        print(f"Found {len(cards)} search result cards")

        if not cards:
            print("[!] No cards found. Dumping page state...")
            text = await page.evaluate("() => document.body?.innerText?.substring(0, 500)")
            print(f"Page text: {text}")
            await page.screenshot(path=str(explore_dir / "no_cards.png"), full_page=False)
            await asyncio.sleep(10)
            await context.close()
            return

        # Try clicking each of the first 3 cards
        for i in range(min(3, len(cards))):
            print(f"\n--- Card {i+1} ---")

            # Re-find cards (DOM may have changed)
            cards = await page.query_selector_all('[class*="search-result-card"]')
            if i >= len(cards):
                break

            card = cards[i]
            text = await card.evaluate("el => el.textContent?.trim().substring(0, 100)")
            print(f"Text: {text}")

            # Click
            before_url = page.url
            print(f"Before: {before_url}")

            try:
                await card.click(timeout=5000)
                await asyncio.sleep(3)
                after_url = page.url
                print(f"After: {after_url}")

                if before_url != after_url:
                    print(f"[!] Navigated! Video URL: {after_url}")
                    # Go back
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(8)
                else:
                    print("[!] No navigation")
                    # Check if a new tab was opened
                    pages = context.pages
                    if len(pages) > 1:
                        new_page = pages[-1]
                        new_url = new_page.url
                        print(f"[!] New tab opened: {new_url}")
                        await new_page.close()
                    else:
                        # Check for modal/overlay
                        await page.screenshot(path=str(explore_dir / f"card_{i+1}_click.png"), full_page=False)
            except Exception as e:
                print(f"[!] Click error: {e}")

        # Keep browser open
        print(f"\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(diagnose())
