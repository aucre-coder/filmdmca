"""Browser lifecycle management using Camoufox."""

from typing import Optional
from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser


class BrowserManager:
    """
    Manages Camoufox browser lifecycle (async version).

    Responsibilities:
    - Starting/stopping Camoufox
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
        self._camoufox = None
        self._browser: Optional[Browser] = None

    async def start(self) -> Browser:
        """
        Start Camoufox and launch browser.

        Returns:
            Browser instance
        """
        if not self._camoufox:
            self._camoufox = AsyncCamoufox(
                headless=self.headless,
                humanize=True,
                geoip=True
            )

        if not self._browser:
            self._browser = await self._camoufox.start()

        return self._browser

    async def stop(self) -> None:
        """Stop browser and Camoufox."""
        if self._browser:
            await self._browser.close()
            self._browser = None

        self._camoufox = None

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