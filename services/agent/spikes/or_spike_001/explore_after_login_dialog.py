"""Explore Douyin after handling login dialog.

Findings so far:
- Direct search URL triggers verification challenge
- Homepage is accessible but login dialog blocks search
- Mobile site returns 404

This script tries to:
1. Close the login dialog
2. Use search without logging in
3. If that fails, try to explore what's accessible without login

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/explore_after_login_dialog.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright

QUERY = "短视频代运营"


async def explore():
    """Handle login dialog and try search."""
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

        # Go to homepage
        print("[*] Navigating to homepage...")
        await page.goto("https://www.douyin.com/jingxuan", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # Step 1: Try to close login dialog
        print("\n[*] Step 1: Looking for login dialog close button...")

        close_result = await page.evaluate("""() => {
            const result = {
                loginPanelFound: false,
                closeButtons: [],
            };

            // Find login panel
            const loginPanel = document.querySelector('[id*="login-full-panel"]');
            if (loginPanel) {
                result.loginPanelFound = true;

                // Find close buttons within or near the login panel
                const closeSelectors = [
                    'button[aria-label="close"]',
                    'button[aria-label="Close"]',
                    '[class*="close"]',
                    '[class*="Close"]',
                    'svg[class*="close"]',
                    'span[class*="close"]',
                    'div[class*="close"]',
                    '[aria-label="关闭"]',
                    '[title="关闭"]',
                    'button[class*="close"]',
                ];

                closeSelectors.forEach(sel => {
                    const els = loginPanel.querySelectorAll(sel);
                    els.forEach(el => {
                        result.closeButtons.push({
                            tag: el.tagName,
                            className: (el.className || '').toString().substring(0, 80),
                            text: el.textContent?.trim().substring(0, 30) || '',
                            ariaLabel: el.getAttribute('aria-label'),
                            rect: el.getBoundingClientRect(),
                        });
                    });
                });

                // Also look for the overlay backdrop
                const overlay = document.querySelector('[class*="overlay"], [class*="mask"], [class*="backdrop"]');
                if (overlay) {
                    result.overlay = {
                        className: (overlay.className || '').toString().substring(0, 80),
                        id: overlay.id,
                    };
                }
            }

            return result;
        }""")

        print(json.dumps(close_result, ensure_ascii=False, indent=2))

        # Try clicking the close button
        if close_result.get("closeButtons"):
            print(f"\n[*] Found {len(close_result['closeButtons'])} potential close buttons, trying to click...")
            for btn in close_result["closeButtons"]:
                if btn["className"] or btn["ariaLabel"]:
                    try:
                        # Try to find and click the close button
                        close_btn = await page.query_selector('[class*="close"]')
                        if close_btn:
                            await close_btn.click(timeout=5000)
                            print("  Clicked close button")
                            await asyncio.sleep(2)
                            break
                    except Exception as e:
                        print(f"  Failed to click: {e}")

        # Alternative: try pressing Escape to close dialog
        print("[*] Trying Escape key to close dialog...")
        await page.keyboard.press("Escape")
        await asyncio.sleep(2)

        # Check if login dialog is still there
        login_still_there = await page.evaluate("""() => {
            const panel = document.querySelector('[id*="login-full-panel"]');
            return panel !== null && panel.offsetParent !== null;
        }""")
        print(f"  Login dialog still visible: {login_still_there}")

        # Take screenshot after dialog handling
        await page.screenshot(path=str(explore_dir / "after_dialog_handling.png"), full_page=False)

        # Step 2: Try to use search box
        print("\n[*] Step 2: Trying to use search box...")

        try:
            # Use a more robust selector with coordinate-based interaction
            search_input = await page.wait_for_selector(
                'input[placeholder*="搜索"]',
                timeout=10000,
                state="visible"
            )
            if search_input:
                print("  Search input found, trying coordinate click...")

                # Get the bounding box and click via coordinates
                box = await search_input.bounding_box()
                if box:
                    await page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    await asyncio.sleep(1)
                    await page.keyboard.type(QUERY, delay=100)
                    await asyncio.sleep(1)
                    await page.keyboard.press("Enter")
                    print("  Query submitted, waiting for results...")
                    await asyncio.sleep(8)

                    result_title = await page.title()
                    result_url = page.url
                    is_verification = any(kw in result_title for kw in ["验证码", "验证", "captcha", "challenge"])

                    print(f"  Result title: {result_title}")
                    print(f"  Result URL: {result_url}")
                    print(f"  Is verification: {is_verification}")

                    await page.screenshot(path=str(explore_dir / "search_result.png"), full_page=False)

                    if not is_verification:
                        # Explore the results
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

                        print("\n[*] Search results structure:")
                        print(json.dumps(structure, ensure_ascii=False, indent=2))

                        struct_file = explore_dir / "search_structure.json"
                        struct_file.write_text(json.dumps(structure, ensure_ascii=False, indent=2), encoding="utf-8")
                        print(f"\n[*] Structure saved: {struct_file}")
                    else:
                        print("[!] Verification challenge still appears.")
        except Exception as e:
            print(f"  Error interacting with search: {e}")

        # Step 3: Explore what's accessible without login
        print("\n[*] Step 3: Exploring accessible content without login...")

        # Go back to homepage
        await page.goto("https://www.douyin.com/jingxuan", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # Try to close login dialog again
        await page.keyboard.press("Escape")
        await asyncio.sleep(2)

        # Look for video content that might be accessible
        accessible_content = await page.evaluate("""() => {
            const result = {
                videoLinks: [],
                creatorLinks: [],
                textContent: '',
            };

            // Find all links
            document.querySelectorAll('a[href]').forEach(el => {
                const href = el.getAttribute('href') || '';
                if (href.includes('/video/') || href.includes('/note/')) {
                    result.videoLinks.push({
                        href: href.substring(0, 200),
                        text: el.textContent?.trim().substring(0, 100) || '',
                    });
                }
                if (href.includes('/user/') || href.includes('/@')) {
                    result.creatorLinks.push({
                        href: href.substring(0, 200),
                        text: el.textContent?.trim().substring(0, 100) || '',
                    });
                }
            });

            result.textContent = document.body?.innerText?.substring(0, 2000) || '';
            return result;
        }""")

        print(f"  Video links found: {len(accessible_content['videoLinks'])}")
        print(f"  Creator links found: {len(accessible_content['creatorLinks'])}")
        print(f"  Content preview: {accessible_content['textContent'][:500]}")

        # Keep browser open
        print("\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(explore())
