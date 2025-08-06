import requests
import base64
import io
import json
import re
from PIL import Image
import streamlit as st
from urllib.parse import quote, urlencode
import time
from bs4 import BeautifulSoup
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

class GoogleLensSimulator:
    """
    Simulates Google Lens functionality by combining multiple APIs and techniques
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def analyze_image_like_lens(self, image):
        """
        Main function that simulates Google Lens analysis
        """
        results = {
            'text_recognition': None,
            'object_detection': None,
            'landmark_detection': None,
            'web_search_results': [],
            'similar_images': [],
            'location_clues': [],
            'status': 'processing'
        }
        
        try:
            # Step 1: Text Recognition (OCR)
            results['text_recognition'] = self.extract_text_from_image(image)
            
            # Step 2: Object and Landmark Detection
            results['object_detection'] = self.detect_objects_and_landmarks(image)
            
            # Step 3: Reverse Image Search
            results['web_search_results'] = self.perform_reverse_image_search(image)
            
            # Step 4: Find Similar Images
            results['similar_images'] = self.find_similar_images(image)
            
            # Step 5: Extract Location Clues
            results['location_clues'] = self.extract_location_clues(results)
            
            results['status'] = 'completed'
            
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def extract_text_from_image(self, image):
        """
        Extract text from image using multiple methods (like Google Lens text recognition)
        """
        try:
            # Method 1: Try with pytesseract if available
            try:
                import pytesseract
                
                # Convert image for OCR
                if CV2_AVAILABLE:
                    import numpy as np
                    img_array = np.array(image)
                    
                    # If image has alpha channel, remove it
                    if len(img_array.shape) == 3 and img_array.shape[2] == 4:
                        import cv2
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                    
                    # Convert RGB to BGR for OpenCV
                    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    
                    # Enhance image for better OCR
                    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                    enhanced = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
                    
                    # Use enhanced image for OCR
                    text = pytesseract.image_to_string(enhanced, lang='eng')
                else:
                    # Use PIL image directly
                    text = pytesseract.image_to_string(image, lang='eng')
                
                # Extract text regions with confidence if possible
                try:
                    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                    text_regions = []
                    for i in range(len(data['text'])):
                        if int(data['conf'][i]) > 30 and data['text'][i].strip():
                            text_regions.append({
                                'text': data['text'][i].strip(),
                                'confidence': data['conf'][i],
                                'bbox': (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                            })
                except:
                    text_regions = []
                
                return {
                    'full_text': text.strip() if text.strip() else 'No text detected in image',
                    'text_regions': text_regions,
                    'method': 'tesseract_ocr'
                }
                
            except ImportError:
                # Method 2: Use Google Gemini for text extraction
                return self.extract_text_with_gemini(image)
                
        except Exception as e:
            return {
                'full_text': f'Text extraction failed: {str(e)}',
                'text_regions': [],
                'method': 'error'
            }
    
    def extract_text_with_gemini(self, image):
        """
        Use Google Gemini to extract text from image
        """
        try:
            import google.generativeai as genai
            from config import GEMINI_API_KEY
            
            # Configure Gemini
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            
            # Create prompt for text extraction
            text_prompt = """
            Extract ALL visible text from this image. Include:
            - Street names, addresses, signs
            - Business names and signs
            - License plates (if visible)
            - Any text on buildings, vehicles, or objects
            - Numbers, codes, or identifiers
            
            Format your response as:
            EXTRACTED_TEXT:
            [list all text found, one item per line]
            
            LOCATION_CLUES:
            [any text that might indicate location like street names, addresses, business names]
            """
            
            # Optimize image size for Gemini
            max_size = 1024
            if image.size[0] > max_size or image.size[1] > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Generate response
            response = model.generate_content([text_prompt, image])
            
            if response and response.text:
                # Parse the response
                response_text = response.text
                
                # Extract text section
                extracted_text = ""
                location_clues = ""
                
                if "EXTRACTED_TEXT:" in response_text:
                    parts = response_text.split("EXTRACTED_TEXT:")
                    if len(parts) > 1:
                        text_part = parts[1]
                        if "LOCATION_CLUES:" in text_part:
                            text_sections = text_part.split("LOCATION_CLUES:")
                            extracted_text = text_sections[0].strip()
                            if len(text_sections) > 1:
                                location_clues = text_sections[1].strip()
                        else:
                            extracted_text = text_part.strip()
                
                # Create text regions from extracted text
                text_regions = []
                if extracted_text:
                    lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
                    for i, line in enumerate(lines):
                        if line and line != '-' and len(line) > 1:
                            text_regions.append({
                                'text': line,
                                'confidence': 85,  # Simulated confidence
                                'bbox': (0, i*20, 100, 20),  # Simulated bbox
                                'is_location_clue': any(keyword in line.lower() for keyword in ['street', 'ave', 'road', 'blvd', 'st ', 'dr ', 'way'])
                            })
                
                final_text = extracted_text if extracted_text else "No text detected in image"
                if location_clues:
                    final_text += f"\n\nLocation Clues:\n{location_clues}"
                
                return {
                    'full_text': final_text,
                    'text_regions': text_regions,
                    'location_clues': location_clues,
                    'method': 'gemini_ocr'
                }
            else:
                return {
                    'full_text': 'No text could be extracted from the image',
                    'text_regions': [],
                    'method': 'gemini_failed'
                }
                
        except Exception as e:
            return {
                'full_text': f'Gemini text extraction failed: {str(e)}. Install pytesseract for OCR functionality.',
                'text_regions': [],
                'method': 'gemini_error'
            }
    
    def detect_objects_and_landmarks(self, image):
        """
        Detect objects and landmarks in the image using Gemini AI
        """
        try:
            # Use Gemini for object detection
            objects_and_landmarks = self.detect_with_gemini(image)
            
            # Basic image analysis
            colors = self.analyze_dominant_colors_basic(image)
            shapes = self.detect_basic_shapes_basic(image)
            
            # Analyze image properties
            properties = {
                'width': image.width,
                'height': image.height,
                'aspect_ratio': round(image.width / image.height, 2),
                'dominant_colors': colors,
                'detected_shapes': shapes,
                'file_format': image.format or 'Unknown',
                'mode': image.mode
            }
            
            return {
                'objects': objects_and_landmarks.get('objects', []),
                'landmarks': objects_and_landmarks.get('landmarks', []),
                'scene_type': objects_and_landmarks.get('scene_type', 'Unknown'),
                'properties': properties,
                'method': 'gemini_and_basic_analysis'
            }
            
        except Exception as e:
            return {
                'objects': [f'Analysis failed: {str(e)}'],
                'landmarks': [],
                'properties': {
                    'width': image.width,
                    'height': image.height,
                    'aspect_ratio': round(image.width / image.height, 2)
                },
                'error': str(e),
                'method': 'error'
            }
    
    def detect_with_gemini(self, image):
        """
        Use Gemini to detect objects and landmarks
        """
        try:
            import google.generativeai as genai
            from config import GEMINI_API_KEY
            
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            
            detection_prompt = """
            Analyze this image and identify:
            
            OBJECTS:
            - List all major objects you can see (cars, buildings, trees, signs, etc.)
            - Include any vehicles, infrastructure, or notable items
            
            LANDMARKS:
            - Any recognizable landmarks, buildings, or distinctive structures
            - Architectural styles or unique features
            - Geographic or cultural indicators
            
            SCENE_TYPE:
            - Describe the type of location (urban, rural, residential, commercial, etc.)
            
            Format your response as:
            OBJECTS:
            [list objects, one per line]
            
            LANDMARKS:
            [list landmarks, one per line]
            
            SCENE_TYPE:
            [describe the scene]
            """
            
            # Optimize image
            max_size = 1024
            if image.size[0] > max_size or image.size[1] > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            response = model.generate_content([detection_prompt, image])
            
            if response and response.text:
                response_text = response.text
                
                objects = []
                landmarks = []
                scene_type = ""
                
                # Parse objects
                if "OBJECTS:" in response_text:
                    parts = response_text.split("OBJECTS:")
                    if len(parts) > 1:
                        objects_section = parts[1]
                        if "LANDMARKS:" in objects_section:
                            objects_section = objects_section.split("LANDMARKS:")[0]
                        
                        objects = [obj.strip() for obj in objects_section.split('\n') if obj.strip() and obj.strip() != '-']
                
                # Parse landmarks
                if "LANDMARKS:" in response_text:
                    parts = response_text.split("LANDMARKS:")
                    if len(parts) > 1:
                        landmarks_section = parts[1]
                        if "SCENE_TYPE:" in landmarks_section:
                            landmarks_section = landmarks_section.split("SCENE_TYPE:")[0]
                        
                        landmarks = [lm.strip() for lm in landmarks_section.split('\n') if lm.strip() and lm.strip() != '-']
                
                # Parse scene type
                if "SCENE_TYPE:" in response_text:
                    parts = response_text.split("SCENE_TYPE:")
                    if len(parts) > 1:
                        scene_type = parts[1].strip()
                
                return {
                    'objects': objects[:10],  # Limit to top 10
                    'landmarks': landmarks[:5],  # Limit to top 5
                    'scene_type': scene_type
                }
            
            return {'objects': [], 'landmarks': [], 'scene_type': 'Unknown'}
            
        except Exception as e:
            return {'objects': [f'Gemini detection failed: {str(e)}'], 'landmarks': [], 'scene_type': 'Error'}
    
    def analyze_dominant_colors_basic(self, image):
        """
        Analyze dominant colors using basic PIL operations
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize for faster processing
            small_image = image.resize((50, 50))
            
            # Get all pixels
            pixels = list(small_image.getdata())
            
            # Count colors
            from collections import Counter
            color_counts = Counter(pixels)
            
            # Get top 5 colors
            top_colors = color_counts.most_common(5)
            
            return [{'color': color, 'count': count, 'percentage': round(count/len(pixels)*100, 1)} for color, count in top_colors]
            
        except Exception:
            return []
    
    def detect_basic_shapes_basic(self, image):
        """
        Basic shape detection without OpenCV
        """
        try:
            # Basic analysis based on image properties
            width, height = image.size
            aspect_ratio = width / height
            
            shapes = []
            
            # Analyze aspect ratio
            if 0.9 <= aspect_ratio <= 1.1:
                shapes.append('square-like')
            elif aspect_ratio > 1.5:
                shapes.append('wide-rectangle')
            elif aspect_ratio < 0.7:
                shapes.append('tall-rectangle')
            else:
                shapes.append('rectangle')
            
            # Analyze image complexity (basic)
            if image.mode == 'RGB':
                # Get a sample of pixels to analyze complexity
                sample = image.resize((10, 10))
                pixels = list(sample.getdata())
                unique_colors = len(set(pixels))
                
                if unique_colors < 10:
                    shapes.append('simple-pattern')
                elif unique_colors > 80:
                    shapes.append('complex-pattern')
                else:
                    shapes.append('moderate-pattern')
            
            return shapes
            
        except Exception:
            return ['basic-analysis-failed']
    
    def analyze_dominant_colors(self, img_array):
        """
        Analyze dominant colors in the image
        """
        try:
            # Reshape image to be a list of pixels
            pixels = img_array.reshape(-1, 3)
            
            # Simple color analysis - find most common colors
            from collections import Counter
            
            # Convert to tuples for counting
            pixel_tuples = [tuple(pixel) for pixel in pixels[::100]]  # Sample every 100th pixel
            
            # Count colors
            color_counts = Counter(pixel_tuples)
            
            # Get top 5 colors
            top_colors = color_counts.most_common(5)
            
            return [{'color': color, 'count': count} for color, count in top_colors]
            
        except Exception:
            return []
    
    def detect_basic_shapes(self, img_array):
        """
        Detect basic shapes in the image
        """
        try:
            if not CV2_AVAILABLE:
                return ['opencv_not_available']
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            shapes = []
            for contour in contours[:10]:  # Limit to top 10 contours
                # Approximate contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Classify shape based on number of vertices
                vertices = len(approx)
                if vertices == 3:
                    shapes.append('triangle')
                elif vertices == 4:
                    shapes.append('rectangle')
                elif vertices > 4:
                    shapes.append('circle/polygon')
            
            return shapes
            
        except Exception:
            return ['shape_detection_failed']
    
    def perform_reverse_image_search(self, image):
        """
        Perform reverse image search to find similar images and sources
        """
        try:
            # Optimize image for search
            search_image = self.optimize_image_for_search(image)
            
            # Convert to base64
            img_base64 = self.image_to_base64(search_image)
            
            # Search results (simulated - would use actual APIs)
            search_results = [
                {
                    'title': 'Similar image found',
                    'url': 'https://example.com/similar-image',
                    'description': 'This would contain actual search results from reverse image search',
                    'source': 'web_search'
                }
            ]
            
            return search_results
            
        except Exception as e:
            return [{'error': f'Reverse search failed: {str(e)}'}]
    
    def find_similar_images(self, image):
        """
        Find similar images across the web
        """
        try:
            # This would use actual image search APIs
            similar_images = [
                {
                    'url': 'https://example.com/similar1.jpg',
                    'source': 'Similar image source 1',
                    'similarity': 0.85
                },
                {
                    'url': 'https://example.com/similar2.jpg',
                    'source': 'Similar image source 2',
                    'similarity': 0.78
                }
            ]
            
            return similar_images
            
        except Exception as e:
            return [{'error': f'Similar image search failed: {str(e)}'}]
    
    def extract_location_clues(self, analysis_results):
        """
        Extract location clues from all analysis results
        """
        location_clues = []
        
        try:
            # From text recognition
            if analysis_results.get('text_recognition'):
                text_data = analysis_results['text_recognition']
                text = text_data.get('full_text', '')
                
                # Enhanced location patterns
                location_patterns = [
                    (r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Circle|Cir|Court|Ct)\b', 'address'),
                    (r'\b[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Circle|Cir|Court|Ct)\b', 'street_name'),
                    (r'\b\d{5}(-\d{4})?\b', 'zip_code'),
                    (r'\b[A-Z]{2}\s+\d{5}\b', 'state_zip'),
                    (r'\b(North|South|East|West|N|S|E|W)\.?\s+[A-Z][a-z]+\s+(St|Ave|Rd|Blvd|Dr)\b', 'directional_street'),
                    (r'\b(Highway|Hwy|Route|Rt)\s+\d+\b', 'highway'),
                    (r'\b[A-Z][a-z]+\s+(City|County|State|Province)\b', 'administrative'),
                    (r'\b(Exit|Mile|MM)\s+\d+\b', 'highway_marker'),
                ]
                
                for pattern, clue_type in location_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = ' '.join(match)
                        location_clues.append({
                            'type': clue_type,
                            'value': match,
                            'source': 'OCR_text'
                        })
                
                # From text regions with location indicators
                text_regions = text_data.get('text_regions', [])
                for region in text_regions:
                    if region.get('is_location_clue', False):
                        location_clues.append({
                            'type': 'location_text',
                            'value': region['text'],
                            'confidence': region.get('confidence', 0),
                            'source': 'OCR_region'
                        })
                
                # From location clues extracted by Gemini
                if 'location_clues' in text_data:
                    gemini_clues = text_data['location_clues']
                    if gemini_clues:
                        for clue in gemini_clues.split('\n'):
                            clue = clue.strip()
                            if clue and clue != '-':
                                location_clues.append({
                                    'type': 'gemini_location',
                                    'value': clue,
                                    'source': 'Gemini_AI'
                                })
            
            # From object detection landmarks
            if analysis_results.get('object_detection'):
                obj_data = analysis_results['object_detection']
                landmarks = obj_data.get('landmarks', [])
                for landmark in landmarks:
                    if landmark and landmark.strip():
                        location_clues.append({
                            'type': 'landmark',
                            'value': landmark,
                            'source': 'object_detection'
                        })
                
                # From scene type
                scene_type = obj_data.get('scene_type', '')
                if scene_type and scene_type != 'Unknown':
                    location_clues.append({
                        'type': 'scene_context',
                        'value': scene_type,
                        'source': 'scene_analysis'
                    })
            
            # Remove duplicates
            unique_clues = []
            seen_values = set()
            for clue in location_clues:
                value_lower = clue['value'].lower()
                if value_lower not in seen_values:
                    seen_values.add(value_lower)
                    unique_clues.append(clue)
            
            return unique_clues[:15]  # Limit to top 15 clues
            
        except Exception as e:
            return [{'type': 'error', 'value': f'Location extraction failed: {str(e)}', 'source': 'error'}]
    
    def optimize_image_for_search(self, image):
        """
        Optimize image for search APIs
        """
        # Resize to reasonable size
        max_size = 800
        if image.size[0] > max_size or image.size[1] > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    
    def image_to_base64(self, image):
        """
        Convert image to base64 string
        """
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr = img_byte_arr.getvalue()
        return base64.b64encode(img_byte_arr).decode('utf-8')

class WebSearchIntegration:
    """
    Integration with web search for location information
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_location_info(self, query):
        """
        Search for location information based on extracted clues
        """
        try:
            # This would use actual search APIs
            # For now, return simulated results
            
            search_results = [
                {
                    'title': f'Search results for: {query}',
                    'description': 'Location information would be extracted from web search',
                    'url': f'https://www.google.com/search?q={quote(query)}',
                    'relevance': 0.9
                }
            ]
            
            return search_results
            
        except Exception as e:
            return [{'error': f'Web search failed: {str(e)}'}]

# Utility functions
def format_lens_results(results):
    """
    Format Google Lens simulation results for display
    """
    formatted = {
        'summary': '',
        'text_found': '',
        'objects_detected': [],
        'location_clues': [],
        'web_results': [],
        'status': results.get('status', 'unknown')
    }
    
    # Format text recognition results
    if results.get('text_recognition'):
        text_data = results['text_recognition']
        formatted['text_found'] = text_data.get('full_text', 'No text detected')
    
    # Format object detection results
    if results.get('object_detection'):
        obj_data = results['object_detection']
        formatted['objects_detected'] = obj_data.get('objects', [])
    
    # Format location clues
    formatted['location_clues'] = results.get('location_clues', [])
    
    # Format web search results
    formatted['web_results'] = results.get('web_search_results', [])
    
    # Create summary
    summary_parts = []
    if formatted['text_found'] and formatted['text_found'] != 'No text detected':
        summary_parts.append(f"Text detected: {len(formatted['text_found'].split())} words")
    
    if formatted['objects_detected']:
        summary_parts.append(f"Objects detected: {len(formatted['objects_detected'])}")
    
    if formatted['location_clues']:
        summary_parts.append(f"Location clues found: {len(formatted['location_clues'])}")
    
    formatted['summary'] = '; '.join(summary_parts) if summary_parts else 'Analysis completed'
    
    return formatted