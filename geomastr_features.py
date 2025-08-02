"""
GeoMastr-inspired features for enhanced OSINT capabilities
"""

import requests
import json
import base64
from urllib.parse import quote
import streamlit as st
from datetime import datetime
import hashlib

class ImageAnalysisTools:
    """Advanced image analysis tools inspired by GeoMastr"""
    
    @staticmethod
    def get_image_hash(image_bytes):
        """Generate hash for image identification"""
        return hashlib.md5(image_bytes).hexdigest()
    
    @staticmethod
    def analyze_image_properties(image):
        """Analyze basic image properties"""
        try:
            properties = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.size[0],
                'height': image.size[1],
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
            # Try to get more info
            if hasattr(image, 'info'):
                properties['dpi'] = image.info.get('dpi', 'Unknown')
                properties['compression'] = image.info.get('compression', 'Unknown')
            
            return properties
        except Exception as e:
            return {'error': str(e)}

class WeatherAnalysis:
    """Weather-based location analysis"""
    
    @staticmethod
    def analyze_weather_clues(image_description):
        """Analyze weather patterns from image description"""
        weather_indicators = {
            'tropical': ['palm trees', 'coconut', 'tropical', 'humid', 'lush vegetation'],
            'temperate': ['deciduous trees', 'moderate climate', 'seasonal'],
            'arid': ['desert', 'cactus', 'dry', 'sparse vegetation', 'sand'],
            'cold': ['snow', 'ice', 'winter', 'bare trees', 'frost'],
            'coastal': ['ocean', 'sea', 'beach', 'salt air', 'seagulls'],
            'mountain': ['elevation', 'peaks', 'alpine', 'thin air', 'rocky']
        }
        
        detected_climate = []
        description_lower = image_description.lower()
        
        for climate, indicators in weather_indicators.items():
            for indicator in indicators:
                if indicator in description_lower:
                    detected_climate.append(climate)
                    break
        
        return detected_climate

class ArchitecturalAnalysis:
    """Architectural style analysis for region identification"""
    
    @staticmethod
    def identify_architectural_style(description):
        """Identify architectural styles from description"""
        styles = {
            'European': ['gothic', 'baroque', 'renaissance', 'medieval', 'tudor', 'victorian'],
            'Asian': ['pagoda', 'temple', 'traditional asian', 'curved roof', 'zen'],
            'Middle Eastern': ['minaret', 'dome', 'islamic', 'arabic', 'mosque'],
            'American': ['colonial', 'ranch', 'craftsman', 'modern american'],
            'Latin American': ['hacienda', 'colonial spanish', 'adobe', 'stucco'],
            'African': ['tribal', 'traditional african', 'mud brick', 'thatched roof'],
            'Modern': ['glass', 'steel', 'concrete', 'minimalist', 'contemporary']
        }
        
        detected_styles = []
        description_lower = description.lower()
        
        for region, style_indicators in styles.items():
            for indicator in style_indicators:
                if indicator in description_lower:
                    detected_styles.append(region)
                    break
        
        return detected_styles

class VegetationAnalysis:
    """Vegetation-based geographic analysis"""
    
    @staticmethod
    def analyze_vegetation(description):
        """Analyze vegetation for geographic clues"""
        vegetation_regions = {
            'Tropical': ['palm', 'banana', 'mango', 'coconut', 'bamboo', 'fern', 'orchid'],
            'Temperate': ['oak', 'maple', 'birch', 'pine', 'fir', 'elm', 'ash'],
            'Mediterranean': ['olive', 'cypress', 'lavender', 'rosemary', 'citrus'],
            'Desert': ['cactus', 'succulent', 'sage', 'joshua tree', 'agave'],
            'Boreal': ['spruce', 'fir', 'pine', 'larch', 'birch'],
            'Grassland': ['grass', 'prairie', 'savanna', 'steppe']
        }
        
        detected_regions = []
        description_lower = description.lower()
        
        for region, plants in vegetation_regions.items():
            for plant in plants:
                if plant in description_lower:
                    detected_regions.append(region)
                    break
        
        return detected_regions

class TimeAnalysis:
    """Time-based analysis from shadows and lighting"""
    
    @staticmethod
    def analyze_lighting_clues(description):
        """Analyze lighting for time and hemisphere clues"""
        lighting_clues = {
            'time_of_day': {
                'morning': ['morning light', 'sunrise', 'early light', 'dawn'],
                'midday': ['harsh shadows', 'bright sun', 'noon', 'overhead sun'],
                'afternoon': ['afternoon light', 'long shadows', 'golden hour'],
                'evening': ['sunset', 'dusk', 'evening light', 'twilight']
            },
            'season': {
                'summer': ['lush green', 'full foliage', 'bright colors'],
                'winter': ['bare trees', 'snow', 'dormant vegetation'],
                'spring': ['new growth', 'blossoms', 'fresh green'],
                'autumn': ['fall colors', 'yellow leaves', 'harvest']
            }
        }
        
        detected_clues = {'time_of_day': [], 'season': []}
        description_lower = description.lower()
        
        for category, subcategories in lighting_clues.items():
            for time_period, indicators in subcategories.items():
                for indicator in indicators:
                    if indicator in description_lower:
                        detected_clues[category].append(time_period)
                        break
        
        return detected_clues

class AdvancedSearchTools:
    """Advanced search and verification tools"""
    
    @staticmethod
    def generate_search_queries(analysis_result):
        """Generate targeted search queries based on analysis"""
        queries = []
        
        # Extract key elements from analysis
        if 'country' in analysis_result.lower():
            country_match = re.search(r'country[:\s]+([^,\n]+)', analysis_result.lower())
            if country_match:
                country = country_match.group(1).strip()
                queries.append(f'"{country}" street view')
        
        if 'city' in analysis_result.lower():
            city_match = re.search(r'city[:\s]+([^,\n]+)', analysis_result.lower())
            if city_match:
                city = city_match.group(1).strip()
                queries.append(f'"{city}" landmarks')
        
        # Add architectural queries
        if 'building' in analysis_result.lower() or 'architecture' in analysis_result.lower():
            queries.append('distinctive architecture landmarks')
        
        return queries
    
    @staticmethod
    def generate_verification_links(lat, lon, analysis_text):
        """Generate comprehensive verification links"""
        links = {
            'Maps & Satellite': {
                'Google Maps': f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
                'Google Earth': f"https://earth.google.com/web/@{lat},{lon},1000a,35y,0h,0t,0r",
                'Bing Maps': f"https://www.bing.com/maps?q={lat},{lon}",
                'OpenStreetMap': f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=16",
                'Yandex Maps': f"https://yandex.com/maps/?ll={lon},{lat}&z=16"
            },
            'Street View': {
                'Google Street View': f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}",
                'Mapillary': f"https://www.mapillary.com/app/?lat={lat}&lng={lon}&z=17",
                'Yandex Panorama': f"https://yandex.com/maps/?ll={lon},{lat}&z=16&l=stv"
            },
            'Reverse Image Search': {
                'Google Images': "https://images.google.com/",
                'TinEye': "https://tineye.com/",
                'Yandex Images': "https://yandex.com/images/",
                'Bing Visual Search': "https://www.bing.com/visualsearch"
            },
            'Weather & Climate': {
                'Weather History': f"https://www.timeanddate.com/weather/@{lat},{lon}/historic",
                'Climate Data': f"https://en.climate-data.org/search/?q={lat},{lon}",
                'Sun Position': f"https://www.suncalc.org/#{lat},{lon},15"
            }
        }
        
        return links

class CoordinateRefinement:
    """Advanced coordinate refinement and validation"""
    
    @staticmethod
    def refine_coordinates_with_landmarks(lat, lon, landmarks_description):
        """Refine coordinates based on visible landmarks"""
        # This would integrate with mapping APIs to find nearby landmarks
        # For now, return the original coordinates with confidence score
        confidence_factors = []
        
        if 'specific building' in landmarks_description.lower():
            confidence_factors.append('specific_landmark')
        if 'intersection' in landmarks_description.lower():
            confidence_factors.append('road_intersection')
        if 'unique feature' in landmarks_description.lower():
            confidence_factors.append('unique_feature')
        
        confidence_score = len(confidence_factors) * 25  # Max 100%
        
        return {
            'refined_lat': lat,
            'refined_lon': lon,
            'confidence_score': min(confidence_score, 100),
            'confidence_factors': confidence_factors
        }
    
    @staticmethod
    def calculate_precision_radius(confidence_level):
        """Calculate precision radius based on confidence"""
        radius_map = {
            'high': 50,      # 50 meters
            'medium': 200,   # 200 meters
            'low': 1000      # 1 kilometer
        }
        
        return radius_map.get(confidence_level.lower(), 500)

import re