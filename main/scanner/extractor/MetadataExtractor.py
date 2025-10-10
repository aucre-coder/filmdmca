"""Metadata extraction from article elements."""

import re
import traceback
from typing import List
from urllib.parse import urljoin

from playwright.async_api import Locator  # ✅ Changed to async_api


class MetadataExtractor:
    """
    Extracts metadata from article elements.

    Responsibilities:
    - Extracting release information
    - Extracting IMDb ratings
    - Extracting titles
    """

    @staticmethod
    async def extract_title(article: Locator) -> str:  # ✅ Added async
        """
        Extract movie title from article.

        Args:
            article: Article locator

        Returns:
            Movie title or empty string
        """
        try:
            elem = article.locator('h2.h2-start a').first
            if await elem.count() > 0:  # ✅ Added await
                return (await elem.text_content()).strip()  # ✅ Added await
        except Exception:
            pass
        return ""

    @staticmethod
    async def extract_source_url(article: Locator, base_url: str) -> List[str]:  # ✅ Added async
        """Extract source URL from article.

        Args:
            article: Article locator
            base_url: Base URL to prepend

        Returns:
            Full source URL or empty string
        """
        try:
            liste = []
            title_elem = article.locator('h2.h2-start a').first
            if await title_elem.count() > 0:  # ✅ Added await
                href = await title_elem.get_attribute('href')  # ✅ Added await
                if href:
                    # urljoin handles relative and absolute URLs correctly
                    liste.append(urljoin(base_url, href))
                    return liste
        except Exception as e:
            print("error", e)
            traceback.print_exc()
        return []  # ✅ Added return for empty case

    @staticmethod
    async def extract_release_info(article: Locator) -> str:  # ✅ Added async
        """
        Extract release information from article.

        Args:
            article: Article locator

        Returns:
            Release info string or empty string
        """
        try:
            elem = article.locator('span.releaseTitleHome').first
            if await elem.count() > 0:  # ✅ Added await
                return (await elem.text_content()).strip()  # ✅ Added await
        except Exception:
            pass
        return ""

    @staticmethod
    async def extract_imdb_rating(article: Locator) -> str:  # ✅ Added async
        """
        Extract IMDb rating from article.

        Args:
            article: Article locator

        Returns:
            IMDb rating string or empty string
        """
        try:
            info_div = article.locator('.toggle-content').first
            if await info_div.count() > 0:  # ✅ Added await
                text = await info_div.text_content()  # ✅ Added await
                match = re.search(r'Imdb:\s*([\d.]+)/10', text)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return ""