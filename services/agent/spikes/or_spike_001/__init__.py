"""OR-SPIKE-001: Douyin Web Real Data Collector.

Validates whether OpportunityRadar can reliably collect real, structured,
traceable video and account data from Douyin Web via Playwright.

Key findings:
- Homepage feed (/jingxuan) is accessible without login
- Search requires login + manual verification solving
- Bot detection prevents search results from rendering without real user session
"""
