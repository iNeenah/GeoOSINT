"""
Google Images reverse search implementation
Performs reverse image search using Google Images and extracts similar images
"""

import asyncio
import base64
import json
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote, urlencode, urlparse
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    import requests
from bs4 import BeautifulSoup

from visual_search_core import (
    SearchEngine, SearchEngineType, SimilarImage, 
    optimize_image_for_search
)


class GoogleImagesSearch(SearchEngine):
    """Google Images reverse search implementation"""
    
    def __init__(self):
        super().__init__("Google Images", SearchEngineType.GOOGLE_IMAGES)
        self.base_url = "https://www.google.com"
        self.search_url = f"{self.base_url}/searchbyimage"
        self.upload_url = f"{self.base_url}/searchbyimage/upload"
        self.rate_limit_delay = 2.0  # Google is more strict
        
    async def reverse_search(self, image_data: bytes) -> List[SimilarImage]:
        """
        Perform reverse image search on Google Images
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            List of similar images found
        """
        try:
            # Optimize image for search
            optimized_image = optimize_image_for_search(image_data, max_size=800)
            
            # Method 1: Try direct image upload
            results = await self._search_by_upload(optimized_image)
            
            if not results:
                # Method 2: Try base64 URL method as fallback
                results = await self._search_by_base64_url(optimized_image)
            
            return results
            
        except Exception as e:
            print(f"Google Images search failed: {str(e)}")
            return []
    
    async def _search_by_upload(self, image_data: bytes) -> List[SimilarImage]:
        """Search by uploading image directly to Google"""
        try:
            if AIOHTTP_AVAILABLE:
                # Create multipart form data
                form_data = aiohttp.FormData()
                form_data.add_field('encoded_image', image_data, 
                                  filename='image.jpg', 
                                  content_type='image/jpeg')
                form_data.add_field('image_content', '')
                form_data.add_field('filename', '')
                form_data.add_field('hl', 'en')
                
                # Upload image and get search results URL
                async with self.session.post(self.upload_url, data=form_data) as response:
                    if response.status == 200:
                        # Google redirects to search results
                        search_url = str(response.url)
                        return await self._parse_search_results(search_url)
                    else:
                        print(f"Upload failed with status: {response.status}")
                        return []
            else:
                # Fallback to requests (synchronous)
                files = {'encoded_image': ('image.jpg', image_data, 'image/jpeg')}
                data = {'image_content': '', 'filename': '', 'hl': 'en'}
                
                response = self.session.post(self.upload_url, files=files, data=data)
                if response.status_code == 200:
                    search_url = response.url
                    return await self._parse_search_results(str(search_url))
                else:
                    print(f"Upload failed with status: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Upload search method failed: {str(e)}")
            return []
    
    async def _search_by_base64_url(self, image_data: bytes) -> List[SimilarImage]:
        """Search using base64 encoded image in URL (fallback method)"""
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create data URL
            data_url = f"data:image/jpeg;base64,{image_base64}"
            
            # Build search URL
            params = {
                'image_url': data_url,
                'hl': 'en'
            }
            
            search_url = f"{self.search_url}?{urlencode(params)}"
            
            # Check URL length (Google has limits)
            if len(search_url) > 8000:
                print("Image too large for base64 URL method")
                return []
            
            return await self._parse_search_results(search_url)
            
        except Exception as e:
            print(f"Base64 URL search method failed: {str(e)}")
            return []
    
    async def _parse_search_results(self, search_url: str) -> List[SimilarImage]:
        """Parse Google Images search results page"""
        try:
            # Add headers to avoid bot detection
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            if AIOHTTP_AVAILABLE:
                async with self.session.get(search_url, headers=headers) as response:
                    if response.status != 200:
                        print(f"Failed to get search results: {response.status}")
                        return []
                    
                    html_content = await response.text()
                    return self._extract_similar_images(html_content, search_url)
            else:
                # Fallback to requests (synchronous)
                response = self.session.get(search_url, headers=headers)
                if response.status_code != 200:
                    print(f"Failed to get search results: {response.status_code}")
                    return []
                
                html_content = response.text
                return self._extract_similar_images(html_content, search_url)
                
        except Exception as e:
            print(f"Failed to parse search results: {str(e)}")
            return []
    
    def _extract_similar_images(self, html_content: str, base_url: str) -> List[SimilarImage]:
        """Extract similar images from Google search results HTML"""
        similar_images = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Look for JSON data in script tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'AF_initDataCallback' in script.string:
                    images = self._extract_from_json_data(script.string)
                    similar_images.extend(images)
            
            # Method 2: Parse HTML elements directly
            if not similar_images:
                similar_images = self._extract_from_html_elements(soup)
            
            # Method 3: Look for "Pages that include matching images" section
            matching_pages = self._extract_matching_pages(soup)
            similar_images.extend(matching_pages)
            
            # Remove duplicates and limit results
            unique_images = self._deduplicate_by_url(similar_images)
            
            return unique_images[:50]  # Limit to top 50 results
            
        except Exception as e:
            print(f"Failed to extract images from HTML: {str(e)}")
            return []
    
    def _extract_from_json_data(self, script_content: str) -> List[SimilarImage]:
        """Extract images from JSON data in script tags"""
        images = []
        
        try:
            # Look for image data in AF_initDataCallback calls
            json_pattern = r'AF_initDataCallback\({[^}]*},(.*?)\);'
            matches = re.findall(json_pattern, script_content, re.DOTALL)
            
            for match in matches:
                try:
                    # Try to parse as JSON
                    data = json.loads(match)
                    images.extend(self._parse_json_image_data(data))
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"Failed to extract from JSON data: {str(e)}")
        
        return images
    
    def _parse_json_image_data(self, data: Any) -> List[SimilarImage]:
        """Parse image data from JSON structure"""
        images = []
        
        try:
            # Google's JSON structure is complex and changes frequently
            # This is a simplified parser that looks for common patterns
            
            def find_images_recursive(obj, depth=0):
                if depth > 10:  # Prevent infinite recursion
                    return
                
                if isinstance(obj, dict):
                    # Look for image-like objects
                    if all(key in obj for key in ['url', 'title']):
                        image = self._create_similar_image_from_dict(obj)
                        if image:
                            images.append(image)
                    
                    # Recurse into nested objects
                    for value in obj.values():
                        find_images_recursive(value, depth + 1)
                        
                elif isinstance(obj, list):
                    for item in obj:
                        find_images_recursive(item, depth + 1)
            
            find_images_recursive(data)
            
        except Exception as e:
            print(f"Failed to parse JSON image data: {str(e)}")
        
        return images
    
    def _extract_from_html_elements(self, soup: BeautifulSoup) -> List[SimilarImage]:
        """Extract images from HTML elements"""
        images = []
        
        try:
            # Look for image containers
            image_containers = soup.find_all(['div', 'a'], class_=re.compile(r'.*image.*|.*result.*'))
            
            for container in image_containers:
                # Look for image elements
                img_tag = container.find('img')
                if not img_tag:
                    continue
                
                # Extract image URL
                image_url = img_tag.get('src') or img_tag.get('data-src')
                if not image_url:
                    continue
                
                # Skip Google's own images (logos, icons, etc.)
                if 'google.com' in image_url and ('logo' in image_url or 'icon' in image_url):
                    continue
                
                # Extract source URL
                link_tag = container.find('a') or container.find_parent('a')
                source_url = link_tag.get('href') if link_tag else ''
                
                # Clean up Google redirect URLs
                if source_url.startswith('/url?'):
                    source_url = self._extract_url_from_google_redirect(source_url)
                
                # Extract title and description
                title = img_tag.get('alt', '')
                description = ''
                
                # Look for title in nearby text
                if not title:
                    title_elem = container.find(['h3', 'h4', 'span'], string=True)
                    if title_elem:
                        title = title_elem.get_text().strip()
                
                # Create similar image object
                if image_url and source_url:
                    similar_image = SimilarImage(
                        image_url=self._resolve_url(image_url),
                        thumbnail_url=self._resolve_url(image_url),
                        source_url=self._resolve_url(source_url),
                        title=title[:200],  # Limit title length
                        description=description[:500],  # Limit description length
                        similarity_score=0.8,  # Default score
                        domain=self._extract_domain(source_url),
                        engine_source=SearchEngineType.GOOGLE_IMAGES
                    )
                    images.append(similar_image)
                    
        except Exception as e:
            print(f"Failed to extract from HTML elements: {str(e)}")
        
        return images
    
    def _extract_matching_pages(self, soup: BeautifulSoup) -> List[SimilarImage]:
        """Extract images from 'Pages that include matching images' section"""
        images = []
        
        try:
            # Look for the matching pages section
            matching_section = soup.find('div', string=re.compile(r'Pages that include matching images'))
            if not matching_section:
                return images
            
            # Find the container with matching pages
            pages_container = matching_section.find_next('div')
            if not pages_container:
                return images
            
            # Extract page results
            page_results = pages_container.find_all('div', class_=re.compile(r'.*result.*'))
            
            for result in page_results:
                # Extract page URL
                link_tag = result.find('a')
                if not link_tag:
                    continue
                
                page_url = link_tag.get('href', '')
                if page_url.startswith('/url?'):
                    page_url = self._extract_url_from_google_redirect(page_url)
                
                # Extract title
                title_elem = result.find(['h3', 'h4'])
                title = title_elem.get_text().strip() if title_elem else ''
                
                # Extract description
                desc_elem = result.find('span', class_=re.compile(r'.*desc.*'))
                description = desc_elem.get_text().strip() if desc_elem else ''
                
                # Look for thumbnail image
                img_tag = result.find('img')
                thumbnail_url = ''
                if img_tag:
                    thumbnail_url = img_tag.get('src') or img_tag.get('data-src') or ''
                
                # Create similar image object (representing the page)
                if page_url and title:
                    similar_image = SimilarImage(
                        image_url=thumbnail_url or page_url,
                        thumbnail_url=thumbnail_url,
                        source_url=page_url,
                        title=title[:200],
                        description=description[:500],
                        similarity_score=0.7,  # Lower score for page matches
                        domain=self._extract_domain(page_url),
                        engine_source=SearchEngineType.GOOGLE_IMAGES
                    )
                    images.append(similar_image)
                    
        except Exception as e:
            print(f"Failed to extract matching pages: {str(e)}")
        
        return images
    
    def _create_similar_image_from_dict(self, data: Dict[str, Any]) -> Optional[SimilarImage]:
        """Create SimilarImage object from dictionary data"""
        try:
            # Extract required fields
            image_url = data.get('url', '')
            source_url = data.get('source_url', data.get('page_url', ''))
            title = data.get('title', '')
            
            if not image_url or not source_url:
                return None
            
            # Extract optional fields
            description = data.get('description', '')
            thumbnail_url = data.get('thumbnail', image_url)
            similarity_score = float(data.get('similarity', 0.5))
            
            # Extract dimensions if available
            dimensions = None
            if 'width' in data and 'height' in data:
                try:
                    dimensions = (int(data['width']), int(data['height']))
                except (ValueError, TypeError):
                    pass
            
            return SimilarImage(
                image_url=self._resolve_url(image_url),
                thumbnail_url=self._resolve_url(thumbnail_url),
                source_url=self._resolve_url(source_url),
                title=title[:200],
                description=description[:500],
                similarity_score=similarity_score,
                dimensions=dimensions,
                domain=self._extract_domain(source_url),
                engine_source=SearchEngineType.GOOGLE_IMAGES
            )
            
        except Exception as e:
            print(f"Failed to create similar image from dict: {str(e)}")
            return None
    
    def _extract_url_from_google_redirect(self, redirect_url: str) -> str:
        """Extract actual URL from Google redirect URL"""
        try:
            # Google redirect URLs look like: /url?q=https://example.com&sa=...
            if '?q=' in redirect_url:
                actual_url = redirect_url.split('?q=')[1].split('&')[0]
                return actual_url
            return redirect_url
        except Exception:
            return redirect_url
    
    def _resolve_url(self, url: str) -> str:
        """Resolve relative URLs to absolute URLs"""
        if not url:
            return url
        
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"{self.base_url}{url}"
        elif not url.startswith(('http://', 'https://')):
            return f"https://{url}"
        
        return url
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ''
    
    def _deduplicate_by_url(self, images: List[SimilarImage]) -> List[SimilarImage]:
        """Remove duplicate images based on image URL"""
        seen_urls = set()
        unique_images = []
        
        for image in images:
            if image.image_url not in seen_urls:
                seen_urls.add(image.image_url)
                unique_images.append(image)
        
        return unique_images
    
    def get_engine_name(self) -> str:
        """Return human-readable engine name"""
        return "Google Images"


# Utility functions for Google Images search
def create_google_search_url(query: str) -> str:
    """Create Google Images search URL for text query"""
    params = {
        'q': query,
        'tbm': 'isch',  # Image search
        'hl': 'en'
    }
    return f"https://www.google.com/search?{urlencode(params)}"


def extract_google_image_metadata(image_url: str) -> Dict[str, Any]:
    """Extract metadata from Google Images URL"""
    metadata = {}
    
    try:
        parsed = urlparse(image_url)
        
        # Extract image parameters from Google URLs
        if 'google.com' in parsed.netloc:
            # Google image URLs often contain metadata in the path or query
            if 'imgres' in parsed.query:
                # Parse imgres parameters
                from urllib.parse import parse_qs
                params = parse_qs(parsed.query)
                
                if 'imgurl' in params:
                    metadata['original_url'] = params['imgurl'][0]
                if 'imgrefurl' in params:
                    metadata['source_page'] = params['imgrefurl'][0]
                if 'w' in params and 'h' in params:
                    metadata['dimensions'] = (int(params['w'][0]), int(params['h'][0]))
        
    except Exception as e:
        print(f"Failed to extract Google image metadata: {str(e)}")
    
    return metadata


async def test_google_images_search():
    """Test function for Google Images search"""
    try:
        # Create test image data (small red square)
        from PIL import Image
        import io
        
        test_image = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='JPEG')
        image_data = img_bytes.getvalue()
        
        # Test search
        search_engine = GoogleImagesSearch()
        
        async with search_engine:
            results = await search_engine.reverse_search(image_data)
            
            print(f"Found {len(results)} similar images")
            for i, result in enumerate(results[:5]):
                print(f"{i+1}. {result.title}")
                print(f"   URL: {result.source_url}")
                print(f"   Similarity: {result.similarity_score}")
                print()
                
    except Exception as e:
        print(f"Test failed: {str(e)}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_google_images_search())