"""Video link extraction from article elements."""

import re
from typing import List, Dict, Set
from httpx._urlparse import urlparse
from playwright.async_api import Locator, Page


async def _extract_hoster_from_watch_episode(link: Locator) -> str:
    """
    Extract hoster name from watchEpisode link element.

    Tries to find hoster from:
    1. <h4> tag inside the link
    2. <i> tag's class or title attribute
    3. Link text content
    """
    try:
        # Try h4 tag
        h4 = link.locator('h4')
        if await h4.count() > 0:
            hoster_text = await h4.first.inner_text()
            if hoster_text and hoster_text.strip():
                return hoster_text.strip()

        # Try icon class
        icon = link.locator('i.icon')
        if await icon.count() > 0:
            icon_elem = icon.first
            # Check title attribute
            title = await icon_elem.get_attribute('title')
            if title:
                # Extract hoster name from "Hoster VOE" -> "VOE"
                match = re.search(r'Hoster\s+(\w+)', title)
                if match:
                    return match.group(1)

            # Check class name
            class_name = await icon_elem.get_attribute('class')
            if class_name:
                # Extract from "icon VOE" -> "VOE"
                classes = class_name.split()
                for cls in classes:
                    if cls.lower() not in ['icon', 'fa', 'fas']:
                        return cls.capitalize()

        # Fallback to link text
        text = await link.inner_text()
        if text and text.strip():
            # Clean up text
            text = text.strip().split('\n')[0].strip()
            if text:
                return text

    except Exception:
        pass

    return "Unknown"


class VideoLinkExtractor:
    """
    Extracts video links from article elements.

    Responsibilities:
    - Extracting links from iframes
    - Extracting links from data attributes
    - Following redirect links (e.g., watchEpisode)
    - Regex-based link extraction
    - Hoster name extraction
    """

    async def extract_video_links(self, article: Locator, page: Page) -> List[Dict]:
        """
        Extract video links from article using multiple strategies.

        Args:
            article: Article locator containing video links
            page: Page instance for context

        Returns:
            List of dictionaries with 'url' and 'hoster' keys
        """
        links = []
        seen_urls: Set[str] = set()

        print("→ Extracting video links (iframe-aware method)...")

        # Strategy 1: Extract from iframes
        await self._extract_from_iframes(article, links, seen_urls)

        # Strategy 2: Extract from watchEpisode redirect links
        await self._extract_from_watch_episode(article, page, links, seen_urls)

        # Strategy 3: Extract from data attributes
        await self._extract_from_data_attributes(article, links, seen_urls)

        # Strategy 4: Regex-based extraction as fallback
        await self._extract_from_regex(article, links, seen_urls)

        # Summary
        if not links:
            print("  ⚠ NO video links found!")
        else:
            print(f"✓ Total: {len(links)} unique video links extracted\n")

        return links

    async def _extract_from_iframes(self, article: Locator, links: List[Dict], seen_urls: Set[str]) -> None:
        """Extract video links from iframe elements."""
        try:
            iframes = await article.locator('iframe').all()
            print(f"  [Iframes] Found: {len(iframes)}")

            for idx, iframe in enumerate(iframes, 1):
                # Standard src attribute
                src = await iframe.get_attribute('src')
                if self._is_valid_url(src) and src not in seen_urls:
                    hoster = self._extract_hoster_name(src)
                    links.append({'url': src, 'hoster': hoster})
                    seen_urls.add(src)
                    print(f"    [{idx}] ✓ {hoster}: {src[:60]}...")

                # Lazy-loading attributes
                for attr in ['data-src', 'data-lazy-src', 'data-url']:
                    lazy_src = await iframe.get_attribute(attr)
                    if self._is_valid_url(lazy_src) and lazy_src not in seen_urls:
                        hoster = self._extract_hoster_name(lazy_src)
                        links.append({'url': lazy_src, 'hoster': hoster})
                        seen_urls.add(lazy_src)
                        print(f"    [{idx}] ✓ {hoster} ({attr}): {lazy_src[:60]}...")

        except Exception as e:
            print(f"  [Iframes] ⚠ Error: {e}")

    async def _extract_from_watch_episode(self, article: Locator, page: Page, links: List[Dict],
                                          seen_urls: Set[str]) -> None:
        """
        Extract and follow watchEpisode redirect links.

        Handles HTML structures like:
        <a class="watchEpisode" href="/redirect/1792993">
            <i class="icon VOE"></i>
            <h4>VOE</h4>
        </a>
        """
        try:
            watch_links = await article.locator('a.watchEpisode').all()

            if not watch_links:
                return

            print(f"  [WatchEpisode] Found: {len(watch_links)} redirect links")

            for idx, link in enumerate(watch_links, 1):
                try:
                    # Extract redirect URL
                    href = await link.get_attribute('href')
                    if not href:
                        continue

                    # Extract hoster name from the link element
                    hoster = await _extract_hoster_from_watch_episode(link)

                    # Resolve relative URL
                    if href.startswith('/'):
                        base_url = page.url
                        parsed_base = urlparse(base_url)
                        full_url = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
                    else:
                        full_url = href

                    print(f"    [{idx}] Following redirect: {full_url}")

                    # Follow the redirect to get the final URL
                    final_url = await self._follow_redirect(page, full_url)

                    if final_url and final_url not in seen_urls and self._is_valid_url(final_url):
                        links.append({'url': final_url, 'hoster': hoster})
                        seen_urls.add(final_url)
                        print(f"    [{idx}] ✓ {hoster}: {final_url[:60]}...")

                except Exception as e:
                    print(f"    [{idx}] ⚠ Error processing redirect: {e}")
                    continue

        except Exception as e:
            print(f"  [WatchEpisode] ⚠ Error: {e}")

    async def _follow_redirect(self, page: Page, redirect_url: str) -> str:
        """
        Follow a redirect URL to extract the final destination.

        Parses JavaScript redirect logic like:
        window.location.href = 'https://jilliandescribecompany.com/e/j24dk14qo61r';

        Args:
            page: Page instance for navigation
            redirect_url: URL to follow

        Returns:
            Final destination URL or empty string if not found
        """
        try:
            # Create a new page context to avoid interfering with the main page
            context = page.context
            redirect_page = await context.new_page()

            try:
                # Navigate to redirect URL with a short timeout
                await redirect_page.goto(redirect_url, timeout=10000, wait_until='domcontentloaded')

                # Wait a moment for JavaScript to execute
                await redirect_page.wait_for_timeout(500)

                # Get the page content to extract the redirect URL from JavaScript
                content = await redirect_page.content()

                # Parse JavaScript redirect patterns
                patterns = [
                    r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]",
                    r"location\.href\s*=\s*['\"]([^'\"]+)['\"]",
                    r"window\.location\s*=\s*['\"]([^'\"]+)['\"]",
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # Return the last match (usually the fallback without localStorage)
                        final_url = matches[-1]
                        if self._is_valid_url(final_url):
                            return final_url

                # Alternative: Check if the page actually redirected
                final_redirect_url = redirect_page.url
                if final_redirect_url != redirect_url and self._is_valid_url(final_redirect_url):
                    return final_redirect_url

            finally:
                await redirect_page.close()

        except Exception as e:
            print(f"      ⚠ Redirect follow error: {e}")

        return ""

    async def _extract_from_data_attributes(self, article: Locator, links: List[Dict], seen_urls: Set[str]) -> None:
        """Extract video links from data attributes."""
        try:
            selectors = [
                'a[data-player-url]',
                'a.iconPlay',
                'a.button.rb.iconPlay',
                'li[data-link-target]',
                '[data-player-url]',
                'a[data-video-url]',
                'div[data-stream-url]',
                '.streamPlayBtn a[href]'
            ]

            found_count = 0
            for selector in selectors:
                try:
                    elements = await article.locator(selector).all()
                    if not elements:
                        continue

                    for elem in elements:
                        url = await self._extract_url_from_element(elem)

                        if not url or url in seen_urls:
                            continue

                        hoster = await self._extract_hoster_from_element(elem, url)

                        links.append({'url': url, 'hoster': hoster})
                        seen_urls.add(url)
                        found_count += 1
                        print(f"    ✓ {hoster}: {url[:60]}...")

                except Exception:
                    continue

            if found_count > 0:
                print(f"  [Data Attrs] Found: {found_count}")

        except Exception as e:
            print(f"  [Data Attrs] ⚠ Error: {e}")

    async def _extract_from_regex(self, article: Locator, links: List[Dict], seen_urls: Set[str]) -> None:
        """Extract video links using regex as fallback."""
        try:
            html_content = await article.inner_html()

            # Pattern 1: data attributes
            data_pattern = r'data-(?:player-url|video-url|stream-url|link-target)=["\']([^"\']+)["\']'
            data_matches = re.findall(data_pattern, html_content)

            # Pattern 2: iframe src
            iframe_pattern = r'<iframe[^>]*src=["\']([^"\']+)["\']'
            iframe_matches = re.findall(iframe_pattern, html_content)

            all_regex_matches = set(data_matches + iframe_matches)
            found_count = 0

            for url in all_regex_matches:
                if not self._is_valid_url(url) or url in seen_urls:
                    continue

                hoster = self._extract_hoster_name(url)
                links.append({'url': url, 'hoster': hoster})
                seen_urls.add(url)
                found_count += 1

            if found_count > 0:
                print(f"  [Regex] Found: {found_count}")

        except Exception as e:
            print(f"  [Regex] ⚠ Error: {e}")

    async def _extract_url_from_element(self, elem: Locator) -> str:
        """Extract URL from element's various attributes."""
        for attr in ['data-player-url', 'data-video-url', 'data-link-target',
                     'data-stream-url', 'href']:
            url = await elem.get_attribute(attr)
            if self._is_valid_url(url):
                return url
        return ""

    async def _extract_hoster_from_element(self, elem: Locator, fallback_url: str) -> str:
        """Extract hoster name from element or URL."""
        try:
            # Try to find hoster name in HTML
            parent = elem.locator('xpath=../..')
            hoster_locator = parent.locator('.hostName, [class*="host"]')

            # ✅ FIXED: Check count BEFORE calling .first
            if await hoster_locator.count() > 0:
                hoster_text = await hoster_locator.first.inner_text()
                return hoster_text.strip().replace(' HD', '').replace('HD', '').strip()
        except Exception:
            pass

        # Fallback to URL extraction
        return self._extract_hoster_name(fallback_url)

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        if not url or url in ['', '#', 'about:blank', None]:
            return False
        return url.startswith('http')

    @staticmethod
    def _extract_hoster_name(url: str) -> str:
        """
        Extract a readable hoster name from URL.

        Examples:
            https://voe.sx/e/abc123 -> Voe
            https://streamtape.com/e/xyz -> Streamtape

        Args:
            url: Video URL

        Returns:
            Capitalized hoster name
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            # Remove www prefix
            domain = re.sub(r'^www\d?\.', '', domain)

            # Remove port
            domain = domain.split(':')[0]

            # Get main domain name
            parts = domain.split('.')
            if len(parts) >= 2:
                main_domain = parts[-2]
            else:
                main_domain = parts[0]

            return main_domain.capitalize()

        except Exception:
            return "Unknown"