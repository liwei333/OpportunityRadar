"""Deep diagnostic of search page blocking state.

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/diagnose_deep.py
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
    """Deep diagnostic."""
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
        await asyncio.sleep(8)

        # Full element dump
        dump = await page.evaluate("""() => {
            const result = {
                title: document.title,
                url: window.location.href,
                bodyText: document.body?.innerText || '',
                docHeight: document.documentElement.scrollHeight,
            };

            // Find all fixed/absolute positioned elements (overlays)
            const overlays = [];
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                const zIndex = parseInt(style.zIndex) || 0;
                if (zIndex > 100 && style.display !== 'none' && style.visibility !== 'hidden') {
                    overlays.push({
                        tag: el.tagName,
                        id: el.id,
                        class: (el.className || '').toString().substring(0, 60),
                        zIndex: zIndex,
                        text: el.textContent?.trim().substring(0, 50),
                    });
                }
            });
            result.overlays = overlays.sort((a, b) => b.zIndex - a.zIndex).slice(0, 20);

            // Find all hidden captcha elements
            const captchaElements = [];
            document.querySelectorAll('[id*="captcha"], [class*="captcha"]').forEach(el => {
                const style = window.getComputedStyle(el);
                captchaElements.push({
                    tag: el.tagName,
                    id: el.id,
                    class: (el.className || '').toString().substring(0, 60),
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    zIndex: style.zIndex,
                    width: el.offsetWidth,
                    height: el.offsetHeight,
                    visible: el.offsetParent !== null,
                });
            });
            result.captchaElements = captchaElements;

            // Find search-related UI
            const searchUI = [];
            document.querySelectorAll('[class*="search"]').forEach(el => {
                if (el.textContent?.trim() && el.textContent.trim().length < 200) {
                    searchUI.push({
                        tag: el.tagName,
                        class: (el.className || '').toString().substring(0, 60),
                        text: el.textContent.trim().substring(0, 80),
                        visible: el.offsetParent !== null,
                    });
                }
            });
            result.searchUI = searchUI.slice(0, 20);

            return result;
        }""")

        print(f"\nTitle: {dump['title']}")
        print(f"URL: {dump['url']}")
        print(f"Doc Height: {dump['docHeight']}")

        print(f"\n--- BODY TEXT (first 2000 chars) ---")
        print(dump['bodyText'][:2000])

        print(f"\n--- HIGH Z-INDEX OVERLAYS ({len(dump['overlays'])}) ---")
        for overlay in dump['overlays']:
            print(f"  z={overlay['zIndex']} {overlay['tag']}#{overlay['id']}.{overlay['class'][:40]} text={overlay['text']}")

        print(f"\n--- CAPTCHA ELEMENTS ({len(dump['captchaElements'])}) ---")
        for cap in dump['captchaElements']:
            print(f"  {cap['tag']}#{cap['id']}.{cap['class'][:40]} display={cap['display']} visible={cap['visible']} z={cap['zIndex']}")

        print(f"\n--- SEARCH UI ({len(dump['searchUI'])}) ---")
        for ui in dump['searchUI']:
            print(f"  {ui['tag']}.{ui['class'][:40]} text={ui['text']}")

        # Save dump
        dump_file = explore_dir / "deep_dump.json"
        dump_file.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[*] Dump saved: {dump_file}")

        # Save HTML
        html = await page.content()
        html_file = explore_dir / "deep_page.html"
        html_file.write_text(html, encoding="utf-8")
        print(f"[*] HTML saved: {html_file} ({len(html)} chars)")

        # Keep browser open
        print(f"\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(diagnose())
