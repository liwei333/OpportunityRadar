"""Explore how to extract video URLs from Douyin feed cards.

The feed shows video cards but no direct /video/ links.
This script explores alternative ways to get video URLs:
1. Click on a card and see what URL it navigates to
2. Look for data attributes or JavaScript state
3. Check if video IDs are embedded in the DOM

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/explore_feed_urls.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright


async def explore():
    """Explore feed card URLs."""
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

        # Go to feed
        print("[*] Navigating to feed...")
        await page.goto("https://www.douyin.com/jingxuan", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # Close login dialog
        await page.keyboard.press("Escape")
        await asyncio.sleep(2)

        # Look for clickable video cards
        print("\n[*] Looking for clickable video cards...")

        cards = await page.evaluate("""() => {
            const results = [];

            // Find all clickable elements that might be video cards
            const clickableElements = document.querySelectorAll(
                'a[href], [role="link"], [role="button"], [class*="card"], [class*="Card"], [class*="item"], [class*="Item"]'
            );

            for (const el of clickableElements) {
                const href = el.getAttribute('href') || '';
                const text = el.textContent?.trim().substring(0, 100) || '';

                // Look for elements with video-related content
                if (text.includes('@') || el.querySelector('a[href*="/video/"]') || el.querySelector('[data-e2e*="video"]')) {
                    results.push({
                        tag: el.tagName,
                        href: href,
                        text: text,
                        className: (el.className || '').toString().substring(0, 80),
                        hasClickHandler: el.onclick !== null,
                        dataAttrs: Object.keys(el.dataset),
                    });
                }
            }

            return results.slice(0, 20);
        }""")

        print(f"  Found {len(cards)} clickable video elements")
        for card in cards[:10]:
            print(f"    {card['tag']} href={card['href'][:80]} text={card['text'][:50]}")

        # Try clicking on the first video card
        print("\n[*] Trying to click on first video card...")

        # Find a clickable element with video content
        first_card = await page.query_selector('[class*="card"], [class*="Card"]')
        if first_card:
            # Get the URL before clicking
            before_url = page.url
            print(f"  Before click: {before_url}")

            # Click
            await first_card.click(timeout=5000)
            await asyncio.sleep(3)

            # Get URL after clicking
            after_url = page.url
            print(f"  After click: {after_url}")

            if before_url != after_url:
                print(f"  [!] Navigated to: {after_url}")

                # Take screenshot
                await page.screenshot(path=str(explore_dir / "after_card_click.png"), full_page=False)
            else:
                print("  [!] URL didn't change - might be a modal/overlay")

            # Go back
            await page.goto("https://www.douyin.com/jingxuan", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)

        # Check for video data in page scripts
        print("\n[*] Looking for video data in page scripts...")

        script_data = await page.evaluate("""() => {
            const results = {
                scriptCount: 0,
                videoIdsInScripts: [],
                exposeData: null,
                nextData: null,
            };

            // Check for __NEXT_DATA__ (Next.js)
            const nextData = document.getElementById('__NEXT_DATA__');
            if (nextData) {
                try {
                    const data = JSON.parse(nextData.textContent);
                    results.nextData = JSON.stringify(data).substring(0, 1000);
                } catch (e) {}
            }

            // Check for EXPOSE_DATA
            try {
                if (window.EXPOSE_DATA) {
                    results.exposeData = JSON.stringify(window.EXPOSE_DATA).substring(0, 500);
                }
            } catch (e) {}

            // Look for video IDs in all script tags
            document.querySelectorAll('script').forEach(script => {
                results.scriptCount++;
                const text = script.textContent || '';
                // Look for video ID patterns (19-digit numbers)
                const videoIds = text.match(/\\b\\d{19}\\b/g);
                if (videoIds) {
                    results.videoIdsInScripts.push(...videoIds.slice(0, 5));
                }
            });

            return results;
        }""")

        print(f"  Scripts found: {script_data['scriptCount']}")
        print(f"  Video IDs in scripts: {script_data['videoIdsInScripts']}")
        if script_data['nextData']:
            print(f"  __NEXT_DATA__: {script_data['nextData'][:300]}")
        if script_data['exposeData']:
            print(f"  EXPOSE_DATA: {script_data['exposeData']}")

        # Try to extract video IDs from the feed by examining the DOM structure
        print("\n[*] Examining feed DOM for video IDs...")

        dom_data = await page.evaluate("""() => {
            const results = {
                allIds: [],
                dataAwemeId: [],
                ariaLabels: [],
            };

            // Look for data-aweme-id or similar attributes
            document.querySelectorAll('*').forEach(el => {
                for (const attr of el.attributes) {
                    if (attr.name.includes('aweme') || attr.name.includes('video') || attr.name.includes('id')) {
                        if (/^\\d{15,20}$/.test(attr.value)) {
                            results.allIds.push({
                                attr: attr.name,
                                value: attr.value,
                                tag: el.tagName,
                                class: (el.className || '').toString().substring(0, 50),
                            });
                        }
                    }
                }
            });

            // Look for aria-labels with video info
            document.querySelectorAll('[aria-label]').forEach(el => {
                const label = el.getAttribute('aria-label');
                if (label && (label.includes('视频') || label.includes('video') || label.includes('作者'))) {
                    results.ariaLabels.push({
                        label: label.substring(0, 100),
                        tag: el.tagName,
                    });
                }
            });

            return results;
        }""")

        print(f"  ID-like attributes found: {len(dom_data['allIds'])}")
        for id_info in dom_data['allIds'][:10]:
            print(f"    {id_info['attr']}={id_info['value']} ({id_info['tag']}.{id_info['class']})")

        print(f"  Aria labels with video info: {len(dom_data['ariaLabels'])}")
        for label_info in dom_data['ariaLabels'][:5]:
            print(f"    {label_info['label']}")

        # Keep browser open
        print("\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(explore())
