from typing import Dict


class Statistics:
    """Verwaltet Statistiken"""

    def __init__(self):
        self.pages_scanned = 0
        self.movies_checked = 0
        self.disney_found = 0
        self.urls_collected = 0
        self.api_calls = 0
        self.errors = 0

    def to_dict(self) -> Dict:
        """Konvertiert zu Dictionary"""
        return {
            'pages_scanned': self.pages_scanned,
            'movies_checked': self.movies_checked,
            'disney_found': self.disney_found,
            'urls_collected': self.urls_collected,
            'api_calls': self.api_calls,
            'errors': self.errors
        }

    def print(self):
        """Zeigt Statistiken"""
        print("\n" + "=" * 60)
        print("STATISTIKEN")
        print("=" * 60)
        print(f"Übersichtsseiten: {self.pages_scanned}")
        print(f"Filme geprüft: {self.movies_checked}")
        print(f"Disney-Filme: {self.disney_found}")
        print(f"Video-URLs: {self.urls_collected}")
        print(f"API-Calls: {self.api_calls}")
        print(f"Fehler: {self.errors}")
        print("=" * 60)
