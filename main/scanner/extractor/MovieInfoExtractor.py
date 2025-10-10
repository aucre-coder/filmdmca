"""Movie information extraction coordinator."""

import traceback
from typing import Optional, List, Dict
from urllib.parse import urljoin
from playwright.async_api import Locator, Page  # ✅ Changed to async_api

from main.scanner.extractor.MetadataExtractor import MetadataExtractor
from main.scanner.extractor.VideoLinkExtractor import VideoLinkExtractor


class MovieInfoExtractor:
    """
    Extracts complete movie information from article elements.

    Responsibilities:
    - Coordinating metadata extraction
    - Coordinating video link extraction
    - Navigating to detail pages
    - Creating MovieInfo objects
    """

    def __init__(self, metadata_extractor: MetadataExtractor,
                 video_link_extractor: VideoLinkExtractor,
                 base_url: str):
        """
        Initialize movie info extractor.

        Args:
            metadata_extractor: MetadataExtractor instance
            video_link_extractor: VideoLinkExtractor instance
            base_url: Base URL of the target site
        """
        self.metadata_extractor = metadata_extractor
        self.video_link_extractor = video_link_extractor
        self.base_url = base_url

    async def extract_from_article(self, article: Locator, page: Page) -> Optional['MovieInfo']:  # ✅ Added async
        """
        Extract movie information from an article element.

        Args:
            article: Article locator
            page: Page instance for navigation

        Returns:
            MovieInfo object or None if extraction failed
        """
        try:
            # Extract basic metadata
            title = await self.metadata_extractor.extract_title(article)  # ✅ Added await
            if not title:
                return None

            source_url = await self.metadata_extractor.extract_source_url(article, self.base_url)  # ✅ Added await
            release_info = await self.metadata_extractor.extract_release_info(article)  # ✅ Added await
            imdb_rating = await self.metadata_extractor.extract_imdb_rating(article)  # ✅ Added await

            # Extract video links from detail pages

            # Import MovieInfo here to avoid circular imports
            from main.data.MovieInfo import MovieInfo

            return MovieInfo(
                title=title,
                source_url=source_url if source_url else [],  # ✅ Fixed: source_url is already a list
                video_links=[],
                release_info=release_info,
                imdb_rating=imdb_rating
            )

        except Exception as e:
            print(f"Error extracting movie info: {e}")
            traceback.print_exc()
            return None