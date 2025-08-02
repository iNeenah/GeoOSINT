"""
GeoOSINT Utilities - Enhanced geolocation analysis tools
Inspired by GeoMastr and geOSINT projects
"""

import exifread
import requests
from geopy.geocoders import Nominatim, GoogleV3
from geopy.distance import geodesic
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import json
import pandas as pd
from datetime import datetime
import streamlit as st

class MetadataExtractor:
    """Extract metadata and EXIF data from images"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="geosint-analyzer")
    
    def extract_exif_data(self, image_path_or_bytes):
        """Extract EXIF data from image"""
        try:
            if isinstance(image_path_or_bytes, str):
                # File path
                with open(image_path_or_bytes, 'rb') as f:
                    tags = exifread.process_file(f)
            else:
                # Bytes object
                tags = exifread.process_file(image_path_or_bytes)
            
            exif_data = {}
            for tag in tags.keys():
                if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                    exif_data[tag] = str(tags[tag])
            
            return exif_data
        except Exception as e:
            st.warning(f"Could not extract EXIF data: {e}")
            return {}
    
    def extract_gps_from_exif(self, image):
        """Extract GPS coordinates from image EXIF data"""
        try:
            exif_dict = image._getexif()
            if exif_dict is not None:
                gps_info = {}
                for key, val in exif_dict.items():
                    if key in TAGS:
                        if TAGS[key] == "GPSInfo":
                            for t in val:
                                sub_key = GPSTAGS.get(t, t)
                                gps_info[sub_key] = val[t]
                
                if gps_info:
                    return self._convert_gps_to_decimal(gps_info)
            return None
        except Exception as e:
            st.warning(f"Could not extract GPS from EXIF: {e}")
            return None
    
    def _convert_gps_to_decimal(self, gps_info):
        """Convert GPS coordinates to decimal format"""
        try:
            def convert_to_degrees(value):
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = convert_to_degrees(gps_info['GPSLatitude'])
            if gps_info['GPSLatitudeRef'] != 'N':
                lat = -lat
            
            lon = convert_to_degrees(gps_info['GPSLongitude'])
            if gps_info['GPSLongitudeRef'] != 'E':
                lon = -lon
            
            return {'latitude': lat, 'longitude': lon}
        except Exception:
            return None

class ReverseGeocoder:
    """Reverse geocoding and location enhancement"""
    
    def __init__(self):
        self.nominatim = Nominatim(user_agent="geosint-analyzer")
    
    def reverse_geocode(self, lat, lon):
        """Get address from coordinates"""
        try:
            location = self.nominatim.reverse(f"{lat}, {lon}")
            if location:
                return {
                    'address': location.address,
                    'raw': location.raw
                }
            return None
        except Exception as e:
            st.warning(f"Reverse geocoding failed: {e}")
            return None
    
    def get_location_details(self, lat, lon):
        """Get detailed location information"""
        try:
            location = self.nominatim.reverse(f"{lat}, {lon}", language='en')
            if location and location.raw:
                raw = location.raw
                details = {
                    'full_address': location.address,
                    'country': raw.get('address', {}).get('country', 'Unknown'),
                    'country_code': raw.get('address', {}).get('country_code', 'Unknown'),
                    'state': raw.get('address', {}).get('state', 'Unknown'),
                    'city': raw.get('address', {}).get('city', 
                           raw.get('address', {}).get('town', 
                           raw.get('address', {}).get('village', 'Unknown'))),
                    'postcode': raw.get('address', {}).get('postcode', 'Unknown'),
                    'road': raw.get('address', {}).get('road', 'Unknown'),
                    'house_number': raw.get('address', {}).get('house_number', 'Unknown')
                }
                return details
            return None
        except Exception as e:
            st.warning(f"Could not get location details: {e}")
            return None

class CoordinateValidator:
    """Validate and enhance coordinates using multiple sources"""
    
    def __init__(self):
        self.nominatim = Nominatim(user_agent="geosint-analyzer")
    
    def validate_coordinates(self, coordinates_list):
        """Validate multiple coordinate candidates"""
        validated = []
        
        for i, (lat, lon) in enumerate(coordinates_list):
            try:
                lat_f, lon_f = float(lat), float(lon)
                
                # Basic range validation
                if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
                    continue
                
                # Try reverse geocoding to validate
                location = self.nominatim.reverse(f"{lat_f}, {lon_f}", timeout=5)
                
                confidence = "High" if location else "Low"
                
                validated.append({
                    'index': i + 1,
                    'latitude': lat_f,
                    'longitude': lon_f,
                    'confidence': confidence,
                    'address': location.address if location else "Address not found",
                    'valid': True
                })
                
            except Exception as e:
                validated.append({
                    'index': i + 1,
                    'latitude': lat,
                    'longitude': lon,
                    'confidence': "Invalid",
                    'address': f"Error: {str(e)}",
                    'valid': False
                })
        
        return validated
    
    def calculate_distances(self, coordinates_list):
        """Calculate distances between coordinate candidates"""
        if len(coordinates_list) < 2:
            return []
        
        distances = []
        for i in range(len(coordinates_list)):
            for j in range(i + 1, len(coordinates_list)):
                try:
                    coord1 = (float(coordinates_list[i][0]), float(coordinates_list[i][1]))
                    coord2 = (float(coordinates_list[j][0]), float(coordinates_list[j][1]))
                    
                    distance = geodesic(coord1, coord2).kilometers
                    
                    distances.append({
                        'from': f"Location {i + 1}",
                        'to': f"Location {j + 1}",
                        'distance_km': round(distance, 2),
                        'distance_miles': round(distance * 0.621371, 2)
                    })
                except Exception:
                    continue
        
        return distances

class DataExporter:
    """Export analysis results in various formats"""
    
    @staticmethod
    def to_csv(data, filename="geosint_results.csv"):
        """Export data to CSV format"""
        try:
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        except Exception as e:
            st.error(f"CSV export failed: {e}")
            return None
    
    @staticmethod
    def to_json(data, filename="geosint_results.json"):
        """Export data to JSON format"""
        try:
            return json.dumps(data, indent=2, default=str)
        except Exception as e:
            st.error(f"JSON export failed: {e}")
            return None
    
    @staticmethod
    def to_kml(coordinates_list, filename="geosint_results.kml"):
        """Export coordinates to KML format for Google Earth"""
        try:
            kml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>GeoOSINT Analysis Results</name>
    <description>Generated by GeoOSINT</description>
'''
            
            for i, (lat, lon) in enumerate(coordinates_list):
                kml_content += f'''
    <Placemark>
      <name>Location {i + 1}</name>
      <description>Candidate location identified by AI analysis</description>
      <Point>
        <coordinates>{lon},{lat},0</coordinates>
      </Point>
    </Placemark>'''
            
            kml_content += '''
  </Document>
</kml>'''
            
            return kml_content
        except Exception as e:
            st.error(f"KML export failed: {e}")
            return None

class SearchEngineIntegration:
    """Integration with multiple search engines for image verification"""
    
    @staticmethod
    def generate_search_urls(lat, lon):
        """Generate search URLs for multiple engines"""
        urls = {
            'Google Maps': f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
            'Google Street View': f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}",
            'Google Earth': f"https://earth.google.com/web/@{lat},{lon},1000a,35y,0h,0t,0r",
            'Bing Maps': f"https://www.bing.com/maps?q={lat},{lon}",
            'OpenStreetMap': f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=16",
            'Yandex Maps': f"https://yandex.com/maps/?ll={lon},{lat}&z=16"
        }
        return urls
    
    @staticmethod
    def generate_reverse_image_search_urls():
        """Generate reverse image search URLs"""
        urls = {
            'Google Images': "https://images.google.com/",
            'TinEye': "https://tineye.com/",
            'Yandex Images': "https://yandex.com/images/",
            'Bing Visual Search': "https://www.bing.com/visualsearch"
        }
        return urls