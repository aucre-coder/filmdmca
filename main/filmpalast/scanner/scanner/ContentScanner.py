"""Main content scanner orchestrator."""

import asyncio
import traceback
from typing import List

from main.data import Config
from main.data.MovieInfo import MovieInfo

from main.filmpalast.manager.BrowserManager import BrowserManager
from main.filmpalast.fetcher.PageFetcher import PageFetcher
from main.filmpalast.scanner.extractor.MetadataExtractor import MetadataExtractor
from main.filmpalast.scanner.extractor.VideoLinkExtractor import VideoLinkExtractor
from main.filmpalast.scanner.extractor.MovieInfoExtractor import MovieInfoExtractor

class ContentScanner:
    """
    Main facade for scanning website content.

    This class orchestrates all scanning operations by coordinating:
    - Browser management
    - Page fetching
    - Movie information extraction

    Design Pattern: Facade
    Benefits:
    - Simple interface for complex subsystem
    - Loose coupling through dependency injection
    - Easy to test individual components
    - Follows Single Responsibility Principle
    """

    def __init__(self, config: Config):
        """
        Initialize content scanner with all dependencies.

        Args:
            config: Configuration object
        """
        self.config = config

        # Initialize dependencies (but don't start browser yet)
        self.browser_manager = BrowserManager(headless=True)
        self.video_link_extractor = VideoLinkExtractor()
        self.page_fetcher = None  # Will be initialized in initialize()

        # Initialize extractors
        metadata_extractor = MetadataExtractor()
        video_link_extractor = VideoLinkExtractor()

        self.movie_info_extractor = MovieInfoExtractor(
            metadata_extractor=metadata_extractor,
            video_link_extractor=video_link_extractor,
            base_url=config.TARGET_SITE
        )

    async def initialize(self):
        """Initialize async components."""
        await self.browser_manager.start()
        browser = await self.browser_manager.get_browser()

        self.page_fetcher = PageFetcher(
            browser=browser,
            timeout=self.config.REQUEST_TIMEOUT * 1000
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.browser_manager.stop()

    async def scan_overview_pages(self, num_pages: int) -> List[MovieInfo]:
        """
        Scan overview pages and extract movie information.

        This is the main public interface that clients will use.

        Args:
            num_pages: Number of pages to scan

        Returns:
            List of MovieInfo objects
        """
        print(f"\n=== Scanning {num_pages} pages ===\n")

        movies = []

        for page_num in range(1, num_pages + 1):
            try:
                url = f"{self.config.TARGET_SITE}/page/{page_num}"
                print(f"Page {page_num}/{num_pages}...")
                print("URL:", url)

                # Fetch page
                page = await self.page_fetcher.fetch(url)
                if not page:
                    print("Error! Page not loaded!")
                    continue

                # Extract movies from page
                page_movies = await self._extract_movies_from_page(page)
                movies.extend(page_movies)

                # Cleanup
                await page.close()
                await asyncio.sleep(self.config.PAGE_DELAY)

            except Exception as e:
                print(f"Error on page {page_num}: {e}")
                traceback.print_exc()

        print(f"\n{len(movies)} movies scanned\n")
        return movies

    async def _extract_movies_from_page(self, page) -> List[MovieInfo]:
        """
        Extract all movies from a single page.

        Args:
            page: Page instance

        Returns:
            List of MovieInfo objects
        """
        movies = []  # Initialize list to collect movies

        try:
            # Store the listing page URL so we can return to it
            listing_url = page.url

            # Find all movie articles
            articles = await page.locator("article").all()
            print(f"  → {len(articles)} movies found")

            # PHASE 1: Collect all basic movie data WITHOUT navigating
            for article in articles:
                try:
                    movie = await self.movie_info_extractor.extract_from_article(article, page)
                    if movie:
                        # Collect stream detail links for later
                        detail_links = await article.locator('a[href*="/stream/"]').all()
                        detail_urls = []

                        for link in detail_links:
                            href = await link.get_attribute('href')
                            if href:
                                from urllib.parse import urljoin
                                absolute_url = urljoin(listing_url, href)
                                detail_urls.append(absolute_url)

                        # Extend the source_url list with detail URLs
                        # (Changed from append to extend to avoid nested lists)
                        if detail_urls:
                            movie.source_url.extend(detail_urls)

                        # Add the movie to our collection
                        movies.append(movie)

                except Exception as e:
                    print(f"  ✗ Error extracting article: {e}")
                    traceback.print_stack()

        except Exception as e:
            print(f"  ✗ Error extracting movies from page: {e}")

        return movies  # Return the collected movies