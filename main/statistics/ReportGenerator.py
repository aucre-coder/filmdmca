import datetime
import json
from typing import List, Dict

from main.data import Config
from main.data.MovieInfo import MovieInfo
from main.statistics import Statistics


class ReportGenerator:
    """Erstellt Reports"""

    @staticmethod
    def generate_json(findings: List[MovieInfo], stats: Statistics, config: Config) -> tuple[str, Dict]:
        """Erstellt JSON-Report"""
        report = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'target': config.TARGET_SITE,
                'verification': 'TMDb API',
                'statistics': stats.to_dict()
            },
            'findings': [ReportGenerator._movie_to_dict(f) for f in findings],
            'summary': {
                'disney_movies_found': len(findings),
                'total_urls': stats.urls_collected,
                'companies': ReportGenerator._count_companies(findings),
                'hosters': ReportGenerator._count_hosters(findings)
            }
        }

        filename = f'disney_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Report: {filename}")
        return filename, report

    @staticmethod
    def generate_email(findings: List[MovieInfo], stats: Statistics) -> str:
        """Erstellt E-Mail-Text"""
        companies = ReportGenerator._count_companies(findings)
        hosters = ReportGenerator._count_hosters(findings)

        text = f"""Subject: Copyright Infringement Report - {len(findings)} Disney Films

Dear Disney Anti-Piracy Team,

Unauthorized Disney content found on filmpalast.to.
Verified via TMDb API.

SUMMARY:
- Disney films: {len(findings)}
- Total URLs: {stats.urls_collected}
- Date: {datetime.now().strftime('%Y-%m-%d')}

COMPANIES:
"""

        for company, count in companies.items():
            text += f"- {company}: {count} films\n"

        text += "\nHOSTERS:\n"
        for hoster, count in hosters.items():
            text += f"- {hoster}: {count} URLs\n"

        text += "\n\nDETAILS:\n\n"

        for i, f in enumerate(findings, 1):
            text += f"{i}. {f.title} ({f.release_year})\n"
            text += f"   TMDb: {f.tmdb_id}\n"
            text += f"   Company: {f.disney_company}\n"
            text += f"   Source: {f.source_url}\n"
            text += f"   URLs ({len(f.video_links)}):\n"
            for link in f.video_links:
                text += f"   - {link['url']}\n"
            text += "\n"

        text += "\nComplete data in JSON attachment.\n\nBest regards"

        filename = f'email_{datetime.now().strftime("%Y%m%d")}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"✓ E-Mail: {filename}")
        return text

    @staticmethod
    def _movie_to_dict(movie: MovieInfo) -> Dict:
        """Konvertiert MovieInfo zu Dict"""
        return {
            'title': movie.title,
            'tmdb_id': movie.tmdb_id,
            'tmdb_title': movie.tmdb_title,
            'release_year': movie.release_year,
            'disney_company': movie.disney_company,
            'source_url': movie.source_url,
            'release_info': movie.release_info,
            'imdb_rating': movie.imdb_rating,
            'video_links': movie.video_links,
            'found_date': movie.found_date
        }

    @staticmethod
    def _count_companies(findings: List[MovieInfo]) -> Dict[str, int]:
        """Zählt Disney-Firmen"""
        companies = {}
        for f in findings:
            if f.disney_company:
                companies[f.disney_company] = companies.get(f.disney_company, 0) + 1
        return companies

    @staticmethod
    def _count_hosters(findings: List[MovieInfo]) -> Dict[str, int]:
        """Zählt Hoster"""
        hosters = {}
        for f in findings:
            for link in f.video_links:
                h = link['hoster']
                hosters[h] = hosters.get(h, 0) + 1
        return hosters
