import asyncio
import traceback
from typing import List, Dict
from urllib.parse import urljoin

from db.DatabaseManager import DatabaseManager
from main.client.TMbdClient import TMDbClient
from main.data import Config, MovieInfo
from main.bsto.scanner.scanner.ContentScanner import ContentScanner
from main.bsto.scanner.extractor.VideoLinkExtractor import VideoLinkExtractor
from main.bsto.fetcher.PageFetcher import PageFetcher
from main.bsto.manager.BrowserManager import BrowserManager
from main.statistics import ReportGenerator
from main.statistics.Statistics import Statistics
from main.verifier.DisneyVerifier import DisneyVerifier


class DisneyContentScannerCaller:

    def __init__(self, config: Config):
        self.config = config
        self.tmdb_client = TMDbClient(config)
        self.verifier = DisneyVerifier(config)
        self.scanner = ContentScanner(config)
        self.stats = Statistics()
        self.findings: List[MovieInfo] = []
        self.page = None
        self.video_link_extractor = VideoLinkExtractor()
        self.browser_manager = BrowserManager(headless=True)
        self.page_fetcher = None
        db_path = r"C:\Users\aurel\PycharmProjects\filmdmca\db\dmcalinks.db"
        self.db_manager = DatabaseManager(db_path)

    async def initialize(self):
        await self.browser_manager.start()
        browser = await self.browser_manager.get_browser()

        self.page_fetcher = PageFetcher(
            browser=browser,
            timeout=self.config.REQUEST_TIMEOUT * 1000
        )

        await self.scanner.initialize()

    async def cleanup(self):
        await self.browser_manager.stop()

    async def run(self, max_series: int = 10000, max_episodes_per_series: int = 100):
        print("Disney Content Scanner - BS.TO")
        print(f"Ziel: {self.config.TARGET_SITE}")
        print("Verifikation: TMDb API\n")

        series_list = await self.scanner.scan_series_list(max_series)
        self.stats.pages_scanned = 1

        await self._scan_series(series_list, max_episodes_per_series)

        if self.findings:
            # Instead of generating report, insert into database
            total_inserted = 0
            website = self.config.TARGET_SITE or "bs.to"

            for series in self.findings:
                inserted = self.db_manager.insert_video_links(
                    company=series.disney_company,
                    video_links=series.video_links,
                    website=website
                )
                total_inserted += inserted

            self.stats.api_calls = self.tmdb_client.api_calls
            self.stats.print()

            print(f"\n✓ Fertig!")
            print(f"→ {total_inserted} Links wurden in die Datenbank eingefügt")
            print(f"→ Datenbank: {self.db_manager.db_path}")
            print(f"→ Gesamt Links in DB: {self.db_manager.get_link_count()}")
        else:
            print("\nKeine Disney-Serien gefunden.")
            self.stats.print()

    async def _scan_series(self, series_list: List[MovieInfo], max_episodes_per_series: int):
        print(f"=== Prüfe {len(series_list)} Serien ===\n")

        for i, series in enumerate(series_list, 1):
            print(f"[{i}/{len(series_list)}] ", end='')

            self.stats.movies_checked += 1

            print("series titel", series.title)
            tv_data = self.tmdb_client.search_tv(series.title)
            if not tv_data:
                print(f"✗ '{series.title}' nicht in TMDb")
                continue

            details = self.tmdb_client.get_tv_details(tv_data['id'])
            if not details:
                continue

            is_disney, company = self.verifier.is_disney_content(details)
            if not is_disney:
                print(f"○ '{series.title}' ist kein Disney-Inhalt")
                continue

            series.tmdb_id = tv_data['id']
            series.tmdb_title = details['name']
            series.release_year = details.get('first_air_date', '')[:4]
            series.disney_company = company

            try:
                await self.scanner.scan_series_episodes(series, max_episodes_per_series)

                if len(series.source_url) > 1:
                    episode_urls = series.source_url[1:]
                    
                    print(f"  Processing {len(episode_urls)} episodes...")
                    series.video_links = await self._extract_video_links_from_episodes(episode_urls)

                    if series.video_links:
                        self.findings.append(series)
                        self.stats.disney_found += 1
                        self.stats.urls_collected += len(series.video_links)
                        print(f"✓ Disney-Serie: {series.title} ({company})")
                        print(f"  → {len(series.video_links)} Links gesammelt")
                    else:
                        print(f"✓ Disney-Serie, aber keine Links")
                else:
                    print(f"✓ Disney-Serie, aber keine Episoden gefunden")

            except Exception as e:
                print(f"  ✗ Error extracting video links for {series.title}: {e}")

            await asyncio.sleep(self.config.MOVIE_DELAY)

    async def _extract_video_links_from_episodes(self, episode_urls: List[str]) -> List[Dict]:
        all_video_links = []
        episode_urls = list(dict.fromkeys(episode_urls))
        
        for url in episode_urls[:5]:
            try:
                if isinstance(url, list):
                    url = url[0] if url else None

                if not url or not isinstance(url, str):
                    print(f"    ✗ Skipping invalid URL: {url}")
                    continue

                page = await self.page_fetcher.fetch(url)

                links = await self.video_link_extractor.extract_video_links(page)
                all_video_links.extend(links)

                await page.close()

            except Exception as e:
                print(f"    ✗ Error extracting from {url}: {e}")
                traceback.print_exc()
                continue

        return all_video_links
