import re
from typing import Optional, Dict
import requests


class TMDbClient:
    """
    Verbesserter API-Client für TMDb

    Features:
    - Automatische TV-Serien Erkennung
    - Multi-Strategie-Suche (Movie → TV → ohne Jahr → Ultra-Clean)
    - Erweiterte Titel-Bereinigung (Episode-Marker, Sprach-Tags, etc.)
    - Unterstützung für Movies und TV-Serien
    """

    def __init__(self, config):
        self.config = config
        self.api_calls = 0

    def search_movie(self, title: str) -> Optional[Dict]:
        """
        Sucht Film oder TV-Serie in TMDb

        Strategien (in dieser Reihenfolge):
        1. Movie-Suche mit Jahr (außer bei offensichtlichen TV-Serien)
        2. TV-Suche mit Jahr
        3. Movie-Suche ohne Jahr
        4. TV-Suche ohne Jahr
        5. Ultra-bereinigte Suche (entfernt auch Sonderzeichen)

        Returns:
            Dict mit result + 'media_type' key ('movie' oder 'tv')
        """
        year = self._extract_year(title)
        clean_title = self._clean_title(title)
        is_likely_tv = self._is_likely_tv_series(title)

        # Debug-Ausgabe
        if is_likely_tv:
            print(f"    [TV-Marker erkannt]", end=' ')

        # Strategie 1: Movie-Suche (außer offensichtlich TV)
        if not is_likely_tv:
            result = self._search_endpoint('movie', clean_title, year)
            if result:
                result['media_type'] = 'movie'
                return result

        # Strategie 2: TV-Suche
        result = self._search_endpoint('tv', clean_title, year)
        if result:
            result['media_type'] = 'tv'
            return result

        # Strategie 3: Ohne Jahr versuchen (falls Jahr vorhanden war)
        if year:
            if not is_likely_tv:
                result = self._search_endpoint('movie', clean_title, None)
                if result:
                    result['media_type'] = 'movie'
                    return result

            result = self._search_endpoint('tv', clean_title, None)
            if result:
                result['media_type'] = 'tv'
                return result

        # Strategie 4: Ultra-Clean Fallback
        ultra_clean = self._ultra_clean_title(clean_title)
        if ultra_clean != clean_title and len(ultra_clean) > 2:
            if not is_likely_tv:
                result = self._search_endpoint('movie', ultra_clean, year)
                if result:
                    result['media_type'] = 'movie'
                    return result

            result = self._search_endpoint('tv', ultra_clean, year)
            if result:
                result['media_type'] = 'tv'
                return result

        return None

    def _search_endpoint(self, endpoint_type: str, title: str, year: Optional[str]) -> Optional[Dict]:
        """
        Führt Suche auf spezifischem Endpoint durch

        Args:
            endpoint_type: 'movie' oder 'tv'
            title: Bereinigter Titel
            year: Jahr (optional)
        """
        if not title or len(title) < 2:
            return None

        params = {
            'api_key': self.config.TMDB_API_KEY,
            'query': title,
            'language': 'de-DE'
        }

        # TV-Serien verwenden 'first_air_date_year' statt 'year'
        if year:
            if endpoint_type == 'tv':
                params['first_air_date_year'] = year
            else:
                params['year'] = year

        try:
            url = f"{self.config.TMDB_BASE_URL}/search/{endpoint_type}"
            response = requests.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
            print(" Browser-URL:", response.url)
            self.api_calls += 1

            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    return data['results'][0]

        except Exception as e:
            print(f" API Fehler ({endpoint_type}): {e}")

        return None

    def get_movie_details(self, movie_id: int, media_type: str = 'movie') -> Optional[Dict]:
        """
        Holt detaillierte Informationen

        Args:
            movie_id: TMDb ID
            media_type: 'movie' oder 'tv'
        """
        try:
            url = f"{self.config.TMDB_BASE_URL}/{media_type}/{movie_id}"
            params = {
                'api_key': self.config.TMDB_API_KEY,
                'language': 'de-DE'
            }

            response = requests.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
            self.api_calls += 1

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            print(f" Details-Fehler: {e}")

        return None

    @staticmethod
    def _is_likely_tv_series(title: str) -> bool:
        """
        Prüft ob Titel vermutlich TV-Serie ist

        Erkannte Muster:
        - S01E07, S1E7 (Season/Episode)
        - Staffel 1, Season 1
        - Episode 7, Folge 7
        """
        tv_patterns = [
            r'S\d{1,2}E\d{1,2}',  # S01E07, S1E7
            r'\bS\d{1,2}\b',  # S01, S1 (allein)
            r'Staffel\s+\d+',  # Staffel 1
            r'Season\s+\d+',  # Season 1
            r'Episode\s+\d+',  # Episode 7
            r'Folge\s+\d+',  # Folge 7
            r'E\d{1,2}\b',  # E07 (allein)
        ]

        for pattern in tv_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def _extract_year(title: str) -> Optional[str]:
        """
        Extrahiert Jahr aus Titel (2000-2099)

        Beispiele:
        - "Moana 2 (2024)" → "2024"
        - "Star Wars 2023" → "2023"
        """
        match = re.search(r'\b(20\d{2})\b', title)
        return match.group(1) if match else None

    @staticmethod
    def _clean_title(title: str) -> str:
        """
        Hauptbereinigung des Titels

        Entfernt:
        1. Episode/Staffel-Marker (S01E07, Staffel 1, etc.)
        2. Sprach-Tags (*ENGLISH*, [GERMAN], (DE), etc.)
        3. Jahre (2024, (2024))
        4. Klammern und eckige Klammern mit Inhalt
        5. Video-Qualitäts-Tags (1080p, 4K, BluRay, etc.)
        6. Codec-Tags (x264, HEVC, etc.)
        7. Abgeschnittene Zeichen am Ende
        8. Mehrfache/führende/folgende Leerzeichen
        """
        if not title:
            return ""

        # 1. Episode/Staffel-Marker entfernen
        title = re.sub(r'S\d{1,2}E\d{1,2}', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\bS\d{1,2}\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\bE\d{1,2}\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'Staffel\s+\d+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'Season\s+\d+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'Episode\s+\d+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'Folge\s+\d+', '', title, flags=re.IGNORECASE)

        # 2. Sprach-Tags entfernen
        # *ENGLISH*, [GERMAN], (DE), etc.
        title = re.sub(r'\*[A-Z]+\*', '', title)
        title = re.sub(r'\[[A-Z]{2,}\]', '', title)
        title = re.sub(r'\([A-Z]{2}\)', '', title)

        # 3. Video-Qualitäts-Tags entfernen
        quality_patterns = [
            r'\b(720p|1080p|2160p|4K|8K)\b',
            r'\b(BluRay|BDRip|DVDRip|WEBRip|HDTV)\b',
            r'\b(x264|x265|HEVC|H\.264|H\.265)\b',
            r'\b(AAC|AC3|DTS|FLAC)\b',
        ]
        for pattern in quality_patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)

        # 4. Jahre entfernen (2000-2099)
        title = re.sub(r'\b20\d{2}\b', '', title)

        # 5. Klammern und eckige Klammern mit Inhalt entfernen
        title = re.sub(r'\([^)]*\)', '', title)
        title = re.sub(r'\[[^\]]*\]', '', title)
        title = re.sub(r'\{[^}]*\}', '', title)

        # 6. Abgeschnittene einzelne Buchstaben am Ende entfernen
        # "Pappbecher t" → "Pappbecher"
        title = re.sub(r'\s+[a-z]\s*$', '', title, flags=re.IGNORECASE)

        # 7. Mehrfache Leerzeichen zusammenfassen
        title = re.sub(r'\s+', ' ', title)

        # 8. Führende/folgende Sonderzeichen entfernen
        title = re.sub(r'^[\s\-:._]+|[\s\-:._]+$', '', title)

        # 9. Trim
        title = title.strip()

        return title

    @staticmethod
    def _ultra_clean_title(title: str) -> str:
        """
        Noch aggressivere Bereinigung für schwierige Fälle

        Entfernt ALLE Sonderzeichen außer Leerzeichen
        Verwendung als letzter Fallback
        """
        if not title:
            return ""

        # Nur Buchstaben, Zahlen und Leerzeichen behalten
        title = re.sub(r'[^\w\s]', ' ', title, flags=re.UNICODE)

        # Mehrfache Leerzeichen
        title = re.sub(r'\s+', ' ', title)

        return title.strip()