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
    """Advanced search and verification tools inspired by GeoMastr"""
    
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
                queries.append(f'"{country}" landmarks')
        
        if 'city' in analysis_result.lower():
            city_match = re.search(r'city[:\s]+([^,\n]+)', analysis_result.lower())
            if city_match:
                city = city_match.group(1).strip()
                queries.append(f'"{city}" landmarks')
                queries.append(f'"{city}" street photography')
        
        # Add architectural queries
        if 'building' in analysis_result.lower() or 'architecture' in analysis_result.lower():
            queries.append('distinctive architecture landmarks')
        
        # Add vegetation queries
        if any(word in analysis_result.lower() for word in ['tree', 'plant', 'vegetation', 'forest']):
            queries.append('vegetation identification location')
        
        # Add infrastructure queries
        if any(word in analysis_result.lower() for word in ['road', 'street', 'sign', 'pole']):
            queries.append('infrastructure street signs')
        
        return queries
    
    @staticmethod
    def generate_osint_tools_links():
        """Generate links to popular OSINT tools"""
        return {
            'Image Analysis': {
                'Jeffrey\'s Image Metadata Viewer': 'http://exif.regex.info/exif.cgi',
                'FotoForensics': 'http://fotoforensics.com/',
                'Ghiro': 'http://www.getghiro.org/',
                'InVID Verification Plugin': 'https://www.invid-project.eu/tools-and-services/invid-verification-plugin/'
            },
            'Geolocation': {
                'GeoGuessr': 'https://www.geoguessr.com/',
                'Wikimapia': 'http://wikimapia.org/',
                'OverpassTurbo': 'https://overpass-turbo.eu/',
                'Dual Maps': 'http://data.mashedworld.com/dualmaps/map.htm'
            },
            'Reverse Image Search': {
                'Google Images': 'https://images.google.com/',
                'TinEye': 'https://tineye.com/',
                'Yandex Images': 'https://yandex.com/images/',
                'Bing Visual Search': 'https://www.bing.com/visualsearch',
                'RevEye': 'https://reveye.it/'
            },
            'Social Media': {
                'Social Searcher': 'https://www.social-searcher.com/',
                'Pipl': 'https://pipl.com/',
                'Sherlock': 'https://github.com/sherlock-project/sherlock',
                'WhatsMyName': 'https://whatsmyname.app/'
            }
        }
    
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

class SunPositionAnalysis:
    """Sun position analysis for hemisphere and time determination"""
    
    @staticmethod
    def analyze_shadows(description):
        """Analyze shadow patterns for geographic clues"""
        shadow_clues = {
            'hemisphere': {
                'northern': ['shadows point north', 'sun in south', 'southern exposure'],
                'southern': ['shadows point south', 'sun in north', 'northern exposure']
            },
            'time': {
                'morning': ['long shadows east', 'sun low east', 'morning shadows'],
                'noon': ['short shadows', 'overhead sun', 'minimal shadows'],
                'afternoon': ['long shadows west', 'sun low west', 'afternoon shadows']
            }
        }
        
        detected_clues = {'hemisphere': [], 'time': []}
        description_lower = description.lower()
        
        for category, subcategories in shadow_clues.items():
            for indicator_type, indicators in subcategories.items():
                for indicator in indicators:
                    if indicator in description_lower:
                        detected_clues[category].append(indicator_type)
                        break
        
        return detected_clues

class VehicleAnalysis:
    """Vehicle analysis for regional identification"""
    
    @staticmethod
    def identify_regional_vehicles(description):
        """Identify vehicles that are region-specific"""
        regional_vehicles = {
            'Europe': ['volkswagen', 'bmw', 'mercedes', 'audi', 'peugeot', 'renault', 'fiat'],
            'Asia': ['toyota', 'honda', 'nissan', 'hyundai', 'kia', 'suzuki', 'mitsubishi'],
            'America': ['ford', 'chevrolet', 'dodge', 'jeep', 'cadillac', 'buick'],
            'India': ['tata', 'mahindra', 'maruti', 'bajaj', 'hero', 'tvs'],
            'Russia': ['lada', 'uaz', 'gaz', 'kamaz'],
            'China': ['byd', 'geely', 'chery', 'great wall']
        }
        
        detected_regions = []
        description_lower = description.lower()
        
        for region, vehicles in regional_vehicles.items():
            for vehicle in vehicles:
                if vehicle in description_lower:
                    detected_regions.append(region)
                    break
        
        return detected_regions

class SignageAnalysis:
    """Traffic signs and signage analysis"""
    
    @staticmethod
    def analyze_traffic_signs(description):
        """Analyze traffic signs for country identification"""
        sign_patterns = {
            'Europe': ['circular signs', 'blue signs', 'eu standard', 'metric units'],
            'USA': ['rectangular signs', 'yellow warning', 'stop sign octagon', 'mph'],
            'UK': ['left side driving', 'circular signs', 'mph', 'british signs'],
            'Australia': ['left side driving', 'kangaroo signs', 'metric', 'australian'],
            'Japan': ['japanese characters', 'left side driving', 'blue signs'],
            'China': ['chinese characters', 'right side driving', 'red signs']
        }
        
        detected_countries = []
        description_lower = description.lower()
        
        for country, patterns in sign_patterns.items():
            for pattern in patterns:
                if pattern in description_lower:
                    detected_countries.append(country)
                    break
        
        return detected_countries

class LanguageAnalysis:
    """Language and text analysis for location identification"""
    
    @staticmethod
    def detect_languages_and_scripts(description):
        """Detect languages and writing systems"""
        language_indicators = {
            'Latin Script': {
                'English': ['english', 'stop', 'street', 'avenue', 'road'],
                'Spanish': ['calle', 'avenida', 'plaza', 'centro', 'iglesia'],
                'French': ['rue', 'avenue', 'place', 'centre', 'église'],
                'German': ['straße', 'platz', 'kirche', 'zentrum', 'bahnhof'],
                'Italian': ['via', 'piazza', 'centro', 'chiesa', 'stazione'],
                'Portuguese': ['rua', 'avenida', 'praça', 'centro', 'igreja']
            },
            'Cyrillic Script': {
                'Russian': ['улица', 'проспект', 'площадь', 'центр', 'церковь'],
                'Ukrainian': ['вулиця', 'проспект', 'площа', 'центр', 'церква'],
                'Bulgarian': ['улица', 'площад', 'център', 'църква']
            },
            'Asian Scripts': {
                'Chinese': ['街', '路', '大道', '中心', '市'],
                'Japanese': ['通り', '街', '駅', '中心', '市'],
                'Korean': ['길', '로', '거리', '중심', '시'],
                'Thai': ['ถนน', 'ซอย', 'ตลาด', 'วัด', 'โรงเรียน']
            },
            'Arabic Script': {
                'Arabic': ['شارع', 'طريق', 'ميدان', 'مركز', 'مسجد'],
                'Persian': ['خیابان', 'میدان', 'مرکز', 'مسجد']
            }
        }
        
        detected_languages = []
        description_lower = description.lower()
        
        for script_family, languages in language_indicators.items():
            for language, words in languages.items():
                for word in words:
                    if word in description_lower:
                        detected_languages.append(f"{language} ({script_family})")
                        break
        
        return detected_languages

import re