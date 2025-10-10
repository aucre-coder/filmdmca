from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class MovieInfo:
    """Film-Informationen"""
    title: str
    source_url: List[str]
    tmdb_id: Optional[int] = None
    tmdb_title: Optional[str] = None
    release_year: Optional[str] = None
    disney_company: Optional[str] = None
    release_info: str = ""
    imdb_rating: str = ""
    video_links: List[Dict] = None
    found_date: str = None

    def __post_init__(self):
        if self.video_links is None:
            self.video_links = []
        if self.found_date is None:
            self.found_date = datetime.now().isoformat()