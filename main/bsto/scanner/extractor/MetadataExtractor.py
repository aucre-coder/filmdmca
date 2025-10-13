import re
import traceback
from typing import List
from urllib.parse import urljoin
from playwright.async_api import Locator


class MetadataExtractor:

    @staticmethod
    async def extract_title(series_link: Locator) -> str:
        try:
            text = await series_link.text_content()
            if text:
                return text.strip()
        except Exception:
            pass
        return ""

    @staticmethod
    async def extract_source_url(series_link: Locator, base_url: str) -> List[str]:
        try:
            href = await series_link.get_attribute('href')
            if href:
                full_url = urljoin(base_url, href)
                return [full_url]
        except Exception as e:
            print("error", e)
            traceback.print_exc()
        return []

    @staticmethod
    async def extract_genres(series_page: Locator) -> str:
        try:
            genre_div = series_page.locator('.infos div:has(span:text("Genres")) p')
            if await genre_div.count() > 0:
                genre_text = await genre_div.first.text_content()
                if genre_text:
                    return genre_text.strip()
        except Exception:
            pass
        return ""

    @staticmethod
    async def extract_production_years(series_page: Locator) -> str:
        try:
            years_div = series_page.locator('.infos div:has(span:text("Produktionsjahre")) p em')
            if await years_div.count() > 0:
                years_text = await years_div.first.text_content()
                if years_text:
                    return years_text.strip()
        except Exception:
            pass
        return ""

    @staticmethod
    async def extract_description(series_page: Locator) -> str:
        try:
            desc_elem = series_page.locator('#sp_left > p').first
            if await desc_elem.count() > 0:
                desc_text = await desc_elem.text_content()
                if desc_text:
                    return desc_text.strip()
        except Exception:
            pass
        return ""
