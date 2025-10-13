import sqlite3
from typing import List, Dict
from urllib.parse import urlparse
import os


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Create database and table if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS streaminglinks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    host TEXT NOT NULL,
                    url TEXT NOT NULL,
                    website TEXT NOT NULL
                )
            ''')
            conn.commit()

    def _extract_host_from_url(self, url: str) -> str:
        """Extract the host/domain from a video URL"""
        try:
            parsed = urlparse(url)
            # Get the domain (e.g., voe.sx, streamtape.com)
            host = parsed.netloc
            # Remove 'www.' prefix if present
            if host.startswith('www.'):
                host = host[4:]
            return host
        except Exception as e:
            print(f"Error parsing URL {url}: {e}")
            return "unknown"

    def insert_video_links(self, company: str, video_links: List[Dict], website: str) -> int:
        """
        Insert video links into the database

        Args:
            company: Disney company name (e.g., "Walt Disney Pictures")
            video_links: List of video link dictionaries
            website: Source website (e.g., "bs.to")

        Returns:
            Number of links inserted
        """
        if not video_links:
            return 0

        inserted_count = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for link in video_links:
                # Extract URL from the link dictionary
                # Adjust this based on your actual video_links structure
                url = link.get('url') or link.get('link') or str(link)

                if not url or not isinstance(url, str):
                    continue

                # Extract host from URL
                host = self._extract_host_from_url(url)

                try:
                    cursor.execute('''
                        INSERT INTO streaminglinks (company, host, url, website)
                        VALUES (?, ?, ?, ?)
                    ''', (company, host, url, website))
                    inserted_count += 1
                except sqlite3.Error as e:
                    print(f"Error inserting URL {url}: {e}")

            conn.commit()

        return inserted_count

    def get_link_count(self) -> int:
        """Get total number of links in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM streaminglinks')
            return cursor.fetchone()[0]

    def get_links_by_company(self, company: str) -> List[Dict]:
        """Get all links for a specific company"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, company, host, url, website 
                FROM streaminglinks 
                WHERE company = ?
            ''', (company,))

            columns = ['id', 'company', 'host', 'url', 'website']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]