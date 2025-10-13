from typing import List
from dataclasses import dataclass


@dataclass
class Config:
    """Zentrale Konfiguration"""
    TMDB_API_KEY: str
    TMDB_BASE_URL: str
    TARGET_SITE: str
    REQUEST_TIMEOUT: int = 15
    PAGE_DELAY: float = 2.0
    MOVIE_DELAY: float = 1.5

    DISNEY_COMPANY_IDS: List[int] = None
    DISNEY_NETWORK_IDS: List[int] = None

    MAX_CONCURRENT: float = 5


    def __post_init__(self):
        if self.DISNEY_COMPANY_IDS is None:
            self.DISNEY_COMPANY_IDS = [
                2,  # Walt Disney Pictures
                3,  # Pixar
                420,  # Marvel Studios
                1,  # Lucasfilm
                127928,  # 20th Century Studios
                17,  # Walt Disney Animation Studios
                7295,  # Searchlight Pictures
                6125,  # Touchstone Pictures
                9195,  # Hollywood Pictures
            ]

        if self.DISNEY_NETWORK_IDS is None:
            self.DISNEY_NETWORK_IDS = [
                2739,  # Disney+
                88,  # FX
                1024,  # National Geographic
                2,  # ABC
                1667,  # Freeform
                44,  # Disney Channel
                2919,  # Disney XD
                453,  # Hulu
            ]