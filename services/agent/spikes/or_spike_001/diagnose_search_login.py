"""Diagnose Douyin search page login requirement.

The search page shows an inline login prompt:
"登录后即可搜索更多精彩视频"

This script:
1. Detects the inline login state
2. Waits for user to complete login
3. Checks if search results appear after login
4. Dumps the post-login DOM structure

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/diagnose_search_login.py
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
    """Diagnose and wait for search login."""
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
        await asyncio.sleep(8)

        title = await page.title()
        print(f"Title: {title}")

        # Check for inline login prompt
        inline_login = await page.evaluate("""() => {
            const bodyText = document.body?.innerText || '';
            return {
                hasInlineLoginPrompt: bodyText.includes('登录后即可搜索更多精彩视频'),
                hasScanLogin: bodyText.includes('扫码登录'),
                hasSmsLogin: bodyText.includes('验证码登录'),
                hasPasswordLogin: bodyText.includes('密码登录'),
                loginSectionVisible: !!document.querySelector('[class*="login"]'),
            };
        }""")
        print(f"\nInline login detection: {json.dumps(inline_login, ensure_ascii=False)}")

        if inline_login.get("hasInlineLoginPrompt"):
            print(f"\n{'='*60}")
            print("INLINE LOGIN REQUIRED")
            print(f"{'='*60}")
            print("Search page requires login to show results.")
            print("Please complete login in the browser window.")
            print("Waiting up to 180 seconds...")

            start = time.time()
            while (time.time() - start) < 180:
                await asyncio.sleep(5)

                state = await page.evaluate("""() => {
                    const bodyText = document.body?.innerText || '';
                    return {
                        stillNeedsLogin: bodyText.includes('登录后即可搜索更多精彩视频'),
                        hasVideoLinks: document.querySelectorAll('[href*="/video/"]').length,
                        title: document.title,
                        bodyLen: bodyText.length,
                    };
                }""")

                elapsed = int(time.time() - start)
                print(f"  [{elapsed}s] needs_login={state['stillNeedsLogin']}, video_links={state['hasVideoLinks']}, title={state['title']}")

                if not state["stillNeedsLogin"] or state["hasVideoLinks"] > 0:
                    print("[!] Login appears complete or results appeared!")
                    break
            else:
                print("[!] Timed out waiting for login")

            # Post-login analysis
            print(f"\n{'='*60}")
            print("POST-LOGIN ANALYSIS")
            print(f"{'='*60}")

            await asyncio.sleep(5)

            post_state = await page.evaluate("""() => {
                const result = {
                    title: document.title,
                    url: window.location.href,
                    bodyLen: (document.body?.innerText || '').length,
                    bodyText: (document.body?.innerText || '').substring(0, 1000),
                    videoHrefs: document.querySelectorAll('[href*="/video/"]').length,
                    scrollList: document.querySelectorAll('[data-e2e="scroll-list"]').length,
                    scrollListChildren: 0,
                    docHeight: document.documentElement.scrollHeight,
                };

                const scrollList = document.querySelector('[data-e2e="scroll-list"]');
                if (scrollList) {
                    result.scrollListChildren = scrollList.children.length;
                    result.scrollListHTML = scrollList.outerHTML.substring(0, 500);
                }

                // Sample video hrefs
                const videoEls = document.querySelectorAll('[href*="/video/"]');
                result.sampleVideoHrefs = Array.from(videoEls).slice(0, 5).map(el => ({
                    href: el.getAttribute('href'),
                    text: el.textContent?.trim().substring(0, 80),
                }));

                return result;
            }""")

            print(json.dumps(post_state, ensure_ascii=False, indent=2))
            await page.screenshot(path=str(explore_dir / "post_login_search.png"), full_page=False)

            # Try scrolling
            if post_state.get("videoHrefs", 0) > 0:
                print(f"\n[*] Found {post_state['videoHrefs']} video links! Testing scroll...")
                for i in range(3):
                    await page.evaluate("window.scrollBy(0, 800)")
                    await asyncio.sleep(3)
                    new_count = await page.evaluate("document.querySelectorAll('[href*=\"/video/\"]').length")
                    print(f"  Scroll {i+1}: {new_count} video links")
            else:
                print("\n[!] No video links found after login. Dumping full page HTML...")
                html = await page.content()
                html_file = explore_dir / "post_login_no_results.html"
                html_file.write_text(html, encoding="utf-8")
                print(f"  HTML saved: {html_file} ({len(html)} chars)")

        else:
            print("[!] No inline login prompt detected. Checking for results...")
            results = await page.evaluate("""() => {
                return {
                    videoHrefs: document.querySelectorAll('[href*="/video/"]').length,
                    bodyLen: (document.body?.innerText || '').length,
                };
            }""")
            print(json.dumps(results, ensure_ascii=False))

        # Keep browser open
        print(f"\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(diagnose())
