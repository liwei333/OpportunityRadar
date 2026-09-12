"""Comprehensive Douyin search page diagnostic.

Dumps everything: full body text, DOM structure, all links, all elements
with text content, to understand exactly what the search page shows.

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/diagnose_search_v2.py
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
    """Comprehensive diagnostic."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    explore_dir = Path(__file__).resolve().parent / "_diagnose"
    explore_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        print("[*] Launching Chromium (headed mode)")
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

        # Wait longer this time
        print("[*] Waiting 12 seconds...")
        await asyncio.sleep(12)

        # Full page dump
        dump = await page.evaluate("""() => {
            const result = {
                title: document.title,
                url: window.location.href,
                timestamp: new Date().toISOString(),
                docHeight: document.documentElement.scrollHeight,
                windowHeight: window.innerHeight,
            };

            // Full body text
            result.bodyText = document.body?.innerText || '';

            // All links with text
            result.allLinks = Array.from(document.querySelectorAll('a[href]')).map(el => ({
                href: el.getAttribute('href'),
                text: el.textContent?.trim().substring(0, 100),
                class: (el.className || '').toString().substring(0, 60),
            }));

            // All elements with href attribute
            result.allHrefElements = Array.from(document.querySelectorAll('[href]')).map(el => ({
                tag: el.tagName,
                href: el.getAttribute('href'),
                text: el.textContent?.trim().substring(0, 80),
            }));

            // Elements with data-e2e
            result.dataE2e = {};
            document.querySelectorAll('[data-e2e]').forEach(el => {
                const key = el.getAttribute('data-e2e');
                if (!result.dataE2e[key]) result.dataE2e[key] = 0;
                result.dataE2e[key]++;
            });

            // Elements with role
            result.roles = {};
            document.querySelectorAll('[role]').forEach(el => {
                const role = el.getAttribute('role');
                if (!result.roles[role]) result.roles[role] = 0;
                result.roles[role]++;
            });

            // Login-related elements
            result.loginElements = Array.from(document.querySelectorAll('[class*="login"], [class*="Login"]')).map(el => ({
                tag: el.tagName,
                class: (el.className || '').toString().substring(0, 80),
                text: el.textContent?.trim().substring(0, 50),
                visible: el.offsetParent !== null,
            }));

            // Search-related elements
            result.searchElements = Array.from(document.querySelectorAll('[class*="search"], [class*="Search"]')).slice(0, 20).map(el => ({
                tag: el.tagName,
                class: (el.className || '').toString().substring(0, 80),
                text: el.textContent?.trim().substring(0, 50),
            }));

            // Video-related elements
            result.videoElements = Array.from(document.querySelectorAll('[class*="video"], [class*="Video"]')).slice(0, 20).map(el => ({
                tag: el.tagName,
                class: (el.className || '').toString().substring(0, 80),
                text: el.textContent?.trim().substring(0, 50),
            }));

            // Iframe check
            result.iframes = document.querySelectorAll('iframe').length;

            // Script tags with data
            result.scriptsWithData = Array.from(document.querySelectorAll('script')).filter(s => {
                const t = s.textContent || '';
                return t.includes('video') || t.includes('aweme') || t.includes('search');
            }).length;

            return result;
        }""")

        print(f"\n{'='*70}")
        print("FULL PAGE DUMP")
        print(f"{'='*70}")
        print(f"Title: {dump['title']}")
        print(f"URL: {dump['url']}")
        print(f"Doc Height: {dump['docHeight']}")
        print(f"\n--- BODY TEXT (first 3000 chars) ---")
        print(dump['bodyText'][:3000])
        print(f"\n--- ALL LINKS ({len(dump['allLinks'])}) ---")
        for link in dump['allLinks'][:30]:
            print(f"  {link['href'][:80]:80s} | {link['text'][:40]}")

        print(f"\n--- DATA-E2E ELEMENTS ---")
        print(json.dumps(dump['dataE2e'], ensure_ascii=False, indent=2))

        print(f"\n--- ROLES ---")
        print(json.dumps(dump['roles'], ensure_ascii=False, indent=2))

        print(f"\n--- LOGIN ELEMENTS ({len(dump['loginElements'])}) ---")
        for el in dump['loginElements'][:10]:
            print(f"  {el['tag']}.{el['class'][:40]} visible={el['visible']} text={el['text']}")

        print(f"\n--- VIDEO ELEMENTS ({len(dump['videoElements'])}) ---")
        for el in dump['videoElements'][:10]:
            print(f"  {el['tag']}.{el['class'][:40]} text={el['text']}")

        # Save full dump
        dump_file = explore_dir / "search_dump.json"
        dump_file.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[*] Full dump saved: {dump_file}")

        # Save HTML
        html = await page.content()
        html_file = explore_dir / "search_page_full.html"
        html_file.write_text(html, encoding="utf-8")
        print(f"[*] HTML saved: {html_file} ({len(html)} chars)")

        # Screenshot
        await page.screenshot(path=str(explore_dir / "search_page_v2.png"), full_page=False)

        # Check for any interactive elements that might trigger content loading
        print(f"\n{'='*70}")
        print("INTERACTIVE ELEMENTS")
        print(f"{'='*70}")

        interactive = await page.evaluate("""() => {
            const result = {
                buttons: Array.from(document.querySelectorAll('button')).slice(0, 20).map(b => ({
                    text: b.textContent?.trim().substring(0, 50),
                    class: (b.className || '').toString().substring(0, 60),
                    visible: b.offsetParent !== null,
                })),
                tabs: Array.from(document.querySelectorAll('[role="tab"]')).map(t => ({
                    text: t.textContent?.trim().substring(0, 50),
                    selected: t.getAttribute('aria-selected'),
                })),
                selectElements: Array.from(document.querySelectorAll('select')).map(s => ({
                    text: s.textContent?.trim().substring(0, 50),
                })),
            };
            return result;
        }""")

        print(json.dumps(interactive, ensure_ascii=False, indent=2))

        # Keep browser open
        print(f"\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(diagnose())
