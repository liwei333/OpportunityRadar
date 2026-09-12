"""Explore Douyin search results page structure.

Key finding: https://www.douyin.com/search/{query} (without ?type=video)
shows real search results without verification challenge.

This script explores the search results page to understand:
1. The DOM structure of search result items
2. How to extract video data (title, author, URL, etc.)
3. How to scroll and load more results
4. How to extract account data

Usage:
    cd services/agent
    .venv/bin/python spikes/or_spike_001/explore_search_results.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from playwright.async_api import async_playwright

QUERY = "短视频代运营"


async def explore_search_results():
    """Explore the search results page structure."""
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

        # Navigate to search page (WITHOUT ?type=video)
        url = f"https://www.douyin.com/search/{QUERY}"
        print(f"[*] Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(8)

        title = await page.title()
        current_url = page.url
        print(f"  Title: {title}")
        print(f"  URL: {current_url}")

        await page.screenshot(path=str(explore_dir / "search_results_initial.png"), full_page=False)

        # Explore the page structure
        print("\n" + "=" * 60)
        print("EXPLORING SEARCH RESULTS STRUCTURE")
        print("=" * 60)

        structure = await page.evaluate("""() => {
            const result = {
                title: document.title,
                url: window.location.href,
                // Find all links
                allLinks: [],
                // Find video-related elements
                videoElements: [],
                // Find search result containers
                containers: {},
                // All role attributes
                roles: {},
                // Text content sample
                textSample: '',
            };

            // Get all links with href
            document.querySelectorAll('a[href]').forEach(el => {
                const href = el.getAttribute('href') || '';
                const text = el.textContent?.trim().substring(0, 150) || '';
                result.allLinks.push({
                    href: href.substring(0, 200),
                    text: text,
                    className: (el.className || '').toString().substring(0, 80),
                });
            });

            // Find elements with role
            document.querySelectorAll('[role]').forEach(el => {
                const role = el.getAttribute('role');
                if (!result.roles[role]) result.roles[role] = 0;
                result.roles[role]++;
            });

            // Look for search result container patterns
            const containerPatterns = [
                '[data-e2e="search-result-list"]',
                '[data-e2e="scroll-list"]',
                '[data-e2e*="search"]',
                '[data-e2e*="video"]',
                '[class*="search-result"]',
                '[class*="search_result"]',
                '[class*="result-list"]',
                '[class*="video-list"]',
                '[class*="scroll-list"]',
                '[class*="content-list"]',
                'ul[class*="list"]',
                'div[class*="List"]',
                'div[class*="item"]',
                'div[class*="Item"]',
                'div[class*="card"]',
                'div[class*="Card"]',
                'li[class*="item"]',
                'li[class*="Item"]',
            ];

            containerPatterns.forEach(sel => {
                const els = document.querySelectorAll(sel);
                if (els.length > 0) {
                    result.containers[sel] = {
                        count: els.length,
                        firstClass: (els[0].className || '').toString().substring(0, 100),
                        firstHTML: els[0].outerHTML.substring(0, 800),
                        childCount: els[0].children.length,
                    };
                }
            });

            // Get text sample
            result.textSample = document.body?.innerText?.substring(0, 3000) || '';

            return result;
        }""")

        print(f"  Total links found: {len(structure['allLinks'])}")
        print(f"  Roles found: {json.dumps(structure['roles'], ensure_ascii=False, indent=2)}")
        print(f"  Container patterns found: {len(structure['containers'])}")

        for sel, info in structure['containers'].items():
            print(f"\n  {sel}: {info['count']} elements")
            print(f"    First class: {info['firstClass']}")
            print(f"    Child count: {info['childCount']}")
            print(f"    HTML preview: {info['firstHTML'][:300]}")

        # Save full structure
        struct_file = explore_dir / "search_results_structure.json"
        struct_file.write_text(json.dumps(structure, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[*] Full structure saved: {struct_file}")

        # Now look specifically for video items
        print("\n" + "=" * 60)
        print("LOOKING FOR VIDEO ITEMS")
        print("=" * 60)

        # Try to find video item containers by looking at the DOM more carefully
        video_items = await page.evaluate("""() => {
            const result = {
                items: [],
                approach: '',
            };

            // Approach 1: Look for links that contain video URLs
            const videoLinks = [];
            document.querySelectorAll('a[href]').forEach(el => {
                const href = el.getAttribute('href') || '';
                if (href.includes('/video/') || href.includes('/note/')) {
                    // Get the parent container
                    let container = el;
                    for (let i = 0; i < 5; i++) {
                        if (container.parentElement) {
                            container = container.parentElement;
                        }
                    }
                    videoLinks.push({
                        href: href,
                        linkText: el.textContent?.trim().substring(0, 100) || '',
                        containerTag: container.tagName,
                        containerClass: (container.className || '').toString().substring(0, 100),
                        containerHTML: container.outerHTML.substring(0, 600),
                    });
                }
            });

            result.approach = 'video_links';
            result.items = videoLinks.slice(0, 5);  // First 5
            result.totalVideoLinks = videoLinks.length;

            return result;
        }""")

        print(f"  Total video links: {video_items['totalVideoLinks']}")
        for item in video_items['items']:
            print(f"\n  Video: {item['href']}")
            print(f"    Text: {item['linkText']}")
            print(f"    Container class: {item['containerClass']}")
            print(f"    HTML: {item['containerHTML'][:300]}")

        # Try to find the scroll container and understand the layout
        print("\n" + "=" * 60)
        print("SCROLL CONTAINER ANALYSIS")
        print("=" * 60)

        scroll_info = await page.evaluate("""() => {
            const result = {
                scrollContainers: [],
                windowHeight: window.innerHeight,
                documentHeight: document.documentElement.scrollHeight,
            };

            // Find scrollable containers
            document.querySelectorAll('*').forEach(el => {
                if (el.scrollHeight > el.clientHeight + 50 && el.clientHeight > 100) {
                    result.scrollContainers.push({
                        tag: el.tagName,
                        className: (el.className || '').toString().substring(0, 80),
                        id: el.id,
                        scrollHeight: el.scrollHeight,
                        clientHeight: el.clientHeight,
                        scrollTop: el.scrollTop,
                    });
                }
            });

            return result;
        }""")

        print(f"  Window height: {scroll_info['windowHeight']}")
        print(f"  Document height: {scroll_info['documentHeight']}")
        print(f"  Scrollable containers: {len(scroll_info['scrollContainers'])}")
        for sc in scroll_info['scrollContainers'][:10]:
            print(f"    {sc['tag']}.{sc['className'][:50]} - scrollH:{sc['scrollHeight']} clientH:{sc['clientHeight']}")

        # Scroll and observe
        print("\n" + "=" * 60)
        print("SCROLLING TO LOAD MORE RESULTS")
        print("=" * 60)

        for i in range(3):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(3)

            new_height = await page.evaluate("document.documentElement.scrollHeight")
            link_count = await page.evaluate("document.querySelectorAll('a[href*=\\'/video/\\']').length")

            print(f"  Scroll {i+1}: doc height={new_height}, video links={link_count}")

        await page.screenshot(path=str(explore_dir / "search_results_scrolled.png"), full_page=False)

        # Final DOM snapshot
        final_html = await page.content()
        html_file = explore_dir / "search_results.html"
        html_file.write_text(final_html, encoding="utf-8")
        print(f"\n[*] Full HTML saved: {html_file} ({len(final_html)} chars)")

        # Keep browser open
        print("\n[*] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)
        await context.close()


if __name__ == "__main__":
    asyncio.run(explore_search_results())
