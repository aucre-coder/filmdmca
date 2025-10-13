import asyncio
import traceback
from typing import List

from main.data import Config
from main.data.MovieInfo import MovieInfo

from main.bsto.manager.BrowserManager import BrowserManager
from main.bsto.fetcher.PageFetcher import PageFetcher
from main.bsto.scanner.extractor.MetadataExtractor import MetadataExtractor
from main.bsto.scanner.extractor.VideoLinkExtractor import VideoLinkExtractor
from main.bsto.scanner.extractor.MovieInfoExtractor import MovieInfoExtractor

class ContentScanner:

    def __init__(self, config: Config):
        self.config = config
        self.browser_manager = BrowserManager(headless=True)
        self.video_link_extractor = VideoLinkExtractor()
        self.page_fetcher = None

        metadata_extractor = MetadataExtractor()
        video_link_extractor = VideoLinkExtractor()

        self.movie_info_extractor = MovieInfoExtractor(
            metadata_extractor=metadata_extractor,
            video_link_extractor=video_link_extractor,
            base_url=config.TARGET_SITE
        )

    async def initialize(self):
        await self.browser_manager.start()
        browser = await self.browser_manager.get_browser()

        self.page_fetcher = PageFetcher(
            browser=browser,
            timeout=self.config.REQUEST_TIMEOUT * 1000
        )

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser_manager.stop()

    async def scan_series_list(self, max_series: int = 10) -> List[MovieInfo]:
        print(f"\n=== Scanning up to {max_series} series ===\n")

        series_list = []

        try:
            url = f"{self.config.TARGET_SITE}/andere-serien"
            print(f"Fetching series list from: {url}")

            page = await self.page_fetcher.fetch(url)
            if not page:
                print("Error! Series list page not loaded!")
                return series_list

            series_links = await page.locator('#seriesContainer .genre ul li a').all()
            print(f"  → {len(series_links)} series found")

            for idx, link in enumerate(series_links[:max_series], 1):
                try:
                    series_info = await self.movie_info_extractor.extract_from_series_link(link)
                    if series_info:
                        series_list.append(series_info)
                        print(f"  [{idx}/{max_series}] ✓ {series_info.title}")

                except Exception as e:
                    print(f"  ✗ Error extracting series: {e}")
                    traceback.print_exc()

            await page.close()
            await asyncio.sleep(self.config.PAGE_DELAY)

        except Exception as e:
            print(f"Error scanning series list: {e}")
            traceback.print_exc()

        print(f"\n{len(series_list)} series collected\n")
        return series_list

    async def scan_series_episodes(self, series_info: MovieInfo, max_episodes: int = 5) -> MovieInfo:
        print(f"\nScanning episodes for: {series_info.title}")

        try:
            if not series_info.source_url:
                print("  ✗ No series URL found")
                return series_info

            series_url = series_info.source_url[0]
            print(f"  Opening series page: {series_url}")

            page = await self.page_fetcher.fetch(series_url)
            if not page:
                print("  ✗ Series page not loaded")
                return series_info

            await self.movie_info_extractor.extract_series_metadata(page, series_info)

            episode_urls = await self.movie_info_extractor.extract_episode_links(page)
            
            if series_info.source_url:
                series_info.source_url.extend(episode_urls[:max_episodes])
            else:
                series_info.source_url = episode_urls[:max_episodes]

            await page.close()
            await asyncio.sleep(self.config.PAGE_DELAY)

        except Exception as e:
            print(f"  ✗ Error scanning series episodes: {e}")
            traceback.print_exc()

        return series_info
