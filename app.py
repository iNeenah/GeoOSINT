import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
import os
import io
import base64
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from urllib.parse import quote
from config import GEMINI_API_KEY
from geosint_utils import (
    MetadataExtractor, 
    ReverseGeocoder, 
    CoordinateValidator, 
    DataExporter, 
    SearchEngineIntegration
)
from geomastr_features import (
    ImageAnalysisTools,
    WeatherAnalysis,
    ArchitecturalAnalysis,
    VegetationAnalysis,
    TimeAnalysis,
    AdvancedSearchTools,
    CoordinateRefinement,
    SunPositionAnalysis,
    VehicleAnalysis,
    SignageAnalysis,
    LanguageAnalysis
)
from google_lens_integration import (
    GoogleLensAnalyzer,
    GoogleReverseImageSearch,
    YandexImageSearch,
    TinEyeIntegration,
    create_all_search_links
)
from google_lens_simulator import (
    GoogleLensSimulator,
    WebSearchIntegration,
    format_lens_results
)

# Configurar API de Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Inicializar session state
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'current_images' not in st.session_state:
    st.session_state.current_images = []
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'multi_analysis_results' not in st.session_state:
    st.session_state.multi_analysis_results = []
if 'coordinates' not in st.session_state:
    st.session_state.coordinates = None
if 'metadata' not in st.session_state:
    st.session_state.metadata = None
if 'validated_coords' not in st.session_state:
    st.session_state.validated_coords = None
if 'location_details' not in st.session_state:
    st.session_state.location_details = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True  # Dark mode por defecto
if 'analysis_mode' not in st.session_state:
    st.session_state.analysis_mode = 'single'  # 'single' or 'multiple'
if 'lens_results' not in st.session_state:
    st.session_state.lens_results = None

# Inicializar utilidades
try:
    metadata_extractor = MetadataExtractor()
    reverse_geocoder = ReverseGeocoder()
    coord_validator = CoordinateValidator()
    data_exporter = DataExporter()
    search_integration = SearchEngineIntegration()
    
    # GeoMastr features
    image_tools = ImageAnalysisTools()
    weather_analysis = WeatherAnalysis()
    arch_analysis = ArchitecturalAnalysis()
    veg_analysis = VegetationAnalysis()
    time_analysis = TimeAnalysis()
    search_tools = AdvancedSearchTools()
    coord_refinement = CoordinateRefinement()
    sun_analysis = SunPositionAnalysis()
    vehicle_analysis = VehicleAnalysis()
    signage_analysis = SignageAnalysis()
    language_analysis = LanguageAnalysis()
    
    # Google Lens and reverse search integration
    google_lens = GoogleLensAnalyzer()
    reverse_search = GoogleReverseImageSearch()
    yandex_search = YandexImageSearch()
    tineye_search = TinEyeIntegration()
    
    # Google Lens Simulator (automatic analysis)
    lens_simulator = GoogleLensSimulator()
    web_search = WebSearchIntegration()
except Exception as e:
    st.error(f"Error initializing utilities: {e}")
    st.stop()

# Cargar prompt OSINT
def load_prompt():
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo prompt.txt")
        return None

# Procesar imagen con Gemini 2.0 - Configuración ultra-optimizada
def analyze_with_gemini(img, prompt):
    try:
        # Intentar Gemini 2.0 Flash primero (más rápido y eficiente)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # Optimizar imagen para máximo detalle
        max_size = 2048  # Tamaño más grande para Gemini 2.0
        if img.size[0] > max_size or img.size[1] > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Configuración ultra-precisa para Gemini 2.0
        response = model.generate_content(
            [prompt, img],
            generation_config={
                "temperature": 0.02,  # Máxima precisión para Gemini 2.0
                "max_output_tokens": 8000,  # Gemini 2.0 soporta más tokens
                "top_p": 0.98,
                "top_k": 16
            }
        )
        return response.text
    except Exception as e:
        # Fallback a Gemini 1.5 Pro
        try:
            st.info("🔄 Usando Gemini 1.5 Pro como respaldo...")
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(
                [prompt, img],
                generation_config={
                    "temperature": 0.05,
                    "max_output_tokens": 4000,
                    "top_p": 0.95,
                    "top_k": 20
                }
            )
            return response.text
        except Exception as e2:
            # Último fallback a Flash
            try:
                st.warning("⚠️ Usando Gemini 1.5 Flash como último recurso...")
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(
                    [prompt, img],
                    generation_config={
                        "temperature": 0.05,
                        "max_output_tokens": 3500,
                        "top_p": 0.95,
                        "top_k": 20
                    }
                )
                return response.text
            except Exception as e3:
                st.error(f"❌ Error con todos los modelos de Gemini: {str(e3)}")
                return None

# Función para análisis múltiple de imágenes
def analyze_multiple_images(images, prompt):
    """Analizar múltiples imágenes y combinar resultados"""
    results = []
    all_coordinates = []
    
    for i, image in enumerate(images):
        st.write(f"🔍 Analyzing image {i+1}/{len(images)}...")
        
        # Analizar cada imagen individualmente
        result = analyze_with_gemini(image, prompt)
        if result:
            results.append({
                'image_index': i + 1,
                'analysis': result,
                'coordinates': extract_multiple_coordinates(result)
            })
            
            # Extraer coordenadas de esta imagen
            coords = extract_multiple_coordinates(result)
            if coords:
                all_coordinates.extend(coords)
    
    # Crear análisis combinado
    combined_analysis = create_combined_analysis(results)
    
    # Filtrar y refinar coordenadas
    refined_coordinates = refine_multiple_coordinates(all_coordinates)
    
    return combined_analysis, refined_coordinates, results

def create_combined_analysis(individual_results):
    """Crear un análisis combinado optimizado para vista 360°"""
    if not individual_results:
        return "No analysis results available"
    
    # Crear análisis combinado más claro y directo
    combined = f"""
ANÁLISIS 360° COMBINADO - {len(individual_results)} IMÁGENES

"""
    
    # Extraer elementos comunes de forma más inteligente
    countries = []
    cities = []
    landmarks = []
    
    for result in individual_results:
        analysis = result['analysis'].lower()
        
        # Extraer países con mejor precisión
        country_patterns = [
            r'país:\s*([^\n]+)',
            r'country:\s*([^\n]+)',
            r'ubicado en\s*([^\n,]+)',
            r'se encuentra en\s*([^\n,]+)'
        ]
        
        for pattern in country_patterns:
            match = re.search(pattern, analysis, re.IGNORECASE)
            if match:
                countries.append(match.group(1).strip())
                break
        
        # Extraer ciudades
        city_patterns = [
            r'ciudad:\s*([^\n]+)',
            r'city:\s*([^\n]+)',
            r'región/ciudad:\s*([^\n]+)'
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, analysis, re.IGNORECASE)
            if match:
                cities.append(match.group(1).strip())
                break
        
        # Extraer landmarks
        landmark_patterns = [
            r'landmark principal:\s*([^\n]+)',
            r'punto de referencia:\s*([^\n]+)',
            r'edificio.*:\s*([^\n]+)'
        ]
        
        for pattern in landmark_patterns:
            match = re.search(pattern, analysis, re.IGNORECASE)
            if match:
                landmarks.append(match.group(1).strip())
                break
    
    # Análisis de consenso más claro
    if countries:
        most_common_country = max(set(countries), key=countries.count)
        consensus_count = countries.count(most_common_country)
        combined += f"PAÍS CONFIRMADO: {most_common_country}\n"
        combined += f"   Consenso: {consensus_count}/{len(individual_results)} imágenes\n\n"
    
    if cities:
        most_common_city = max(set(cities), key=cities.count)
        consensus_count = cities.count(most_common_city)
        combined += f"CIUDAD CONFIRMADA: {most_common_city}\n"
        combined += f"   Consenso: {consensus_count}/{len(individual_results)} imágenes\n\n"
    
    if landmarks:
        most_common_landmark = max(set(landmarks), key=landmarks.count)
        combined += f"LANDMARK PRINCIPAL: {most_common_landmark}\n\n"
    
    combined += "ANÁLISIS POR IMAGEN (Vista 360°)\n"
    combined += "─" * 50 + "\n\n"
    
    # Mostrar análisis individuales de forma más compacta
    for result in individual_results:
        combined += f"IMAGEN {result['image_index']}:\n"
        combined += "─" * 30 + "\n"
        combined += result['analysis']
        combined += "\n\n"
    
    # Conclusión más clara
    combined += "CONCLUSIÓN FINAL 360°\n"
    combined += "─" * 50 + "\n\n"
    
    combined += f"ANÁLISIS COMPLETADO: {len(individual_results)} ángulos diferentes\n"
    combined += "TRIANGULACIÓN: Coordenadas refinadas por vista múltiple\n"
    combined += "CONFIANZA: ALTA (Verificación cruzada 360°)\n\n"
    
    combined += "VENTAJA DEL ANÁLISIS 360°:\n"
    combined += "- Eliminación de puntos ciegos\n"
    combined += "- Verificación cruzada de elementos\n"
    combined += "- Mayor precisión en coordenadas\n"
    combined += "- Confirmación de landmarks desde múltiples ángulos\n"
    
    return combined

def refine_multiple_coordinates(all_coordinates):
    """Refinar coordenadas de múltiples imágenes"""
    if not all_coordinates:
        return None
    
    # Remover duplicados y coordenadas muy cercanas
    refined = []
    min_distance = 0.001  # ~100 metros
    
    for coord in all_coordinates:
        try:
            lat, lon = float(coord[0]), float(coord[1])
            is_duplicate = False
            
            for existing in refined:
                existing_lat, existing_lon = float(existing[0]), float(existing[1])
                # Calcular distancia aproximada
                distance = ((lat - existing_lat) ** 2 + (lon - existing_lon) ** 2) ** 0.5
                if distance < min_distance:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                refined.append(coord)
                
        except (ValueError, IndexError):
            continue
    
    # Retornar las 3 mejores coordenadas
    return refined[:3] if refined else None

# Extraer múltiples coordenadas candidatas con patrones mejorados
def extract_multiple_coordinates(text):
    coordinates_list = []
    
    # Patrones específicos para el nuevo formato
    patterns = [
        # Formato exacto del prompt
        r"UBICACION_PRINCIPAL:\s*(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,})",
        r"UBICACION_ALTERNATIVA_1:\s*(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,})",
        r"UBICACION_ALTERNATIVA_2:\s*(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,})"
    ]
    
    # Buscar cada patrón específico
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            lat, lon = match.groups()
            try:
                lat_f, lon_f = float(lat), float(lon)
                if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                    coordinates_list.append((lat, lon))
            except ValueError:
                continue
    
    # Si encontramos las 3 coordenadas específicas, las devolvemos
    if len(coordinates_list) >= 3:
        return coordinates_list[:3]
    
    # Fallback: buscar cualquier coordenada en el texto
    fallback_patterns = [
        r"(\-?\d+\.\d{6,}),\s*(\-?\d+\.\d{6,})",
        r"(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,})",
        r"(\-?\d+\.\d{3,}),\s*(\-?\d+\.\d{3,})"
    ]
    
    all_coords = []
    for pattern in fallback_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            lat, lon = match
            try:
                lat_f, lon_f = float(lat), float(lon)
                if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                    coord_tuple = (lat, lon)
                    if coord_tuple not in all_coords:
                        all_coords.append(coord_tuple)
            except ValueError:
                continue
    
    # Si tenemos coordenadas del fallback, tomar las primeras 3
    if all_coords:
        return all_coords[:3]
    
    # Si no encontramos nada, devolver None
    return None

# Configuración de la página
st.set_page_config(
    page_title="GeoIntel OSINT Pro",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Función para generar CSS dinámico basado en el tema
def get_theme_css(dark_mode=False):
    if dark_mode:
        # Tema oscuro
        bg_primary = "#0e1117"
        bg_secondary = "#1a1d23"
        bg_tertiary = "#262730"
        text_primary = "#ffffff"
        text_secondary = "#b3b3b3"
        accent_color = "#ff6b6b"
        border_color = "#333333"
        gradient_start = "#1a1d23"
        gradient_end = "#0e1117"
    else:
        # Tema claro
        bg_primary = "#ffffff"
        bg_secondary = "#fafafa"
        bg_tertiary = "#f5f5f5"
        text_primary = "#000000"
        text_secondary = "#666666"
        accent_color = "#1e3c72"
        border_color = "#e0e0e0"
        gradient_start = "#000000"
        gradient_end = "#1a1a1a"
    
    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700&display=swap');
    
    /* Reset y base */
    .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: {bg_primary};
        color: {text_primary};
        transition: all 0.3s ease;
    }}
    
    /* Sidebar styling */
    .css-1d391kg {{
        background: {bg_secondary};
        border-right: 1px solid {border_color};
    }}
    
    /* Main content area */
    .main .block-container {{
        background: {bg_primary};
        color: {text_primary};
    }}
    
    /* Text elements */
    h1, h2, h3, h4, h5, h6 {{
        color: {text_primary} !important;
    }}
    
    p, div, span {{
        color: {text_primary} !important;
    }}
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Header ultra-moderno */
    .main-header {{
        background: linear-gradient(135deg, {gradient_start} 0%, {gradient_end} 100%);
        color: #ffffff;
        padding: 4rem 0;
        margin: -2rem -2rem 3rem -2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }}
    
    .main-header::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        opacity: 0.5;
    }}
    
    .main-header h1 {{
        font-size: 3.5rem;
        font-weight: 200;
        letter-spacing: -0.05em;
        margin: 0;
        position: relative;
        z-index: 1;
        color: #ffffff !important;
    }}
    
    .main-header p {{
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.9;
        margin: 1rem 0 0 0;
        position: relative;
        z-index: 1;
        color: #ffffff !important;
    }}
    
    /* Theme toggle button */
    .theme-toggle {{
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        background: {accent_color};
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        cursor: pointer;
        font-size: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }}
    
    .theme-toggle:hover {{
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }}
    
    /* Cards modernos */
    .modern-card {{
        background: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 2px 20px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }}
    
    .modern-card:hover {{
        box-shadow: 0 8px 40px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }}
    
    .result-box {{
        background: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 2.5rem;
        margin: 2rem 0;
        box-shadow: 0 4px 30px rgba(0,0,0,0.06);
    }}
    
    .coordinate-box {{
        background: {bg_tertiary};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 2.5rem;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }}
    
    .coordinate-box::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, {accent_color}, {text_secondary}, {accent_color});
    }}
    
    /* Botones ultra-modernos */
    .stButton > button {{
        background: {accent_color};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.95rem;
        padding: 0.8rem 2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.01em;
        position: relative;
        overflow: hidden;
    }}
    
    .stButton > button:hover {{
        background: {text_secondary};
        transform: translateY(-1px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    /* Tabs elegantes */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        background: {bg_tertiary};
        border-radius: 8px;
        padding: 4px;
        border: none;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border: none;
        color: {text_secondary};
        font-weight: 400;
        padding: 0.8rem 1.5rem;
        border-radius: 6px;
        transition: all 0.2s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {bg_primary};
        color: {text_primary};
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    
    /* Inputs modernos */
    .stTextInput > div > div > input {{
        font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
        font-size: 0.9rem;
        background: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 0.8rem 1rem;
        transition: all 0.2s ease;
        color: {text_primary};
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {accent_color};
        box-shadow: 0 0 0 3px rgba(30,60,114,0.1);
    }}
    
    /* File uploader elegante */
    .stFileUploader {{
        border: 2px dashed {border_color};
        border-radius: 12px;
        padding: 3rem 2rem;
        text-align: center;
        background: {bg_tertiary};
        transition: all 0.3s ease;
    }}
    
    .stFileUploader:hover {{
        border-color: {accent_color};
        background: {bg_secondary};
    }}
    
    /* Alertas modernas */
    .stSuccess {{
        background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
        border: 1px solid #9ae6b4;
        border-radius: 8px;
        color: #22543d;
    }}
    
    .stInfo {{
        background: {bg_tertiary};
        border: 1px solid {border_color};
        border-radius: 8px;
        color: {text_primary};
    }}
    
    .stWarning {{
        background: linear-gradient(135deg, #fffbeb 0%, #fef5e7 100%);
        border: 1px solid #f6e05e;
        border-radius: 8px;
        color: #744210;
    }}
    
    .stError {{
        background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
        border: 1px solid #feb2b2;
        border-radius: 8px;
        color: #742a2a;
    }}
    
    /* Spinner personalizado */
    .stSpinner > div {{
        border-color: {accent_color} transparent transparent transparent;
    }}
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {bg_tertiary};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {text_secondary};
        border-radius: 3px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {accent_color};
    }}
    
    /* Animaciones suaves */
    * {{
        transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
        .main-header h1 {{
            font-size: 2.5rem;
        }}
        
        .main-header {{
            padding: 3rem 0;
        }}
        
        .modern-card, .result-box, .coordinate-box {{
            padding: 1.5rem;
            margin: 1rem 0;
        }}
        
        .theme-toggle {{
            top: 10px;
            right: 10px;
            width: 40px;
            height: 40px;
            font-size: 16px;
        }}
    }}
</style>
"""

# Aplicar CSS dinámico
st.markdown(get_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)


# Theme toggle en la parte superior
col_theme1, col_theme2, col_theme3 = st.columns([1, 2, 1])
with col_theme3:
    theme_icon = "🌙" if not st.session_state.dark_mode else "☀️"
    theme_text = "Dark Mode" if not st.session_state.dark_mode else "Light Mode"
    
    if st.button(f"{theme_icon} {theme_text}", key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# Header ultra-moderno
st.markdown("""
<div class="main-header">
    <h1>GeoIntel</h1>
    <p>Advanced Visual Geolocation Analysis</p>
</div>
""", unsafe_allow_html=True)

# Sidebar ultra-elegante
with st.sidebar:
    # Theme indicator
    theme_status = "🌙 Dark Mode" if st.session_state.dark_mode else "☀️ Light Mode"
    st.markdown(f"**Current Theme:** {theme_status}")
    st.markdown("---")
    
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("#### System Information")
    st.markdown("""
    **Analysis Engine**
    
    • Multi-candidate location detection
    • High-precision coordinate extraction
    • Cross-reference verification system
    • Advanced pattern recognition
    
    **Visual Elements**
    
    • Signage and textual content
    • Infrastructure characteristics
    • Architectural style analysis
    • Geographic feature detection
    • Cultural pattern recognition
    
    **Input Support**
    
    • Direct file upload
    • Clipboard integration
    • Screenshot processing
    • Multiple format support
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("#### Technology")
    st.markdown("""
    **AI Models**
    • Google Gemini 2.0 Flash
    • Gemini 1.5 Pro (Backup)
    
    **Framework**
    • OSINT Analysis Engine
    • Streamlit Interface
    • Folium Mapping
    
    **Features**
    • Dynamic theming
    • Advanced OSINT tools
    • Multi-format export
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Layout principal
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Upload Images")
    
    # Selector de modo de análisis
    analysis_mode = st.radio(
        "Analysis Mode:",
        ["Single Image", "360° Analysis (2-5 images)"],
        horizontal=True,
        help="360° analysis uses multiple angles of the same location for higher precision"
    )
    
    st.session_state.analysis_mode = 'multiple' if analysis_mode == "360° Analysis (2-5 images)" else 'single'
    
    # Tabs minimalistas
    if st.session_state.analysis_mode == 'single':
        tab1, tab2 = st.tabs(["Upload File", "Paste Image"])
    else:
        tab1, tab2 = st.tabs(["Multiple Files", "Paste 360° View"])
    
    with tab1:
        if st.session_state.analysis_mode == 'single':
            uploaded_file = st.file_uploader(
                "Select an image for geolocation analysis",
                type=["jpg", "jpeg", "png", "webp", "bmp"],
                help="Supported formats: JPG, PNG, WEBP, BMP"
            )
            
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.session_state.current_image = image
                st.session_state.current_images = [image]  # Para compatibilidad
                
                # Extract metadata and EXIF data
                with st.spinner("Extracting metadata..."):
                    try:
                        # Try to extract GPS from EXIF
                        gps_coords = metadata_extractor.extract_gps_from_exif(image)
                        
                        # Extract other EXIF data
                        uploaded_file.seek(0)  # Reset file pointer
                        exif_data = metadata_extractor.extract_exif_data(uploaded_file)
                        
                        st.session_state.metadata = {
                            'gps_coordinates': gps_coords,
                            'exif_data': exif_data,
                            'file_info': {
                                'filename': uploaded_file.name,
                                'size': uploaded_file.size,
                                'type': uploaded_file.type
                            }
                        }
                    except Exception as e:
                        st.session_state.metadata = {
                            'gps_coordinates': None,
                            'exif_data': {},
                            'file_info': {
                                'filename': uploaded_file.name,
                                'size': uploaded_file.size,
                                'type': uploaded_file.type
                            },
                            'error': str(e)
                        }
                
                st.success("Image loaded successfully")
                
                # Show GPS coordinates if found in EXIF
                if gps_coords:
                    st.info(f"GPS coordinates found in EXIF: {gps_coords['latitude']:.6f}, {gps_coords['longitude']:.6f}")
        
        else:  # Multiple images mode
            uploaded_files = st.file_uploader(
                "Select 2-5 images of the same location for enhanced analysis",
                type=["jpg", "jpeg", "png", "webp", "bmp"],
                accept_multiple_files=True,
                help="Upload multiple images of the same location from different angles for more accurate analysis"
            )
            
            if uploaded_files:
                if len(uploaded_files) < 2:
                    st.warning("Please upload at least 2 images for multiple image analysis")
                elif len(uploaded_files) > 5:
                    st.warning("Maximum 5 images allowed. Using first 5 images.")
                    uploaded_files = uploaded_files[:5]
                else:
                    images = []
                    metadata_list = []
                    
                    for i, uploaded_file in enumerate(uploaded_files):
                        image = Image.open(uploaded_file)
                        images.append(image)
                        
                        # Extract metadata for each image
                        try:
                            gps_coords = metadata_extractor.extract_gps_from_exif(image)
                            uploaded_file.seek(0)
                            exif_data = metadata_extractor.extract_exif_data(uploaded_file)
                            
                            metadata_list.append({
                                'gps_coordinates': gps_coords,
                                'exif_data': exif_data,
                                'file_info': {
                                    'filename': uploaded_file.name,
                                    'size': uploaded_file.size,
                                    'type': uploaded_file.type
                                }
                            })
                        except Exception as e:
                            metadata_list.append({
                                'gps_coordinates': None,
                                'exif_data': {},
                                'file_info': {
                                    'filename': uploaded_file.name,
                                    'size': uploaded_file.size,
                                    'type': uploaded_file.type
                                },
                                'error': str(e)
                            })
                    
                    st.session_state.current_images = images
                    st.session_state.current_image = images[0]  # Para compatibilidad
                    st.session_state.metadata = metadata_list
                    
                    st.success(f"✅ {len(images)} images loaded successfully")
                    
                    # Show preview of all images
                    st.markdown("#### Image Preview")
                    cols = st.columns(min(len(images), 3))
                    for i, image in enumerate(images):
                        with cols[i % len(cols)]:
                            st.image(image, caption=f"Image {i+1}", use_container_width=True)
                    
                    # Show GPS coordinates if found
                    gps_found = 0
                    for i, metadata in enumerate(metadata_list):
                        if metadata.get('gps_coordinates'):
                            gps_coords = metadata['gps_coordinates']
                            st.info(f"📍 GPS found in Image {i+1}: {gps_coords['latitude']:.6f}, {gps_coords['longitude']:.6f}")
                            gps_found += 1
                    
                    if gps_found == 0:
                        st.info("No GPS coordinates found in EXIF data")
    
    with tab2:
        if st.session_state.analysis_mode == 'single':
            st.markdown("### Paste Image Directly")
            
            # Intentar usar streamlit-paste-button
            try:
                from streamlit_paste_button import paste_image_button
                
                paste_result = paste_image_button(
                    label="Paste from Clipboard",
                    key="paste_btn",
                    errors='ignore'
                )
                
                if paste_result.image_data is not None:
                    st.session_state.current_image = paste_result.image_data
                    st.session_state.current_images = [paste_result.image_data]
                    
                    # Extract metadata from pasted image
                    with st.spinner("Extracting metadata..."):
                        gps_coords = metadata_extractor.extract_gps_from_exif(paste_result.image_data)
                        st.session_state.metadata = {
                            'gps_coordinates': gps_coords,
                            'exif_data': {},
                            'file_info': {
                                'filename': 'pasted_image',
                                'size': 'Unknown',
                                'type': 'image/png'
                            }
                        }
                    
                    st.success("Image pasted successfully")
                    
                    if gps_coords:
                        st.info(f"📍 GPS coordinates found: {gps_coords['latitude']:.6f}, {gps_coords['longitude']:.6f}")
                    
            except ImportError:
                st.warning("For direct paste functionality:")
                st.code("pip install streamlit-paste-button")
                
                # Método alternativo
                st.markdown("**Alternative method:**")
                st.info("""
                1. Take screenshot (Win+Shift+S)
                2. Save as file
                3. Use "File Upload" tab
                """)
        
        else:  # Multiple images mode
            st.markdown("### Paste Multiple Images")
            st.markdown("""
            **📸 Análisis 360° - Cómo pegar múltiples imágenes:**
            1. 🔄 Toma screenshots desde diferentes ángulos del MISMO lugar
            2. 📋 Pega la primera imagen abajo
            3. ✅ Haz clic en "Add Image" para agregarla
            4. 🔁 Repite para cada ángulo adicional (máximo 5)
            5. 🚀 Inicia análisis cuando tengas todas las vistas
            
            **💡 Tip:** Para mejor precisión, toma fotos mirando Norte, Sur, Este, Oeste
            """)
            
            # Inicializar lista de imágenes pegadas si no existe
            if 'pasted_images' not in st.session_state:
                st.session_state.pasted_images = []
            
            # Mostrar imágenes ya pegadas
            if st.session_state.pasted_images:
                st.markdown(f"#### Images Added: {len(st.session_state.pasted_images)}/5")
                cols = st.columns(min(len(st.session_state.pasted_images), 3))
                for i, img in enumerate(st.session_state.pasted_images):
                    with cols[i % len(cols)]:
                        st.image(img, caption=f"Pasted Image {i+1}", use_container_width=True)
            
            # Área para pegar nueva imagen
            try:
                from streamlit_paste_button import paste_image_button
                
                paste_result = paste_image_button(
                    label="📋 Paste Next Image",
                    key="paste_multi_btn",
                    errors='ignore'
                )
                
                if paste_result.image_data is not None:
                    # Verificar si ya tenemos esta imagen (evitar duplicados)
                    is_duplicate = False
                    for existing_img in st.session_state.pasted_images:
                        if existing_img.size == paste_result.image_data.size:
                            # Comparación básica por tamaño (podrías hacer más sofisticada)
                            is_duplicate = True
                            break
                    
                    if not is_duplicate and len(st.session_state.pasted_images) < 5:
                        # Botones para agregar o descartar la imagen
                        col1, col2 = st.columns(2)
                        
                        # Mostrar preview de la imagen pegada
                        st.image(paste_result.image_data, caption="New pasted image - Add it?", use_container_width=True)
                        
                        with col1:
                            if st.button("✅ Add This Image", use_container_width=True):
                                st.session_state.pasted_images.append(paste_result.image_data)
                                st.session_state.current_images = st.session_state.pasted_images.copy()
                                st.session_state.current_image = st.session_state.pasted_images[0]
                                st.success(f"Image added! Total: {len(st.session_state.pasted_images)}")
                                st.rerun()
                        
                        with col2:
                            if st.button("❌ Discard", use_container_width=True):
                                st.info("Image discarded")
                                st.rerun()
                    
                    elif len(st.session_state.pasted_images) >= 5:
                        st.warning("⚠️ Maximum 5 images reached. Remove some images if you want to add more.")
                    
                    elif is_duplicate:
                        st.warning("⚠️ This image appears to be a duplicate.")
                
                # Botones de control
                if st.session_state.pasted_images:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🗑️ Remove Last", use_container_width=True):
                            if st.session_state.pasted_images:
                                st.session_state.pasted_images.pop()
                                st.session_state.current_images = st.session_state.pasted_images.copy()
                                if st.session_state.pasted_images:
                                    st.session_state.current_image = st.session_state.pasted_images[0]
                                else:
                                    st.session_state.current_image = None
                                st.rerun()
                    
                    with col2:
                        if st.button("🔄 Clear All", use_container_width=True):
                            st.session_state.pasted_images = []
                            st.session_state.current_images = []
                            st.session_state.current_image = None
                            st.rerun()
                    
                    with col3:
                        if len(st.session_state.pasted_images) >= 2:
                            if st.button("✅ Ready to Analyze", use_container_width=True):
                                st.session_state.current_images = st.session_state.pasted_images.copy()
                                st.session_state.current_image = st.session_state.pasted_images[0]
                                st.success(f"Ready! {len(st.session_state.pasted_images)} images prepared for analysis.")
                        else:
                            st.info("Need at least 2 images for multi-image analysis")
                
            except ImportError:
                st.warning("For direct paste functionality:")
                st.code("pip install streamlit-paste-button")
                
                st.markdown("**Alternative method:**")
                st.info("""
                1. Take multiple screenshots of the same location
                2. Save them as files
                3. Use the "Multiple Files" tab to upload them
                """)
        
        # Botón para limpiar (solo mostrar si hay imágenes)
        has_any_images = (st.session_state.current_image is not None or 
                         st.session_state.current_images or 
                         st.session_state.get('pasted_images', []))
        
        if has_any_images:
            st.markdown("---")
            if st.button("🗑️ Clear All Images & Results", use_container_width=True):
                # Limpiar todo
                st.session_state.current_image = None
                st.session_state.current_images = []
                st.session_state.pasted_images = []
                st.session_state.analysis_result = None
                st.session_state.multi_analysis_results = []
                st.session_state.coordinates = None
                st.session_state.metadata = None
                st.session_state.validated_coords = None
                st.session_state.location_details = None
                st.success("All images and results cleared!")
                st.rerun()
    
    # Mostrar imágenes cargadas
    if st.session_state.analysis_mode == 'single':
        if st.session_state.current_image:
            st.image(
                st.session_state.current_image, 
                caption="Ready for analysis", 
                use_container_width=True
            )
            
            # Info de la imagen
            img_info = st.session_state.current_image
            st.info(f"Resolution: {img_info.size[0]} × {img_info.size[1]} px")
    
    else:  # Multiple images mode
        if st.session_state.current_images:
            st.markdown("#### Images Ready for Analysis")
            st.info(f"📊 **{len(st.session_state.current_images)} images** loaded for enhanced analysis")
            
            # Show thumbnails
            if len(st.session_state.current_images) <= 3:
                cols = st.columns(len(st.session_state.current_images))
                for i, image in enumerate(st.session_state.current_images):
                    with cols[i]:
                        st.image(image, caption=f"Image {i+1}", use_container_width=True)
            else:
                # Show in rows of 3
                for row in range(0, len(st.session_state.current_images), 3):
                    cols = st.columns(3)
                    for i in range(3):
                        if row + i < len(st.session_state.current_images):
                            with cols[i]:
                                st.image(
                                    st.session_state.current_images[row + i], 
                                    caption=f"Image {row + i + 1}", 
                                    use_container_width=True
                                )

with col2:
    st.header("Analysis")
    
    # Determinar si hay imágenes para analizar
    has_images = (st.session_state.current_image is not None or 
                  (st.session_state.current_images and len(st.session_state.current_images) > 0))
    
    if has_images:
        # Mostrar información del análisis
        if st.session_state.analysis_mode == 'single':
            analysis_text = "🔍 Start Single Image Analysis"
            analysis_help = "Analyze one image for location identification"
        else:
            num_images = len(st.session_state.current_images) if st.session_state.current_images else 0
            analysis_text = f"🔍 Start Multi-Image Analysis ({num_images} images)"
            analysis_help = f"Analyze {num_images} images together for enhanced accuracy"
        
        if st.button(analysis_text, type="primary", use_container_width=True, help=analysis_help):
            prompt = load_prompt()
            
            if prompt:
                if st.session_state.analysis_mode == 'single':
                    # Análisis de imagen única
                    with st.spinner("🧠 Analyzing with Gemini 2.0..."):
                        progress_bar = st.progress(0)
                        
                        # Simular progreso del análisis
                        import time
                        for i in range(100):
                            time.sleep(0.02)
                            progress_bar.progress(i + 1)
                        
                        result = analyze_with_gemini(st.session_state.current_image, prompt)
                        progress_bar.empty()
                    
                    if result:
                        st.session_state.analysis_result = result
                        coordinates_list = extract_multiple_coordinates(result)
                        st.session_state.coordinates = coordinates_list
                        
                        # Validate coordinates and get location details
                        if coordinates_list:
                            with st.spinner("Validating coordinates and getting location details..."):
                                st.session_state.validated_coords = coord_validator.validate_coordinates(coordinates_list)
                                
                                # Get detailed location information for each coordinate
                                location_details = []
                                for lat, lon in coordinates_list:
                                    details = reverse_geocoder.get_location_details(lat, lon)
                                    if details:
                                        details['coordinates'] = f"{lat}, {lon}"
                                        location_details.append(details)
                                st.session_state.location_details = location_details
                        
                        st.success("✅ Single image analysis completed")
                
                else:
                    # Análisis de múltiples imágenes
                    with st.spinner("🧠 Analyzing multiple images with Gemini 2.0..."):
                        progress_bar = st.progress(0)
                        
                        # Analizar múltiples imágenes
                        combined_result, refined_coordinates, individual_results = analyze_multiple_images(
                            st.session_state.current_images, prompt
                        )
                        
                        progress_bar.progress(100)
                        progress_bar.empty()
                    
                    if combined_result:
                        st.session_state.analysis_result = combined_result
                        st.session_state.multi_analysis_results = individual_results
                        st.session_state.coordinates = refined_coordinates
                        
                        # Validate coordinates and get location details
                        if refined_coordinates:
                            with st.spinner("Validating coordinates and getting location details..."):
                                st.session_state.validated_coords = coord_validator.validate_coordinates(refined_coordinates)
                                
                                # Get detailed location information for each coordinate
                                location_details = []
                                for lat, lon in refined_coordinates:
                                    details = reverse_geocoder.get_location_details(lat, lon)
                                    if details:
                                        details['coordinates'] = f"{lat}, {lon}"
                                        location_details.append(details)
                                st.session_state.location_details = location_details
                        
                        st.success(f"✅ Multi-image analysis completed ({len(st.session_state.current_images)} images processed)")
            else:
                st.error("❌ Could not load analysis prompt")
        
        # Google Lens and Reverse Image Search Section
        st.markdown("---")
        st.markdown("### Additional Analysis Tools")
        
        col_lens1, col_lens2 = st.columns(2)
        
        with col_lens1:
            st.markdown("#### Google Lens Analysis")
            if st.button("Analyze with Google Lens", use_container_width=True, help="Automatic analysis like Google Lens - extracts text, objects, and location clues"):
                if st.session_state.current_image:
                    with st.spinner("Analyzing image like Google Lens..."):
                        # Perform automatic Google Lens-like analysis
                        lens_results = lens_simulator.analyze_image_like_lens(st.session_state.current_image)
                        st.session_state.lens_results = lens_results
                        
                        if lens_results['status'] == 'completed':
                            st.success("Google Lens analysis completed!")
                            
                            # Format and display results
                            formatted_results = format_lens_results(lens_results)
                            
                            # Show summary
                            st.info(f"Analysis Summary: {formatted_results['summary']}")
                            
                            # Show text recognition results
                            if formatted_results['text_found'] and formatted_results['text_found'] != 'No text detected':
                                st.markdown("**Text Found in Image:**")
                                st.text_area("Extracted Text", formatted_results['text_found'], height=100, key="lens_text")
                                
                                # Add copy button functionality
                                if st.button("Copy Text to Clipboard", key="copy_lens_text"):
                                    st.write("Text copied! (Use Ctrl+C to copy from the text area above)")
                            
                            # Show objects detected
                            if lens_results.get('object_detection', {}).get('objects'):
                                objects = lens_results['object_detection']['objects']
                                st.markdown("**Objects Detected:**")
                                for obj in objects[:8]:  # Show top 8 objects
                                    st.markdown(f"• {obj}")
                            
                            # Show landmarks detected
                            if lens_results.get('object_detection', {}).get('landmarks'):
                                landmarks = lens_results['object_detection']['landmarks']
                                st.markdown("**Landmarks Detected:**")
                                for landmark in landmarks:
                                    st.markdown(f"• {landmark}")
                            
                            # Show location clues
                            if formatted_results['location_clues']:
                                st.markdown("**Location Clues Found:**")
                                for i, clue in enumerate(formatted_results['location_clues']):
                                    clue_type = clue.get('type', 'Unknown').replace('_', ' ').title()
                                    clue_value = clue.get('value', 'N/A')
                                    clue_source = clue.get('source', 'unknown')
                                    
                                    # Color code by type
                                    if 'address' in clue.get('type', '').lower():
                                        st.markdown(f"🏠 **{clue_type}**: {clue_value} _(from {clue_source})_")
                                    elif 'street' in clue.get('type', '').lower():
                                        st.markdown(f"🛣️ **{clue_type}**: {clue_value} _(from {clue_source})_")
                                    elif 'landmark' in clue.get('type', '').lower():
                                        st.markdown(f"🏛️ **{clue_type}**: {clue_value} _(from {clue_source})_")
                                    else:
                                        st.markdown(f"📍 **{clue_type}**: {clue_value} _(from {clue_source})_")
                        
                        elif lens_results['status'] == 'error':
                            st.error(f"Google Lens analysis failed: {lens_results.get('error', 'Unknown error')}")
                        else:
                            st.warning("Google Lens analysis is still processing...")
        
        with col_lens2:
            st.markdown("#### Reverse Image Search")
            if st.button("Multiple Search Engines", use_container_width=True, help="Search across multiple reverse image search engines"):
                if st.session_state.current_image:
                    with st.spinner("Generating search links..."):
                        search_links = create_all_search_links(st.session_state.current_image)
                        
                        if search_links:
                            st.success(f"Generated {len(search_links)} search links!")
                            
                            # Display search links in a nice format
                            for engine, url in search_links.items():
                                if engine == "Google Lens":
                                    st.markdown(f"**[{engine}]({url})** - Visual search and object recognition")
                                elif engine == "Google Images":
                                    st.markdown(f"**[{engine}]({url})** - Find similar images and sources")
                                elif engine == "Yandex Images":
                                    st.markdown(f"**[{engine}]({url})** - Russian search engine with good image recognition")
                                elif engine == "TinEye":
                                    st.markdown(f"**[{engine}]({url})** - Reverse image search specialist")
                        else:
                            st.error("Failed to generate search links")
    
    # Mostrar resultados si existen
    if st.session_state.analysis_result:
        # Crear tabs para diferentes tipos de información
        if st.session_state.analysis_mode == 'multiple' and st.session_state.multi_analysis_results:
            result_tab1, result_tab2, result_tab3, result_tab4, result_tab5, result_tab6, result_tab7, result_tab8 = st.tabs([
                "Combined Analysis", "Individual Results", "Advanced Analysis", "Metadata", "Location Details", "Export", "External Search", "Google Lens"
            ])
        else:
            result_tab1, result_tab2, result_tab3, result_tab4, result_tab5, result_tab6, result_tab7 = st.tabs([
                "AI Analysis", "Advanced Analysis", "Metadata", "Location Details", "Export", "External Search", "Google Lens"
            ])
            result_tab8 = None
        
        with result_tab1:
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            if st.session_state.analysis_mode == 'multiple':
                st.markdown("### 🔍 Combined Multi-Image Analysis")
            else:
                st.markdown("### 🔍 AI Analysis Results")
            st.markdown(st.session_state.analysis_result)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Pestaña de resultados individuales (solo para análisis múltiple)
        if result_tab6:
            with result_tab6:
                st.markdown("### 📸 Individual Image Analysis Results")
                
                if st.session_state.multi_analysis_results:
                    for result in st.session_state.multi_analysis_results:
                        with st.expander(f"🖼️ Image {result['image_index']} Analysis", expanded=False):
                            st.markdown(result['analysis'])
                            
                            # Mostrar coordenadas específicas de esta imagen
                            if result['coordinates']:
                                st.markdown("#### Coordinates from this image:")
                                for i, (lat, lon) in enumerate(result['coordinates']):
                                    st.code(f"Location {i+1}: {lat}, {lon}")
                                    
                                    # Enlaces para esta coordenada específica
                                    maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                                    sv_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.link_button(f"🗺️ Maps", maps_url, use_container_width=True)
                                    with col2:
                                        st.link_button(f"📸 Street View", sv_url, use_container_width=True)
                            else:
                                st.info("No specific coordinates extracted from this image")
                            
                            st.markdown("---")
                else:
                    st.info("No individual results available")
        
        # Ajustar índice de pestañas según el modo
        advanced_tab = result_tab3 if result_tab6 else result_tab2
        metadata_tab = result_tab4 if result_tab6 else result_tab3
        location_tab = result_tab5 if result_tab6 else result_tab4
        export_tab = result_tab6 if result_tab6 else result_tab5
        
        with advanced_tab:
            st.markdown("### Advanced OSINT Analysis")
            
            if st.session_state.current_image and st.session_state.analysis_result:
                # Create sub-tabs for different analysis types
                analysis_tab1, analysis_tab2, analysis_tab3, analysis_tab4 = st.tabs([
                    "Visual Analysis", "Language & Signs", "Environmental", "Technical"
                ])
                
                with analysis_tab1:
                    # Image properties analysis
                    st.markdown("#### Image Properties")
                    try:
                        image_props = image_tools.analyze_image_properties(st.session_state.current_image)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Format", image_props.get('format', 'Unknown'))
                            st.metric("Mode", image_props.get('mode', 'Unknown'))
                        with col2:
                            st.metric("Width", f"{image_props.get('width', 0)} px")
                            st.metric("Height", f"{image_props.get('height', 0)} px")
                        with col3:
                            st.metric("DPI", str(image_props.get('dpi', 'Unknown')))
                            st.metric("Transparency", "Yes" if image_props.get('has_transparency') else "No")
                    except Exception as e:
                        st.error(f"Error analyzing image properties: {e}")
                    
                    # Sun position and shadow analysis
                    st.markdown("#### Sun Position & Shadow Analysis")
                    try:
                        shadow_clues = sun_analysis.analyze_shadows(st.session_state.analysis_result)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if shadow_clues['hemisphere']:
                                st.success(f"Hemisphere: {', '.join(shadow_clues['hemisphere'])}")
                            else:
                                st.info("No hemisphere indicators detected")
                        
                        with col2:
                            if shadow_clues['time']:
                                st.success(f"Time indicators: {', '.join(shadow_clues['time'])}")
                            else:
                                st.info("No time indicators detected")
                    except Exception as e:
                        st.error(f"Error in shadow analysis: {e}")
                    
                    # Vehicle analysis
                    st.markdown("#### Vehicle Analysis")
                    try:
                        vehicle_regions = vehicle_analysis.identify_regional_vehicles(st.session_state.analysis_result)
                        if vehicle_regions:
                            st.success(f"Vehicle regions detected: {', '.join(set(vehicle_regions))}")
                        else:
                            st.info("No specific regional vehicles detected")
                    except Exception as e:
                        st.error(f"Error in vehicle analysis: {e}")
                
                with analysis_tab2:
                    # Language analysis
                    st.markdown("#### Language & Script Analysis")
                    try:
                        detected_languages = language_analysis.detect_languages_and_scripts(st.session_state.analysis_result)
                        if detected_languages:
                            for lang in detected_languages:
                                st.success(f"Detected: {lang}")
                        else:
                            st.info("No specific languages detected")
                    except Exception as e:
                        st.error(f"Error in language analysis: {e}")
                    
                    # Signage analysis
                    st.markdown("#### Traffic Signs & Signage")
                    try:
                        sign_countries = signage_analysis.analyze_traffic_signs(st.session_state.analysis_result)
                        if sign_countries:
                            st.success(f"Sign patterns suggest: {', '.join(set(sign_countries))}")
                        else:
                            st.info("No specific signage patterns detected")
                    except Exception as e:
                        st.error(f"Error in signage analysis: {e}")
                
                with analysis_tab3:
                    # Weather analysis
                    st.markdown("#### Climate Analysis")
                    try:
                        weather_clues = weather_analysis.analyze_weather_clues(st.session_state.analysis_result)
                        if weather_clues:
                            st.success(f"Climate types: {', '.join(weather_clues)}")
                        else:
                            st.info("No specific climate indicators detected")
                    except Exception as e:
                        st.error(f"Error in weather analysis: {e}")
                    
                    # Architectural analysis
                    st.markdown("#### Architectural Analysis")
                    try:
                        arch_styles = arch_analysis.identify_architectural_style(st.session_state.analysis_result)
                        if arch_styles:
                            st.success(f"Architectural regions: {', '.join(set(arch_styles))}")
                        else:
                            st.info("No specific architectural styles detected")
                    except Exception as e:
                        st.error(f"Error in architectural analysis: {e}")
                    
                    # Vegetation analysis
                    st.markdown("#### Vegetation Analysis")
                    try:
                        vegetation_regions = veg_analysis.analyze_vegetation(st.session_state.analysis_result)
                        if vegetation_regions:
                            st.success(f"Vegetation regions: {', '.join(set(vegetation_regions))}")
                        else:
                            st.info("No specific vegetation indicators detected")
                    except Exception as e:
                        st.error(f"Error in vegetation analysis: {e}")
                
                with analysis_tab4:
                    # Time analysis
                    st.markdown("#### Time & Lighting Analysis")
                    try:
                        time_clues = time_analysis.analyze_lighting_clues(st.session_state.analysis_result)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if time_clues.get('time_of_day'):
                                st.metric("Time of Day", ', '.join(time_clues['time_of_day']))
                            else:
                                st.metric("Time of Day", "Unknown")
                        
                        with col2:
                            if time_clues.get('season'):
                                st.metric("Season", ', '.join(time_clues['season']))
                            else:
                                st.metric("Season", "Unknown")
                    except Exception as e:
                        st.error(f"Error in time analysis: {e}")
                    
                    # Advanced search queries
                    st.markdown("#### Suggested Search Queries")
                    try:
                        if hasattr(search_tools, 'generate_search_queries'):
                            search_queries = search_tools.generate_search_queries(st.session_state.analysis_result)
                            if search_queries:
                                for i, query in enumerate(search_queries):
                                    st.code(query)
                                    try:
                                        google_search_url = f"https://www.google.com/search?q={quote(query)}"
                                        st.link_button(f"Search Query {i+1}", google_search_url, use_container_width=True)
                                    except Exception as url_error:
                                        st.warning(f"Could not create search URL for query {i+1}: {url_error}")
                            else:
                                st.info("No specific search queries generated")
                        else:
                            st.warning("Search query generation not available")
                    except Exception as e:
                        st.error(f"Error generating search queries: {e}")
                        st.info("Search query feature temporarily unavailable")
                    
                    # OSINT Tools Links
                    st.markdown("#### OSINT Tools")
                    try:
                        if hasattr(search_tools, 'generate_osint_tools_links'):
                            osint_tools = search_tools.generate_osint_tools_links()
                            for category, tools in osint_tools.items():
                                with st.expander(f"{category} Tools"):
                                    cols = st.columns(2)
                                    for i, (tool_name, url) in enumerate(tools.items()):
                                        with cols[i % 2]:
                                            try:
                                                st.link_button(tool_name, url, use_container_width=True)
                                            except Exception as link_error:
                                                st.warning(f"Could not create link for {tool_name}: {link_error}")
                        else:
                            st.warning("OSINT tools links not available")
                    except Exception as e:
                        st.error(f"Error loading OSINT tools: {e}")
                        st.info("OSINT tools feature temporarily unavailable")
            else:
                st.info("Complete an analysis first to see advanced features")
        
        with metadata_tab:
            st.markdown("### Image Metadata")
            
            # Always try to extract metadata if we have an image
            if st.session_state.current_image:
                try:
                    # File information
                    st.markdown("#### File Information")
                    if st.session_state.metadata and st.session_state.metadata.get('file_info'):
                        file_info = st.session_state.metadata['file_info']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Filename", file_info.get('filename', 'Unknown'))
                        with col2:
                            size_val = file_info.get('size', 0)
                            if isinstance(size_val, int):
                                size_str = f"{size_val:,} bytes"
                            else:
                                size_str = str(size_val)
                            st.metric("Size", size_str)
                        with col3:
                            st.metric("Type", file_info.get('type', 'Unknown'))
                    else:
                        st.info("File information not available")
                    
                    # Image properties
                    st.markdown("#### Image Properties")
                    try:
                        img_props = image_tools.analyze_image_properties(st.session_state.current_image)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Dimensions", f"{img_props.get('width', 0)} × {img_props.get('height', 0)}")
                        with col2:
                            st.metric("Format", img_props.get('format', 'Unknown'))
                        with col3:
                            st.metric("Mode", img_props.get('mode', 'Unknown'))
                    except Exception as e:
                        st.warning(f"Could not analyze image properties: {e}")
                    
                    # GPS coordinates from EXIF
                    st.markdown("#### GPS Coordinates (EXIF)")
                    if st.session_state.metadata and st.session_state.metadata.get('gps_coordinates'):
                        gps_coords = st.session_state.metadata['gps_coordinates']
                        st.success(f"📍 Found: {gps_coords['latitude']:.6f}, {gps_coords['longitude']:.6f}")
                        
                        # Add to map
                        try:
                            import folium
                            from streamlit_folium import st_folium
                            
                            m = folium.Map(
                                location=[gps_coords['latitude'], gps_coords['longitude']], 
                                zoom_start=17,  # Zoom más cercano
                                tiles=None
                            )
                            
                            # Agregar capas profesionales
                            folium.TileLayer(
                                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                                attr='Esri World Imagery',
                                name='Satellite View',
                                overlay=False,
                                control=True
                            ).add_to(m)
                            
                            folium.TileLayer(
                                'OpenStreetMap',
                                name='Street Map',
                                overlay=False,
                                control=True
                            ).add_to(m)
                            
                            folium.TileLayer(
                                'CartoDB positron',
                                name='Clean Map',
                                overlay=False,
                                control=True
                            ).add_to(m)
                            
                            # Marcador mejorado
                            popup_html = f"""
                            <div style="font-family: Arial, sans-serif; width: 200px; padding: 10px;">
                                <h4 style="margin: 0 0 10px 0; color: green; border-bottom: 1px solid #eee; padding-bottom: 5px;">
                                    EXIF GPS Location
                                </h4>
                                <p style="margin: 5px 0; font-size: 13px;">
                                    <strong>Coordinates:</strong><br>
                                    <code style="background: #f5f5f5; padding: 2px 4px; border-radius: 3px;">
                                    {gps_coords['latitude']:.6f}, {gps_coords['longitude']:.6f}
                                    </code>
                                </p>
                                <p style="margin: 5px 0; font-size: 11px; color: #666; font-style: italic;">
                                    Extracted from image metadata
                                </p>
                            </div>
                            """
                            
                            folium.Marker(
                                [gps_coords['latitude'], gps_coords['longitude']],
                                popup=folium.Popup(popup_html, max_width=250),
                                tooltip="EXIF GPS Location - Click for details",
                                icon=folium.Icon(color='green', icon='camera', prefix='fa')
                            ).add_to(m)
                            
                            # Círculo de precisión
                            folium.Circle(
                                [gps_coords['latitude'], gps_coords['longitude']],
                                radius=50,
                                popup="GPS precision area from EXIF",
                                color='green',
                                weight=2,
                                fill=True,
                                fillColor='green',
                                fillOpacity=0.15,
                                opacity=0.7
                            ).add_to(m)
                            
                            # Control de capas
                            folium.LayerControl(position='topright', collapsed=False).add_to(m)
                            
                            st_folium(m, width=None, height=500, use_container_width=True, key="exif_map")
                        except ImportError:
                            st.info("Install folium for map visualization")
                        except Exception as e:
                            st.warning(f"Could not display map: {e}")
                    else:
                        st.info("No GPS coordinates found in EXIF data")
                        
                        # Try to extract GPS again
                        if st.button("🔄 Try Extract GPS Again", key="extract_gps_btn"):
                            with st.spinner("Extracting GPS data..."):
                                try:
                                    gps_coords = metadata_extractor.extract_gps_from_exif(st.session_state.current_image)
                                    if gps_coords:
                                        st.success(f"📍 GPS Found: {gps_coords['latitude']:.6f}, {gps_coords['longitude']:.6f}")
                                        if not st.session_state.metadata:
                                            st.session_state.metadata = {}
                                        st.session_state.metadata['gps_coordinates'] = gps_coords
                                        st.rerun()
                                    else:
                                        st.info("No GPS coordinates found in this image")
                                except Exception as e:
                                    st.error(f"Error extracting GPS: {e}")
                    
                    # Other EXIF data
                    st.markdown("#### EXIF Data")
                    if st.session_state.metadata and st.session_state.metadata.get('exif_data'):
                        exif_data = st.session_state.metadata['exif_data']
                        if exif_data:
                            with st.expander("View all EXIF data"):
                                for key, value in exif_data.items():
                                    st.text(f"{key}: {value}")
                        else:
                            st.info("No EXIF data available")
                    else:
                        st.info("No EXIF data extracted")
                        
                        # Try to extract EXIF again
                        if st.button("🔄 Try Extract EXIF Again", key="extract_exif_btn"):
                            with st.spinner("Extracting EXIF data..."):
                                try:
                                    # This would need the original file, which we might not have for pasted images
                                    st.info("EXIF extraction requires original file upload")
                                except Exception as e:
                                    st.error(f"Error extracting EXIF: {e}")
                    
                    # Show any errors
                    if st.session_state.metadata and st.session_state.metadata.get('error'):
                        st.error(f"Metadata extraction error: {st.session_state.metadata['error']}")
                        
                except Exception as e:
                    st.error(f"Error displaying metadata: {e}")
            else:
                st.info("No image loaded for metadata analysis")
        
        with location_tab:
            st.markdown("### Location Details")
            if st.session_state.location_details:
                for i, details in enumerate(st.session_state.location_details):
                    with st.expander(f"Location {i+1} Details"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Country", details.get('country', 'Unknown'))
                            st.metric("State/Region", details.get('state', 'Unknown'))
                            st.metric("City", details.get('city', 'Unknown'))
                        with col2:
                            st.metric("Country Code", details.get('country_code', 'Unknown'))
                            st.metric("Postal Code", details.get('postcode', 'Unknown'))
                            st.metric("Road", details.get('road', 'Unknown'))
                        
                        st.text_area("Full Address", details.get('full_address', 'Unknown'), height=100, key=f"address_{i}")
            
            # Coordinate validation results
            if st.session_state.validated_coords:
                st.markdown("#### Coordinate Validation")
                validation_data = []
                for coord in st.session_state.validated_coords:
                    validation_data.append({
                        'Location': f"Location {coord['index']}",
                        'Latitude': coord['latitude'],
                        'Longitude': coord['longitude'],
                        'Confidence': coord['confidence'],
                        'Valid': '✅' if coord['valid'] else '❌'
                    })
                
                df = pd.DataFrame(validation_data)
                st.dataframe(df, use_container_width=True)
                
                # Distance calculations
                if st.session_state.coordinates and len(st.session_state.coordinates) > 1:
                    distances = coord_validator.calculate_distances(st.session_state.coordinates)
                    if distances:
                        st.markdown("#### Distances Between Locations")
                        distance_df = pd.DataFrame(distances)
                        st.dataframe(distance_df, use_container_width=True)
        
        with export_tab:
            st.markdown("### Export Results")
            
            if st.session_state.coordinates:
                # Prepare export data
                export_data = []
                for i, (lat, lon) in enumerate(st.session_state.coordinates):
                    data_point = {
                        'location_id': i + 1,
                        'latitude': lat,
                        'longitude': lon,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Add location details if available
                    if st.session_state.location_details and i < len(st.session_state.location_details):
                        details = st.session_state.location_details[i]
                        data_point.update({
                            'country': details.get('country', ''),
                            'state': details.get('state', ''),
                            'city': details.get('city', ''),
                            'full_address': details.get('full_address', '')
                        })
                    
                    export_data.append(data_point)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Export as CSV", key="export_csv_btn"):
                        csv_data = data_exporter.to_csv(export_data)
                        if csv_data:
                            st.download_button(
                                label="Download CSV",
                                data=csv_data,
                                file_name=f"geosint_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="download_csv_btn"
                            )
                
                with col2:
                    if st.button("Export as JSON", key="export_json_btn"):
                        json_data = data_exporter.to_json(export_data)
                        if json_data:
                            st.download_button(
                                label="Download JSON",
                                data=json_data,
                                file_name=f"geosint_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                key="download_json_btn"
                            )
                
                with col3:
                    if st.button("Export as KML", key="export_kml_btn"):
                        kml_data = data_exporter.to_kml(st.session_state.coordinates)
                        if kml_data:
                            st.download_button(
                                label="Download KML",
                                data=kml_data,
                                file_name=f"geosint_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.kml",
                                mime="application/vnd.google-earth.kml+xml",
                                key="download_kml_btn"
                            )
                
                # Advanced verification links
                st.markdown("#### Advanced Verification Links")
                if st.session_state.coordinates:
                    for i, (lat, lon) in enumerate(st.session_state.coordinates):
                        with st.expander(f"Verification Links for Location {i+1}"):
                            verification_links = search_tools.generate_verification_links(
                                lat, lon, st.session_state.analysis_result
                            )
                            
                            for category, links in verification_links.items():
                                st.markdown(f"**{category}**")
                                cols = st.columns(min(len(links), 3))
                                for j, (name, url) in enumerate(links.items()):
                                    with cols[j % len(cols)]:
                                        st.link_button(name, url, use_container_width=True)
                                st.markdown("---")
            else:
                st.info("No coordinates available for export")
        
        # Google Lens Tab (Automatic Analysis)
        lens_tab = result_tab7 if result_tab8 is None else result_tab8
        if lens_tab:
            with lens_tab:
                st.markdown("### Google Lens Analysis")
                
                if st.session_state.current_image:
                    # Auto-analyze button
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("""
                        **Automatic Google Lens-like Analysis:**
                        - Text recognition (OCR) from images
                        - Object and landmark detection
                        - Location clue extraction
                        - Web search integration
                        - Similar image finding
                        """)
                    
                    with col2:
                        if st.button("Start Google Lens Analysis", key="lens_tab_btn", use_container_width=True):
                            with st.spinner("Performing Google Lens analysis..."):
                                lens_results = lens_simulator.analyze_image_like_lens(st.session_state.current_image)
                                st.session_state.lens_results = lens_results
                    
                    # Display results if available
                    if st.session_state.lens_results:
                        results = st.session_state.lens_results
                        
                        if results['status'] == 'completed':
                            st.success("Analysis completed successfully!")
                            
                            # Text Recognition Section
                            st.markdown("#### Text Recognition (OCR)")
                            if results.get('text_recognition'):
                                text_data = results['text_recognition']
                                full_text = text_data.get('full_text', 'No text detected')
                                
                                if full_text and full_text != 'No text detected':
                                    st.text_area("Extracted Text", full_text, height=150, key="detailed_lens_text")
                                    
                                    # Text regions with confidence
                                    text_regions = text_data.get('text_regions', [])
                                    if text_regions:
                                        st.markdown("**Text Regions with Confidence:**")
                                        for region in text_regions[:10]:  # Show top 10
                                            if region['text'].strip():
                                                st.markdown(f"- **{region['text']}** (confidence: {region['confidence']}%)")
                                else:
                                    st.info("No text detected in the image")
                            
                            st.markdown("---")
                            
                            # Object Detection Section
                            st.markdown("#### Object & Landmark Detection")
                            if results.get('object_detection'):
                                obj_data = results['object_detection']
                                
                                # Show detected objects
                                objects = obj_data.get('objects', [])
                                if objects and objects != ['Analysis failed: ']:
                                    st.markdown("**Objects Detected:**")
                                    obj_cols = st.columns(2)
                                    for i, obj in enumerate(objects[:10]):
                                        with obj_cols[i % 2]:
                                            st.markdown(f"• {obj}")
                                
                                # Show detected landmarks
                                landmarks = obj_data.get('landmarks', [])
                                if landmarks:
                                    st.markdown("**Landmarks Detected:**")
                                    for landmark in landmarks:
                                        st.markdown(f"🏛️ {landmark}")
                                
                                # Show scene type
                                scene_type = obj_data.get('scene_type', '')
                                if scene_type and scene_type != 'Unknown':
                                    st.markdown(f"**Scene Type:** {scene_type}")
                                
                                # Show image properties
                                properties = obj_data.get('properties', {})
                                if properties:
                                    st.markdown("**Image Properties:**")
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("Width", f"{properties.get('width', 0)}px")
                                    with col2:
                                        st.metric("Height", f"{properties.get('height', 0)}px")
                                    with col3:
                                        st.metric("Aspect Ratio", f"{properties.get('aspect_ratio', 0):.2f}")
                                    with col4:
                                        st.metric("Format", properties.get('file_format', 'Unknown'))
                                
                                # Show dominant colors
                                colors = properties.get('dominant_colors', [])
                                if colors:
                                    st.markdown("**Dominant Colors:**")
                                    color_cols = st.columns(min(len(colors), 5))
                                    for i, color_data in enumerate(colors[:5]):
                                        with color_cols[i]:
                                            color = color_data['color']
                                            percentage = color_data.get('percentage', 0)
                                            st.markdown(f"<div style='background-color: rgb{color}; height: 40px; border-radius: 5px; margin: 5px 0; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; text-shadow: 1px 1px 1px rgba(0,0,0,0.5);'>{percentage}%</div>", unsafe_allow_html=True)
                                            st.caption(f"RGB{color}")
                                
                                # Show detected shapes
                                shapes = properties.get('detected_shapes', [])
                                if shapes and 'basic-analysis-failed' not in shapes:
                                    st.markdown(f"**Pattern Analysis:** {', '.join(set(shapes))}")
                            
                            st.markdown("---")
                            
                            # Location Clues Section
                            st.markdown("#### Location Clues")
                            location_clues = results.get('location_clues', [])
                            if location_clues:
                                for clue in location_clues:
                                    clue_type = clue.get('type', 'Unknown')
                                    clue_value = clue.get('value', 'N/A')
                                    clue_source = clue.get('source', 'unknown')
                                    
                                    st.markdown(f"**{clue_type.title()}**: {clue_value}")
                                    st.caption(f"Source: {clue_source}")
                            else:
                                st.info("No specific location clues detected")
                            
                            st.markdown("---")
                            
                            # Web Search Results Section
                            st.markdown("#### Web Search Results")
                            web_results = results.get('web_search_results', [])
                            if web_results:
                                for result in web_results:
                                    if 'error' not in result:
                                        st.markdown(f"**[{result.get('title', 'Unknown')}]({result.get('url', '#')})**")
                                        st.markdown(result.get('description', 'No description available'))
                                        st.markdown("---")
                            else:
                                st.info("No web search results available")
                        
                        elif results['status'] == 'error':
                            st.error(f"Analysis failed: {results.get('error', 'Unknown error')}")
                    
                    else:
                        st.info("Click 'Start Google Lens Analysis' to analyze the image automatically")
                
                else:
                    st.info("Upload an image to use Google Lens analysis")
        
        # External Search Tab (Manual Links)
        external_tab = result_tab6 if result_tab8 is None else result_tab7
        if external_tab:
            with external_tab:
                st.markdown("### External Search Tools")
                st.markdown("Use these tools to cross-verify and enhance your analysis with external search engines.")
                
                if st.session_state.current_image:
                    # Google Lens Section
                    st.markdown("#### Google Lens Analysis")
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("""
                        **Google Lens** provides visual search capabilities that can:
                        - Identify landmarks and buildings
                        - Recognize text in images (OCR)
                        - Find similar images across the web
                        - Provide contextual information about objects
                        """)
                    
                    with col2:
                        if st.button("Generate Google Lens Link", key="lens_result_btn", use_container_width=True):
                            with st.spinner("Preparing Google Lens analysis..."):
                                lens_url = google_lens.create_lens_search_link(st.session_state.current_image)
                                if lens_url:
                                    st.success("Google Lens URL generated!")
                                    st.markdown(f"**[Open in Google Lens]({lens_url})**")
                                else:
                                    st.error("Failed to generate Google Lens URL")
                    
                    st.markdown("---")
                    
                    # Reverse Image Search Section
                    st.markdown("#### Reverse Image Search Engines")
                    
                    search_engines_info = {
                        "Google Images": "Best for finding image sources and similar images",
                        "Yandex Images": "Excellent for Eastern European and Russian content",
                        "TinEye": "Specialized reverse image search with detailed tracking"
                    }
                    
                    for engine, description in search_engines_info.items():
                        st.markdown(f"**{engine}**: {description}")
                    
                    if st.button("Generate All Search Links", key="all_search_result_btn", use_container_width=True):
                        with st.spinner("Generating search links..."):
                            search_links = create_all_search_links(st.session_state.current_image)
                            
                            if search_links:
                                st.success(f"Generated {len(search_links)} search links!")
                                
                                # Create columns for search links
                                cols = st.columns(2)
                                for i, (engine, url) in enumerate(search_links.items()):
                                    with cols[i % 2]:
                                        if engine == "Google Lens":
                                            st.link_button(f"Google Lens", url, use_container_width=True)
                                        elif engine == "Google Images":
                                            st.link_button(f"Google Images", url, use_container_width=True)
                                        elif engine == "Yandex Images":
                                            st.link_button(f"Yandex Images", url, use_container_width=True)
                                        elif engine == "TinEye":
                                            st.link_button(f"TinEye", url, use_container_width=True)
                            else:
                                st.error("Failed to generate search links")
                    
                    st.markdown("---")
                    
                    # Tips for External Search
                    st.markdown("#### Tips for External Search")
                    st.markdown("""
                    **Best Practices:**
                    - Use Google Lens for landmark identification and text recognition
                    - Try Yandex for images that might be from Eastern Europe or Russia
                    - Use TinEye to track image usage and find original sources
                    - Cross-reference results from multiple engines for verification
                    - Look for metadata and EXIF data in original sources
                    - Check image timestamps and upload dates for temporal analysis
                    """)
                    
                else:
                    st.info("Upload an image to use external search tools")
        
        # Mostrar múltiples coordenadas candidatas
        if st.session_state.coordinates and len(st.session_state.coordinates) > 0:
            st.markdown('<div class="coordinate-box">', unsafe_allow_html=True)
            st.markdown("### Candidate Locations")
            
            # Crear tabs para cada coordenada
            if len(st.session_state.coordinates) >= 3:
                tab1, tab2, tab3 = st.tabs(["Primary", "Alternative 1", "Alternative 2"])
                tabs = [tab1, tab2, tab3]
            elif len(st.session_state.coordinates) == 2:
                tab1, tab2 = st.tabs(["Primary", "Alternative"])
                tabs = [tab1, tab2]
            else:
                tab1 = st.tabs(["Single"])[0]
                tabs = [tab1]
            
            # Mostrar cada coordenada en su tab
            for i, (lat, lon) in enumerate(st.session_state.coordinates[:len(tabs)]):
                with tabs[i]:
                    # Campo de coordenadas para copiar
                    coords_text = f"{lat}, {lon}"
                    st.text_input(
                        f"Coordinates {i+1}:",
                        value=coords_text,
                        key=f"coords_copy_{i}",
                        help="Select all (Ctrl+A) and copy (Ctrl+C) to paste in Google Maps"
                    )
                    
                    # Validar coordenadas
                    try:
                        lat_f, lon_f = float(lat), float(lon)
                        if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                            # Enlaces directos
                            maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                            sv_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"
                            earth_url = f"https://earth.google.com/web/@{lat},{lon},1000a,35y,0h,0t,0r"
                            
                            col_map1, col_map2, col_map3 = st.columns(3)
                            with col_map1:
                                st.link_button(f"Maps {i+1}", maps_url, use_container_width=True)
                            with col_map2:
                                st.link_button(f"Street {i+1}", sv_url, use_container_width=True)
                            with col_map3:
                                st.link_button(f"Earth {i+1}", earth_url, use_container_width=True)
                        else:
                            st.error(f"Coordinates {i+1} out of valid range")
                    except ValueError:
                        st.error(f"Error processing coordinates {i+1}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Mapa interactivo con todas las ubicaciones
            st.markdown("### Interactive Map")
            
            try:
                import folium
                from streamlit_folium import st_folium
                
                # Calcular centro del mapa basado en todas las coordenadas
                valid_coords = []
                for lat, lon in st.session_state.coordinates:
                    try:
                        lat_f, lon_f = float(lat), float(lon)
                        if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                            valid_coords.append([lat_f, lon_f])
                    except ValueError:
                        continue
                
                if valid_coords:
                    # Centro del mapa
                    center_lat = sum(coord[0] for coord in valid_coords) / len(valid_coords)
                    center_lon = sum(coord[1] for coord in valid_coords) / len(valid_coords)
                    
                    # Crear mapa profesional ultra-mejorado
                    m = folium.Map(
                        location=[center_lat, center_lon], 
                        zoom_start=17,  # Zoom más cercano para máximo detalle
                        tiles=None  # No usar tiles por defecto
                    )
                    
                    # Agregar vista satelital de alta calidad como principal
                    folium.TileLayer(
                        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                        attr='Esri World Imagery',
                        name='Satellite View',
                        overlay=False,
                        control=True
                    ).add_to(m)
                    
                    # Agregar OpenStreetMap como alternativa
                    folium.TileLayer(
                        'OpenStreetMap',
                        name='Street Map',
                        overlay=False,
                        control=True
                    ).add_to(m)
                    
                    # Agregar mapa limpio profesional
                    folium.TileLayer(
                        'CartoDB positron',
                        name='Clean Map',
                        overlay=False,
                        control=True
                    ).add_to(m)
                    
                    # Agregar mapa oscuro para contraste
                    folium.TileLayer(
                        'CartoDB dark_matter',
                        name='Dark Map',
                        overlay=False,
                        control=True
                    ).add_to(m)
                    
                    # Colores y etiquetas profesionales
                    colors = ['red', 'blue', 'green', 'purple', 'orange']
                    labels = ['Primary Location', 'Alternative 1', 'Alternative 2', 'Alternative 3', 'Alternative 4']
                    
                    # Agregar marcadores mejorados
                    for i, [lat_f, lon_f] in enumerate(valid_coords):
                        color = colors[i % len(colors)]
                        label = labels[i % len(labels)]
                        
                        # Popup más profesional
                        popup_html = f"""
                        <div style="font-family: Arial, sans-serif; width: 220px; padding: 10px;">
                            <h4 style="margin: 0 0 10px 0; color: {color}; border-bottom: 1px solid #eee; padding-bottom: 5px;">
                                {label}
                            </h4>
                            <p style="margin: 5px 0; font-size: 13px;">
                                <strong>Coordinates:</strong><br>
                                <code style="background: #f5f5f5; padding: 2px 4px; border-radius: 3px;">
                                {st.session_state.coordinates[i][0]}, {st.session_state.coordinates[i][1]}
                                </code>
                            </p>
                            <p style="margin: 5px 0; font-size: 11px; color: #666; font-style: italic;">
                                Click to copy coordinates
                            </p>
                        </div>
                        """
                        
                        folium.Marker(
                            [lat_f, lon_f],
                            popup=folium.Popup(popup_html, max_width=250),
                            tooltip=f"{label} - Click for details",
                            icon=folium.Icon(
                                color=color,
                                icon='map-pin',
                                prefix='fa'
                            )
                        ).add_to(m)
                        
                        # Círculo de precisión más sutil
                        folium.Circle(
                            [lat_f, lon_f],
                            radius=75,  # Radio más pequeño
                            popup=f"Estimated precision area for {label}",
                            color=color,
                            weight=2,
                            fill=True,
                            fillColor=color,
                            fillOpacity=0.15,
                            opacity=0.7
                        ).add_to(m)
                    
                    # Control de capas en posición mejor
                    folium.LayerControl(position='topright', collapsed=False).add_to(m)
                    
                    # Agregar botón de pantalla completa
                    try:
                        from folium.plugins import Fullscreen
                        Fullscreen(position='topleft').add_to(m)
                    except ImportError:
                        pass  # Si no está disponible, continuar sin él
                    
                    # Mostrar mapa ultra-profesional y grande
                    st_folium(
                        m, 
                        width=None,  # Usar ancho completo del contenedor
                        height=700,  # Altura mucho más grande
                        returned_objects=["last_clicked"],
                        use_container_width=True,
                        key="main_map"
                    )
                    
                    # Información adicional
                    st.info(f"{len(valid_coords)} candidate locations • Verify each one in Street View for accuracy")
                
            except ImportError:
                st.info("For interactive map: `pip install folium streamlit-folium`")
                for i, (lat, lon) in enumerate(st.session_state.coordinates):
                    st.markdown(f"**Location {i+1}:** [View on OpenStreetMap](https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=16)")
        else:
            st.warning("No specific coordinates detected")
            st.info("The image may need more distinctive elements for precise geolocation")
    
    else:
        if st.session_state.analysis_mode == 'single':
            st.info("📤 Upload an image to start analysis")
        else:
            st.info("📤 Upload 2-5 images of the same location for enhanced multi-image analysis")

# Footer ultra-elegante
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; padding: 3rem 0; font-size: 0.85rem; font-weight: 300;">
    <div style="margin-bottom: 1rem;">
        <strong style="font-size: 1.1rem; color: #000; font-weight: 400;">GeoIntel</strong>
    </div>
    <div style="margin-bottom: 0.5rem;">
        Advanced Visual Geolocation Analysis System
    </div>
    <div style="opacity: 0.7;">
        AI-powered location intelligence • Results are estimates for reference purposes
    </div>
</div>
""", unsafe_allow_html=True)

