"""Explore Douyin homepage search functionality.

Since direct search URL triggers verification, try using the
search box on the homepage which may not trigger the same challenge.

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/explore_homepage_search.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright

QUERY = "短视频代运营"


async def explore():
    """Use homepage search box to search."""
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

        # Step 1: Go to homepage
        print("[*] Step 1: Navigating to homepage...")
        await page.goto("https://www.douyin.com/jingxuan", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        title = await page.title()
        print(f"  Title: {title}")
        await page.screenshot(path=str(explore_dir / "homepage.png"), full_page=False)

        # Step 2: Find search input on homepage
        print("\n[*] Step 2: Looking for search input on homepage...")

        search_info = await page.evaluate("""() => {
            const result = {
                inputs: [],
                searchButtons: [],
                forms: [],
            };

            // Find all inputs
            document.querySelectorAll('input').forEach((el, i) => {
                result.inputs.push({
                    index: i,
                    type: el.type,
                    placeholder: el.placeholder,
                    className: el.className.substring(0, 100),
                    id: el.id,
                    name: el.name,
                    value: el.value,
                    role: el.getAttribute('role'),
                    ariaLabel: el.getAttribute('aria-label'),
                    rect: el.getBoundingClientRect(),
                });
            });

            // Find buttons that might be search buttons
            document.querySelectorAll('button, [role="button"], div[class*="search"], span[class*="search"]').forEach((el, i) => {
                if (i < 20) {
                    const text = el.textContent?.trim().substring(0, 50) || '';
                    const cls = (el.className || '').toString().substring(0, 80);
                    if (text.includes('搜索') || text.includes('search') || cls.includes('search') || cls.includes('Search')) {
                        result.searchButtons.push({
                            tag: el.tagName,
                            text: text,
                            className: cls,
                            role: el.getAttribute('role'),
                        });
                    }
                }
            });

            // Find forms
            document.querySelectorAll('form').forEach((el, i) => {
                result.forms.push({
                    index: i,
                    action: el.action,
                    method: el.method,
                    className: el.className.substring(0, 80),
                    id: el.id,
                });
            });

            return result;
        }""")

        print(json.dumps(search_info, ensure_ascii=False, indent=2))

        # Step 3: Try to use the search box
        print("\n[*] Step 3: Attempting to use search box...")

        # Try to find and interact with search input
        search_input = await page.query_selector('input[type="text"], input[type="search"], input[placeholder*="搜索"], input[placeholder*="search"]')
        if search_input:
            print("  Found search input, clicking and typing...")
            await search_input.click()
            await asyncio.sleep(1)
            await search_input.fill(QUERY)
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            print("  Waiting for results...")
            await asyncio.sleep(8)

            result_title = await page.title()
            result_url = page.url
            print(f"  Result title: {result_title}")
            print(f"  Result URL: {result_url}")

            is_verification = any(kw in result_title for kw in ["验证码", "验证", "captcha", "challenge"])
            print(f"  Is verification: {is_verification}")

            await page.screenshot(path=str(explore_dir / "homepage_search_result.png"), full_page=False)

            if not is_verification:
                # Explore the results page
                print("\n[*] Step 4: Exploring search results structure...")
                structure = await page.evaluate("""() => {
                    const result = {
                        title: document.title,
                        url: window.location.href,
                        videoLinks: [],
                        allRoles: {},
                        containerPatterns: [],
                        textContent: '',
                    };

                    document.querySelectorAll('[role]').forEach(el => {
                        const role = el.getAttribute('role');
                        if (!result.allRoles[role]) result.allRoles[role] = 0;
                        result.allRoles[role]++;
                    });

                    document.querySelectorAll('a[href]').forEach(el => {
                        const href = el.getAttribute('href') || '';
                        if (href.includes('/video/') || href.includes('/note/')) {
                            result.videoLinks.push({
                                href: href.substring(0, 200),
                                text: el.textContent?.trim().substring(0, 100) || '',
                            });
                        }
                    });

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

                    result.textContent = document.body?.innerText?.substring(0, 3000) || '';
                    return result;
                }""")

                print(json.dumps(structure, ensure_ascii=False, indent=2))

                struct_file = explore_dir / "homepage_search_structure.json"
                struct_file.write_text(json.dumps(structure, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"\n[*] Structure saved: {struct_file}")
            else:
                print("[!] Verification challenge still appears even from homepage search.")
        else:
            print("  No search input found on homepage.")

            # Try looking for a search icon/button that reveals a search input
            print("  Looking for search icon/button...")
            search_icon = await page.query_selector('[class*="search"], [class*="Search"], svg[class*="search"]')
            if search_icon:
                print("  Found search icon, clicking...")
                await search_icon.click()
                await asyncio.sleep(2)

                # Check for new input
                search_input2 = await page.query_selector('input[type="text"], input[type="search"]')
                if search_input2:
                    print("  Search input appeared, typing query...")
                    await search_input2.click()
                    await search_input2.fill(QUERY)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(8)

                    result_title = await page.title()
                    print(f"  Result title: {result_title}")
                    await page.screenshot(path=str(explore_dir / "homepage_search_result.png"), full_page=False)

        # Keep browser open
        print("\n[*] Keeping browser open for 60 seconds...")
        await asyncio.sleep(60)
        await context.close()


if __name__ == "__main__":
    asyncio.run(explore())
