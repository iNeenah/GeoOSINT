import requests
import base64
import io
import json
import re
from urllib.parse import quote, urlencode
from PIL import Image
import streamlit as st
import time

class GoogleLensAnalyzer:
    """
    Google Lens integration for visual search and location analysis
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.max_url_length = 8000  # Conservative URL length limit
    
    def prepare_image_for_lens(self, image):
        """
        Prepare image for Google Lens analysis
        """
        try:
            # Resize image if too large (Google Lens works better with smaller images)
            max_size = 1024
            if image.size[0] > max_size or image.size[1] > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=85)
            img_byte_arr = img_byte_arr.getvalue()
            
            # Encode to base64
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
            
            return img_base64
        except Exception as e:
            st.error(f"Error preparing image for Google Lens: {e}")
            return None
    
    def create_lens_url(self, image):
        """
        Create Google Lens search URL with image
        """
        try:
            img_base64 = self.prepare_image_for_lens(image)
            if not img_base64:
                return None
            
            # Create the Google Lens URL
            base_url = "https://lens.google.com/uploadbyurl"
            params = {
                'url': f"data:image/jpeg;base64,{img_base64}",
                'hl': 'en'
            }
            
            lens_url = f"{base_url}?{urlencode(params)}"
            return lens_url
            
        except Exception as e:
            st.error(f"Error creating Google Lens URL: {e}")
            return None
    
    def analyze_with_lens_api(self, image):
        """
        Attempt to analyze image using Google Lens-like functionality
        This is a simplified version that extracts text and searches for location info
        """
        try:
            # For now, we'll create a lens URL and provide instructions
            # Real Google Lens API is not publicly available
            lens_url = self.create_lens_url(image)
            
            if lens_url:
                return {
                    'status': 'success',
                    'lens_url': lens_url,
                    'message': 'Google Lens URL generated successfully',
                    'instructions': 'Click the link to open Google Lens analysis in a new tab'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to generate Google Lens URL'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error in Google Lens analysis: {str(e)}'
            }
    
    def extract_location_from_lens_results(self, lens_results):
        """
        Extract location information from Google Lens results
        This would parse the results if we had access to the API
        """
        # Placeholder for future implementation
        # Would parse JSON results from Google Lens API
        locations = []
        
        # For now, return empty list
        return locations
    
    def create_lens_search_link(self, image):
        """
        Create a direct link to Google Lens search with aggressive optimization
        """
        try:
            # Start with very small size to avoid 413 errors
            max_size = 256  # Very small to start
            quality = 40    # Low quality to minimize size
            
            # Create a copy to avoid modifying original
            img_copy = image.copy()
            
            # Convert to RGB if necessary
            if img_copy.mode != 'RGB':
                img_copy = img_copy.convert('RGB')
            
            # Resize aggressively
            img_copy.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Save with very low quality to minimize size
            img_byte_arr = io.BytesIO()
            img_copy.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
            img_bytes = img_byte_arr.getvalue()
            
            # Encode to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Check final URL length
            data_url = f"data:image/jpeg;base64,{img_base64}"
            lens_url = f"https://lens.google.com/uploadbyurl?url={quote(data_url)}"
            
            # If URL is still too long, return None to trigger alternative method
            if len(lens_url) > self.max_url_length:
                return None
            
            return lens_url
            
        except Exception as e:
            return None  # Return None to trigger alternative method
    
    def create_alternative_lens_method(self, image):
        """
        Alternative method: Create instructions for manual Google Lens usage
        """
        try:
            # Create a smaller preview image for download
            max_size = 800
            img_copy = image.copy()
            
            if img_copy.size[0] > max_size or img_copy.size[1] > max_size:
                img_copy.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            if img_copy.mode != 'RGB':
                img_copy = img_copy.convert('RGB')
            
            # Save optimized image
            img_byte_arr = io.BytesIO()
            img_copy.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
            img_bytes = img_byte_arr.getvalue()
            
            return {
                'status': 'success',
                'method': 'manual',
                'image_data': img_bytes,
                'instructions': [
                    "1. Download the optimized image below",
                    "2. Go to lens.google.com",
                    "3. Click the camera icon or upload button",
                    "4. Upload the downloaded image",
                    "5. Analyze the results for location clues"
                ]
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error preparing alternative method: {str(e)}'
            }

class GoogleReverseImageSearch:
    """
    Google Reverse Image Search integration
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def create_reverse_search_url(self, image):
        """
        Create Google Reverse Image Search URL with size optimization
        """
        try:
            # Optimize image to avoid 413 errors
            max_size = 512
            quality = 70
            
            img_copy = image.copy()
            
            # Resize for better performance and smaller size
            if img_copy.size[0] > max_size or img_copy.size[1] > max_size:
                img_copy.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            if img_copy.mode != 'RGB':
                img_copy = img_copy.convert('RGB')
            
            img_byte_arr = io.BytesIO()
            img_copy.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
            img_bytes = img_byte_arr.getvalue()
            
            # Check size and optimize if needed
            max_bytes = 100000  # 100KB limit
            while len(img_bytes) > max_bytes and quality > 30:
                quality -= 10
                img_byte_arr = io.BytesIO()
                img_copy.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
                img_bytes = img_byte_arr.getvalue()
            
            # Encode to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Create reverse search URL with proper encoding
            search_url = f"https://www.google.com/searchbyimage?image_url={quote('data:image/jpeg;base64,' + img_base64)}"
            
            return search_url
            
        except Exception as e:
            st.error(f"Error creating reverse search URL: {e}")
            return None

class TinEyeIntegration:
    """
    TinEye reverse image search integration
    """
    
    def create_tineye_search_url(self, image):
        """
        Create TinEye search URL
        """
        try:
            # TinEye requires image upload, so we'll create a search URL
            # This is a simplified version
            return "https://tineye.com/"
            
        except Exception as e:
            st.error(f"Error creating TinEye URL: {e}")
            return None

class YandexImageSearch:
    """
    Yandex reverse image search integration
    """
    
    def create_yandex_search_url(self, image):
        """
        Create Yandex reverse image search URL with size optimization
        """
        try:
            # Optimize image to avoid 413 errors
            max_size = 512
            quality = 70
            
            img_copy = image.copy()
            
            # Resize for better performance
            if img_copy.size[0] > max_size or img_copy.size[1] > max_size:
                img_copy.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            if img_copy.mode != 'RGB':
                img_copy = img_copy.convert('RGB')
            
            img_byte_arr = io.BytesIO()
            img_copy.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
            img_bytes = img_byte_arr.getvalue()
            
            # Check size and optimize if needed
            max_bytes = 100000  # 100KB limit
            while len(img_bytes) > max_bytes and quality > 30:
                quality -= 10
                img_byte_arr = io.BytesIO()
                img_copy.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
                img_bytes = img_byte_arr.getvalue()
            
            # Encode to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Create Yandex search URL with proper encoding
            search_url = f"https://yandex.com/images/search?rpt=imageview&url={quote('data:image/jpeg;base64,' + img_base64)}"
            
            return search_url
            
        except Exception as e:
            st.error(f"Error creating Yandex search URL: {e}")
            return None

# Utility functions
def create_all_search_links(image):
    """
    Create all available reverse image search links
    """
    links = {}
    
    try:
        # Google Lens
        lens_analyzer = GoogleLensAnalyzer()
        lens_url = lens_analyzer.create_lens_search_link(image)
        if lens_url:
            links['Google Lens'] = lens_url
        
        # Google Reverse Image Search
        reverse_search = GoogleReverseImageSearch()
        reverse_url = reverse_search.create_reverse_search_url(image)
        if reverse_url:
            links['Google Images'] = reverse_url
        
        # Yandex
        yandex_search = YandexImageSearch()
        yandex_url = yandex_search.create_yandex_search_url(image)
        if yandex_url:
            links['Yandex Images'] = yandex_url
        
        # TinEye
        tineye_search = TinEyeIntegration()
        tineye_url = tineye_search.create_tineye_search_url(image)
        if tineye_url:
            links['TinEye'] = tineye_url
            
    except Exception as e:
        st.error(f"Error creating search links: {e}")
    
    return links