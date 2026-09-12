"""Find video IDs in search results.

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/diagnose_search_v3.py
"""

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright


QUERY = "短视频代运营"
PROFILE_DIR = Path("data/browser_profile/douyin-spike-001")


async def diagnose():
    """Find video IDs in search results."""
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

        # Intercept API responses
        api_responses = []

        async def handle_response(response):
            url = response.url
            if "/api/" in url or "aweme" in url or "search" in url.lower():
                if not any(ext in url for ext in [".js", ".css", ".woff", ".png", ".jpg", ".svg", ".woff2"]):
                    try:
                        body = await response.text()
                        api_responses.append({
                            "url": url[:200],
                            "status": response.status,
                            "bodyLen": len(body),
                            "bodySample": body[:500],
                        })
                    except Exception:
                        pass

        page.on("response", handle_response)

        url = f"https://www.douyin.com/search/{QUERY}"
        print(f"[*] Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(12)

        # Check search-result-card elements
        print(f"\n{'='*60}")
        print("SEARCH RESULT CARDS")
        print(f"{'='*60}")

        # Get card HTML and parse with Python
        card_htmls = await page.evaluate("""() => {
            const cards = document.querySelectorAll('[class*="search-result-card"]');
            return Array.from(cards).slice(0, 3).map(c => c.outerHTML);
        }""")

        for i, html in enumerate(card_htmls):
            print(f"\n--- Card {i+1} ---")
            # Find 19-digit numbers (aweme IDs)
            ids = re.findall(r'\b\d{19}\b', html)
            print(f"Aweme IDs found: {ids}")
            # Find data attributes
            data_attrs = re.findall(r'data-([a-z-]+)="([^"]*)"', html)
            print(f"Data attributes: {data_attrs[:10]}")
            # Find href values
            hrefs = re.findall(r'href="([^"]*)"', html)
            print(f"Hrefs: {hrefs[:5]}")
            # Text content
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            print(f"Text: {text[:200]}")
            # HTML preview
            print(f"HTML preview: {html[:500]}")

        # Check API responses
        print(f"\n{'='*60}")
        print("API RESPONSES")
        print(f"{'='*60}")

        for resp in api_responses[:10]:
            print(f"\n{resp['status']} {resp['url']}")
            print(f"  Body ({resp['bodyLen']} chars): {resp['bodySample'][:300]}")

        # Click test
        print(f"\n{'='*60}")
        print("CLICK TEST")
        print(f"{'='*60}")

        first_card = await page.query_selector('[class*="search-result-card"]')
        if first_card:
            print("Clicking first video card...")
            before_url = page.url
            await first_card.click(timeout=5000)
            await asyncio.sleep(3)
            after_url = page.url
            print(f"Before: {before_url}")
            print(f"After: {after_url}")

            if before_url != after_url:
                print(f"[!] Navigated to: {after_url}")
                if "/video/" in after_url:
                    print("[!] SUCCESS! Video URL found!")
            else:
                print("[!] URL didn't change")
                await page.screenshot(path=str(explore_dir / "after_card_click.png"), full_page=False)

        # Keep browser open
        print(f"\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(diagnose())
