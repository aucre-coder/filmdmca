from typing import Dict, Optional

from main.data import Config


class DisneyVerifier:
    """Prüft ob Content von Disney ist"""

    def __init__(self, config: Config):
        self.config = config

    def is_disney_content(self, movie_details: Dict) -> tuple[bool, Optional[str]]:
        if not movie_details:
            return False, None

        # Production Companies
        for company in movie_details.get('production_companies', []):
            print("company",company)
            if company['id'] in self.config.DISNEY_COMPANY_IDS:
                return True, company['name']

        # Networks
        for network in movie_details.get('networks', []):
            if network['id'] in self.config.DISNEY_NETWORK_IDS:
                return True, network['name']

        return False, None
