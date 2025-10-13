"""Browser lifecycle management using Playwright."""

from typing import Optional
from playwright.async_api import async_playwright, Browser, Playwright


class BrowserManager:
    """
    Manages Playwright browser lifecycle (async version).

    Responsibilities:
    - Starting/stopping Playwright
    - Launching/closing browser
    - Providing browser instances
    """

    def __init__(self, headless: bool = True):
        """
        Initialize browser manager.

        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def start(self) -> Browser:
        """
        Start Playwright and launch browser.

        Returns:
            Browser instance
        """
        if not self._playwright:
            self._playwright = await async_playwright().start()

        if not self._browser:
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )

        return self._browser

    async def stop(self) -> None:
        """Stop browser and Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def get_browser(self) -> Browser:
        """
        Get browser instance (starts if not running).

        Returns:
            Browser instance
        """
        if not self._browser:
            return await self.start()
        return self._browser

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()