"""Page fetching functionality."""

from typing import Optional
from playwright.async_api import Browser, Page  # ✅ Changed from sync_api to async_api


class PageFetcher:
    """
    Fetches web pages using Playwright.

    Responsibilities:
    - Creating browser contexts
    - Loading pages with proper configuration
    - Handling page load errors
    """

    def __init__(self, browser: Browser, timeout: int = 30000,
                 user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'):
        """
        Initialize page fetcher.

        Args:
            browser: Playwright browser instance
            timeout: Page load timeout in milliseconds
            user_agent: User agent string
        """
        self.browser = browser
        self.timeout = timeout
        self.user_agent = user_agent

    async def fetch(self, url: str) -> Optional[Page]:  # ✅ Added async
        """
        Fetch a web page.

        Args:
            url: URL to fetch

        Returns:
            Page instance or None if failed
        """
        try:
            context = await self.browser.new_context(  # ✅ Added await
                ignore_https_errors=True,
                user_agent=self.user_agent
            )
            page = await context.new_page()  # ✅ Added await
            await page.goto(url, timeout=self.timeout)  # ✅ Added await
            await page.wait_for_load_state('networkidle')  # ✅ Added await
            return page
        except Exception as e:
            print(f"ERROR loading {url}: {e}")
            return None