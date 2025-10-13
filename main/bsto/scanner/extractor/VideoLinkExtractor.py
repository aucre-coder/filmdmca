import re
from typing import List, Dict, Set
from httpx._urlparse import urlparse
from playwright.async_api import Locator, Page


class VideoLinkExtractor:

    async def extract_video_links(self, episode_page: Page) -> List[Dict]:
        links = []
        seen_urls: Set[str] = set()

        print("→ Extracting video links from episode page...")

        try:
            hoster_links = await episode_page.locator('ul.hoster-tabs a').all()
            print(f"  [Hoster Links] Found: {len(hoster_links)}")

            for idx, link in enumerate(hoster_links, 1):
                try:
                    href = await link.get_attribute('href')
                    hoster_name = await link.get_attribute('title')

                    # If title attribute is not available, get text content
                    if not hoster_name:
                        hoster_name = await link.inner_text()

                    if not href or not hoster_name:
                        continue

                    # Build full URL from href
                    from urllib.parse import urljoin
                    # Ensure href starts with / for proper URL joining
                    if not href.startswith('/') and not href.startswith('http'):
                        href = '/' + href
                    full_url = urljoin(episode_page.url, href)

                    if full_url not in seen_urls:
                        links.append({
                            'url': full_url,
                            'hoster': hoster_name.strip()
                        })
                        seen_urls.add(full_url)
                        print(f"    [{idx}] ✓ {hoster_name}: {full_url}")

                except Exception as e:
                    print(f"    [{idx}] ⚠ Error: {e}")
                    continue

            table_links = await episode_page.locator('table.episodes td a[href*="serie/"]').all()
            
            for link in table_links:
                try:
                    href = await link.get_attribute('href')
                    if not href or '/en' not in href and '/de' not in href:
                        continue
                    
                    if href.count('/') >= 5:
                        from urllib.parse import urljoin
                        full_url = urljoin(episode_page.url, href)
                        
                        if full_url not in seen_urls:
                            hoster_elem = link.locator('i.hoster')
                            hoster = "Unknown"
                            if await hoster_elem.count() > 0:
                                class_attr = await hoster_elem.first.get_attribute('class')
                                if class_attr:
                                    classes = class_attr.split()
                                    for cls in classes:
                                        if cls != 'hoster':
                                            hoster = cls
                                            break
                            
                            links.append({
                                'url': full_url,
                                'hoster': hoster
                            })
                            seen_urls.add(full_url)

                except Exception:
                    continue

        except Exception as e:
            print(f"  [Video Links] ⚠ Error: {e}")

        if not links:
            print("  ⚠ NO video links found!")
        else:
            print(f"✓ Total: {len(links)} unique video links extracted\n")

        return links

    async def extract_redirect_url(self, page: Page, episode_url: str) -> str:
        try:
            new_page = await page.context.new_page()
            
            try:
                await new_page.goto(episode_url, timeout=15000, wait_until='domcontentloaded')
                await new_page.wait_for_timeout(1000)
                
                iframe = new_page.locator('iframe#bs_player')
                if await iframe.count() > 0:
                    iframe_src = await iframe.get_attribute('src')
                    if iframe_src and iframe_src.startswith('http'):
                        return iframe_src
                
                content = await new_page.content()
                
                patterns = [
                    r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]",
                    r"location\.href\s*=\s*['\"]([^'\"]+)['\"]",
                    r'<iframe[^>]*src=["\']([^"\']+)["\']',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        final_url = matches[-1]
                        if final_url.startswith('http'):
                            return final_url
                
                final_redirect_url = new_page.url
                if final_redirect_url != episode_url and final_redirect_url.startswith('http'):
                    return final_redirect_url
                    
            finally:
                await new_page.close()
                
        except Exception as e:
            print(f"      ⚠ Redirect extraction error: {e}")
        
        return ""

    @staticmethod
    def _extract_hoster_name(url: str) -> str:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            domain = re.sub(r'^www\d?\.', '', domain)
            domain = domain.split(':')[0]
            parts = domain.split('.')
            if len(parts) >= 2:
                main_domain = parts[-2]
            else:
                main_domain = parts[0]
            return main_domain.capitalize()
        except Exception:
            return "Unknown"
