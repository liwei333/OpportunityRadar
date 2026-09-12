"""Explore alternative Douyin access points.

Tests multiple URLs and approaches to find what's accessible
without triggering verification challenges.

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/explore_alternatives.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright

QUERY = "短视频代运营"

URLS_TO_TEST = [
    ("Desktop Search", f"https://www.douyin.com/search/{QUERY}?type=video"),
    ("Mobile Search", f"https://m.douyin.com/search/{QUERY}?type=video"),
    ("Douyin Homepage", "https://www.douyin.com"),
    ("Mobile Homepage", "https://m.douyin.com"),
    ("Douyin Discover", "https://www.douyin.com/discover"),
    ("Search Subdomain", f"https://s.douyin.com/s?keyword={QUERY}"),
]


async def test_url(browser, name, url):
    """Test a single URL and report what we get."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        title = await page.title()
        current_url = page.url

        # Check for verification/captcha indicators
        is_verification = any(kw in title for kw in ["验证码", "验证", "captcha", "challenge"])
        is_login = any(kw in current_url for kw in ["login", "passport"])

        # Get page text content (first 500 chars)
        body_text = await page.evaluate("() => document.body?.innerText?.substring(0, 500) || ''")

        result = {
            "name": name,
            "url": url,
            "final_url": current_url,
            "title": title,
            "is_verification": is_verification,
            "is_login": is_login,
            "body_text_preview": body_text[:300],
        }

        print(f"  Title: {title}")
        print(f"  Final URL: {current_url}")
        print(f"  Is Verification: {is_verification}")
        print(f"  Is Login: {is_login}")
        print(f"  Body preview: {body_text[:200]}...")

        return result

    except Exception as e:
        print(f"  ERROR: {e}")
        return {
            "name": name,
            "url": url,
            "error": str(e),
        }
    finally:
        await page.close()


async def explore_with_manual_intervention():
    """Open browser, detect verification, wait for manual solve, then explore."""
    print("\n" + "=" * 80)
    print("MANUAL INTERVENTION MODE")
    print("=" * 80)
    print("This will open Douyin search and wait for you to solve any verification.")
    print("After solving, the script will continue automatically.")
    print()

    profile_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "browser_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )

        page = context.pages[0] if context.pages else await context.new_page()
        url = f"https://www.douyin.com/search/{QUERY}?type=video"
        print(f"[*] Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Wait and check for verification
        for attempt in range(12):  # Check every 10 seconds for 2 minutes
            await asyncio.sleep(10)
            title = await page.title()
            current_url = page.url

            is_verification = any(kw in title for kw in ["验证码", "验证", "captcha", "challenge"])

            if is_verification:
                print(f"  [{attempt+1}/12] Still on verification page: {title}")
                print(f"           URL: {current_url}")
                print("           Please solve the verification in the browser...")
            else:
                print(f"  [{attempt+1}/12] Verification cleared! Title: {title}")
                print(f"           URL: {current_url}")
                break
        else:
            print("[!] Timed out waiting for manual verification.")
            print("[!] Will try to continue anyway...")

        # Now explore the actual page
        print("\n[*] Exploring page structure after verification...")

        structure = await page.evaluate("""() => {
            const result = {
                title: document.title,
                url: window.location.href,
                searchInputs: [],
                videoLinks: [],
                allRoles: {},
                containerPatterns: [],
                textContent: '',
            };

            // Search inputs
            document.querySelectorAll('input').forEach((el, i) => {
                if (i < 10) {
                    result.searchInputs.push({
                        type: el.type,
                        placeholder: el.placeholder,
                        className: el.className.substring(0, 80),
                        value: el.value,
                        role: el.getAttribute('role'),
                    });
                }
            });

            // Roles
            document.querySelectorAll('[role]').forEach(el => {
                const role = el.getAttribute('role');
                if (!result.allRoles[role]) result.allRoles[role] = 0;
                result.allRoles[role]++;
            });

            // Video links
            document.querySelectorAll('a[href]').forEach(el => {
                const href = el.getAttribute('href') || '';
                if (href.includes('/video/') || href.includes('/note/')) {
                    result.videoLinks.push({
                        href: href.substring(0, 200),
                        text: el.textContent?.trim().substring(0, 100) || '',
                    });
                }
            });

            // Container patterns
            const patterns = [
                '[data-e2e*="search"]',
                '[data-e2e*="video"]',
                '[data-e2e*="scroll"]',
                '[class*="search-result"]',
                '[class*="video-list"]',
                '[class*="scroll-list"]',
                '[class*="content-list"]',
                'ul[class*="list"]',
            ];
            patterns.forEach(sel => {
                const els = document.querySelectorAll(sel);
                if (els.length > 0) {
                    result.containerPatterns.push({
                        selector: sel,
                        count: els.length,
                        firstClass: (els[0].className || '').toString().substring(0, 80),
                    });
                }
            });

            // Get main text content
            result.textContent = document.body?.innerText?.substring(0, 2000) || '';

            return result;
        }""")

        print(json.dumps(structure, ensure_ascii=False, indent=2))

        # Save results
        explore_dir = Path(__file__).resolve().parent / "_explore"
        explore_dir.mkdir(exist_ok=True)

        struct_file = explore_dir / "post_verification_structure.json"
        struct_file.write_text(json.dumps(structure, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[*] Structure saved: {struct_file}")

        # Take screenshot
        await page.screenshot(path=str(explore_dir / "post_verification.png"), full_page=False)
        print(f"[*] Screenshot saved: {explore_dir / 'post_verification.png'}")

        # Wait for manual close
        print("\n[*] Keeping browser open for 60 seconds...")
        await asyncio.sleep(60)
        await context.close()


async def main():
    """Run all exploration approaches."""
    print("=" * 80)
    print("DOUYIN ACCESS ALTERNATIVES EXPLORATION")
    print("=" * 80)

    # Phase 1: Test multiple URLs
    print("\n## Phase 1: Testing multiple URL patterns...")

    async with async_playwright() as p:
        profile_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "browser_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        browser = await p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )

        results = []
        for name, url in URLS_TO_TEST:
            result = await test_url(browser, name, url)
            results.append(result)

        await browser.close()

    # Save results
    explore_dir = Path(__file__).resolve().parent / "_explore"
    explore_dir.mkdir(exist_ok=True)
    results_file = explore_dir / "url_tests.json"
    results_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[*] URL test results saved: {results_file}")

    # Phase 2: Manual intervention
    print("\n## Phase 2: Manual intervention for verification...")
    await explore_with_manual_intervention()


if __name__ == "__main__":
    asyncio.run(main())
