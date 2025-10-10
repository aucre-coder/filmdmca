import asyncio
import traceback
from typing import List, Dict
from urllib.parse import urljoin

from main.client.TMbdClient import TMDbClient
from main.data import Config, MovieInfo
from main.scanner.ContentScanner import ContentScanner
from main.scanner.extractor import VideoLinkExtractor
from main.scanner.fetcher.PageFetcher import PageFetcher
from main.scanner.manager.BrowserManager import BrowserManager
from main.statistics import ReportGenerator
from main.statistics.Statistics import Statistics
from main.verifier.DisneyVerifier import DisneyVerifier


class DisneyContentScannerCaller:
    """Hauptklasse - orchestriert alle Komponenten"""

    def __init__(self, config: Config):
        self.config = config
        self.tmdb_client = TMDbClient(config)
        self.verifier = DisneyVerifier(config)
        self.scanner = ContentScanner(config)
        self.stats = Statistics()
        self.findings: List[MovieInfo] = []
        self.page = None  # Will be set during initialization
        self.video_link_extractor = VideoLinkExtractor()
        self.browser_manager = BrowserManager(headless=True)
        self.page_fetcher = None  # Will be initialized in initialize()

    async def initialize(self):
        """Initialize async components."""
        await self.browser_manager.start()
        browser = await self.browser_manager.get_browser()

        self.page_fetcher = PageFetcher(
            browser=browser,
            timeout=self.config.REQUEST_TIMEOUT * 1000
        )

        # Initialize scanner's async components
        await self.scanner.initialize()

    async def cleanup(self):
        """Cleanup async resources."""
        await self.browser_manager.stop()

    async def run(self, num_pages: int = 1):
        """Führt kompletten Scan durch"""
        print("Disney Content Scanner")
        print(f"Ziel: {self.config.TARGET_SITE}")
        print("Verifikation: TMDb API\n")

        # Schritt 1: URLs sammeln
        movie = await self.scanner.scan_overview_pages(num_pages)
        self.stats.pages_scanned = num_pages

        # Schritt 2: Filme prüfen
        await self._scan_movies(movie)

        # Schritt 3: Reports
        if self.findings:
            filename, report = ReportGenerator.generate_json(
                self.findings, self.stats, self.config
            )
            ReportGenerator.generate_email(self.findings, self.stats)

            self.stats.api_calls = self.tmdb_client.api_calls
            self.stats.print()

            print(f"\n✓ Fertig!")
            print(f"→ Sende an: tips@disneyantipiracy.com")
            print(f"→ Anhang: {filename}")
        else:
            print("\nKeine Disney-Filme gefunden.")
            self.stats.print()

    async def _scan_movies(self, movie_info: List[MovieInfo]):
        """Scannt alle Filme"""
        print(f"=== Prüfe {len(movie_info)} Filme ===\n")

        for i, movie in enumerate(movie_info, 1):
            print(f"[{i}/{len(movie_info)}] ", end='')

            self.stats.movies_checked += 1

            # TMDb Suche
            print("movie titel", movie.title, "t")
            movie_data = self.tmdb_client.search_movie(movie.title)
            if not movie_data:
                print(f"✗ '{movie.title}' nicht in TMDb")
                continue

            # Details abrufen
            details = self.tmdb_client.get_movie_details(movie_data['id'])
            if not details:
                continue

            # Disney-Check
            is_disney, company = self.verifier.is_disney_content(details)
            if not is_disney:
                print(f"○ '{movie.title}' ist kein Disney-Film")
                continue

            # Erfolg! Set TMDb info
            movie.tmdb_id = movie_data['id']
            movie.tmdb_title = details['title']
            movie.release_year = details.get('release_date', '')[:4]
            movie.disney_company = company

            # NOW extract video links from the detail URLs (already stored in movie.source_url)
            try:
                if movie.source_url:  # Check if there are detail URLs
                    print("source url", movie.source_url)
                    print(f"  Processing {len(movie.source_url)} detail pages...")

                    # Extract video links from all detail URLs for this movie
                    movie.video_links = await self._extract_video_links_from_urls(
                        movie.source_url
                    )

                    if movie.video_links:
                        self.findings.append(movie)
                        self.stats.disney_found += 1
                        self.stats.urls_collected += len(movie.video_links)
                        print(f"✓ Disney-Film: {movie.title} ({company})")
                        print(f"  → {len(movie.video_links)} Links gesammelt")
                    else:
                        print(f"✓ Disney-Film, aber keine Links")
                else:
                    print(f"✓ Disney-Film, aber keine Detail-URLs")

            except Exception as e:
                print(f"  ✗ Error extracting video links for {movie.title}: {e}")

            await asyncio.sleep(self.config.MOVIE_DELAY)

    async def _extract_video_links_from_urls(self, detail_urls: List[str]) -> List[Dict]:
        """
        Extract video links from a list of detail page URLs.

        Args:
            detail_urls: List of detail page URLs to visit

        Returns:
            List of video link dictionaries
        """
        all_video_links = []
        detail_urls = list(dict.fromkeys(detail_urls))
        for url in detail_urls:
            try:
                if isinstance(url, list):
                    url = url[0] if url else None

                if not url or not isinstance(url, str):
                    print(f"    ✗ Skipping invalid URL: {url}")
                    continue

                # Navigate to detail page
                page = await self.page_fetcher.fetch(url)

                # Extract video links from this page
                links = await self.video_link_extractor.extract_video_links(
                    page.locator("body"),
                    page
                )
                all_video_links.extend(links)

            except Exception as e:
                print(f"    ✗ Error extracting from {url}: {e}")
                traceback.print_exc()
                continue

        return all_video_links