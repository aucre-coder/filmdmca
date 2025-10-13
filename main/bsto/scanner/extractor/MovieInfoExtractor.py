import traceback
from typing import Optional, List
from urllib.parse import urljoin
from playwright.async_api import Locator, Page

from main.bsto.scanner.extractor.MetadataExtractor import MetadataExtractor
from main.bsto.scanner.extractor.VideoLinkExtractor import VideoLinkExtractor


class MovieInfoExtractor:

    def __init__(self, metadata_extractor: MetadataExtractor,
                 video_link_extractor: VideoLinkExtractor,
                 base_url: str):
        self.metadata_extractor = metadata_extractor
        self.video_link_extractor = video_link_extractor
        self.base_url = base_url

    async def extract_from_series_link(self, series_link: Locator) -> Optional['MovieInfo']:
        try:
            title = await self.metadata_extractor.extract_title(series_link)
            if not title:
                return None

            source_url = await self.metadata_extractor.extract_source_url(series_link, self.base_url)

            from main.data.MovieInfo import MovieInfo

            return MovieInfo(
                title=title,
                source_url=source_url if source_url else [],
                video_links=[],
                release_info="",
                imdb_rating=""
            )

        except Exception as e:
            print(f"Error extracting series info: {e}")
            traceback.print_exc()
            return None

    async def extract_series_metadata(self, page: Page, movie_info: 'MovieInfo') -> None:
        try:
            body = page.locator('body')
            
            genres = await self.metadata_extractor.extract_genres(body)
            years = await self.metadata_extractor.extract_production_years(body)
            description = await self.metadata_extractor.extract_description(body)
            
            if genres:
                movie_info.release_info = f"Genres: {genres}"
            if years:
                movie_info.release_info += f" | Years: {years}" if movie_info.release_info else f"Years: {years}"
            
        except Exception as e:
            print(f"Error extracting series metadata: {e}")
            traceback.print_exc()

    async def extract_episode_links(self, page: Page) -> List[str]:
        episode_urls = []
        
        try:
            episode_links = await page.locator('table.episodes tr td a[href*="serie/"]').all()
            
            seen_urls = set()
            for link in episode_links:
                try:
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                    
                    if href.count('/') >= 5:
                        full_url = urljoin(self.base_url, href)
                        
                        if full_url not in seen_urls:
                            episode_urls.append(full_url)
                            seen_urls.add(full_url)
                            
                except Exception:
                    continue
                    
            print(f"  Found {len(episode_urls)} episode links")
            
        except Exception as e:
            print(f"Error extracting episode links: {e}")
            traceback.print_exc()
        
        return episode_urls
