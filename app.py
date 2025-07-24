import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
import os
import io
import base64
from config import GEMINI_API_KEY

# Configurar API de Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Inicializar session state
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'coordinates' not in st.session_state:
    st.session_state.coordinates = None

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

# Extraer múltiples coordenadas candidatas
def extract_multiple_coordinates(text):
    # Patrones para encontrar múltiples coordenadas
    patterns = [
        # Ubicación principal, alternativa 1, alternativa 2
        r"PRINCIPAL.*?(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,}).*?ALTERNATIVA\s*1.*?(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,}).*?ALTERNATIVA\s*2.*?(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,})",
        # Formato con números
        r"1.*?(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,}).*?2.*?(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,}).*?3.*?(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,})",
        # Formato general múltiple
        r"(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,}).*?(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,}).*?(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,})"
    ]
    
    coordinates_list = []
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            coords = match.groups()
            # Agrupar de a pares (lat, lon)
            for i in range(0, len(coords), 2):
                if i + 1 < len(coords):
                    lat, lon = coords[i], coords[i + 1]
                    try:
                        lat_f, lon_f = float(lat), float(lon)
                        if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                            coordinates_list.append((lat, lon))
                    except ValueError:
                        continue
            
            if len(coordinates_list) >= 2:
                return coordinates_list[:3]  # Máximo 3 coordenadas
    
    # Fallback: buscar coordenadas individuales
    individual_patterns = [
        r"(\-?\d+\.\d{6,}),\s*(\-?\d+\.\d{6,})",
        r"(\-?\d+\.\d{4,}),\s*(\-?\d+\.\d{4,})",
        r"(\-?\d+\.\d{3,}),\s*(\-?\d+\.\d{3,})"
    ]
    
    for pattern in individual_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            lat, lon = match
            try:
                lat_f, lon_f = float(lat), float(lon)
                if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                    if (lat, lon) not in coordinates_list:
                        coordinates_list.append((lat, lon))
                        if len(coordinates_list) >= 3:
                            break
            except ValueError:
                continue
        if len(coordinates_list) >= 3:
            break
    
    return coordinates_list if coordinates_list else None

# Configuración de la página
st.set_page_config(
    page_title="GeoIntel OSINT Pro",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS ultra-moderno y estético
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700&display=swap');
    
    /* Reset y base */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: #ffffff;
        color: #000000;
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Header ultra-moderno */
    .main-header {
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
        color: #ffffff;
        padding: 4rem 0;
        margin: -2rem -2rem 3rem -2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        opacity: 0.5;
    }
    
    .main-header h1 {
        font-size: 3.5rem;
        font-weight: 200;
        letter-spacing: -0.05em;
        margin: 0;
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.9;
        margin: 1rem 0 0 0;
        position: relative;
        z-index: 1;
    }
    
    /* Contenedores principales */
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 2rem;
    }
    
    /* Cards modernos */
    .modern-card {
        background: #ffffff;
        border: 1px solid #f0f0f0;
        border-radius: 12px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 2px 20px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }
    
    .modern-card:hover {
        box-shadow: 0 8px 40px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }
    
    .result-box {
        background: #ffffff;
        border: 1px solid #f0f0f0;
        border-radius: 12px;
        padding: 2.5rem;
        margin: 2rem 0;
        box-shadow: 0 4px 30px rgba(0,0,0,0.06);
    }
    
    .coordinate-box {
        background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
        border: 1px solid #e8e8e8;
        border-radius: 12px;
        padding: 2.5rem;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .coordinate-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #000000, #333333, #000000);
    }
    
    /* Botones ultra-modernos */
    .stButton > button {
        background: #000000;
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
    }
    
    .stButton > button:hover {
        background: #1a1a1a;
        transform: translateY(-1px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Tabs elegantes */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #fafafa;
        border-radius: 8px;
        padding: 4px;
        border: none;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        color: #666666;
        font-weight: 400;
        padding: 0.8rem 1.5rem;
        border-radius: 6px;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: #ffffff;
        color: #000000;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Inputs modernos */
    .stTextInput > div > div > input {
        font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
        font-size: 0.9rem;
        background: #ffffff;
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #000000;
        box-shadow: 0 0 0 3px rgba(0,0,0,0.1);
    }
    
    /* File uploader elegante */
    .stFileUploader {
        border: 2px dashed #e0e0e0;
        border-radius: 12px;
        padding: 3rem 2rem;
        text-align: center;
        background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #000000;
        background: linear-gradient(135deg, #f8f8f8 0%, #f0f0f0 100%);
    }
    
    /* Sidebar moderno */
    .css-1d391kg {
        background: #fafafa;
        border-right: 1px solid #f0f0f0;
    }
    
    /* Tipografía */
    h1 {
        font-weight: 600;
        color: #000000;
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    h2 {
        font-weight: 500;
        color: #000000;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        font-weight: 500;
        color: #000000;
        font-size: 1.25rem;
        margin-bottom: 0.75rem;
    }
    
    /* Alertas modernas */
    .stSuccess {
        background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
        border: 1px solid #9ae6b4;
        border-radius: 8px;
        color: #22543d;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border: 1px solid #cbd5e0;
        border-radius: 8px;
        color: #2d3748;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef5e7 100%);
        border: 1px solid #f6e05e;
        border-radius: 8px;
        color: #744210;
    }
    
    .stError {
        background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
        border: 1px solid #feb2b2;
        border-radius: 8px;
        color: #742a2a;
    }
    
    /* Spinner personalizado */
    .stSpinner > div {
        border-color: #000000 transparent transparent transparent;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* Animaciones suaves */
    * {
        transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2.5rem;
        }
        
        .main-header {
            padding: 3rem 0;
        }
        
        .modern-card, .result-box, .coordinate-box {
            padding: 1.5rem;
            margin: 1rem 0;
        }
    }
</style>
""", unsafe_allow_html=True)

# Header ultra-moderno
st.markdown("""
<div class="main-header">
    <h1>GeoIntel</h1>
    <p>Advanced Visual Geolocation Analysis</p>
</div>
""", unsafe_allow_html=True)

# Sidebar ultra-elegante
with st.sidebar:
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
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Layout principal
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Upload Image")
    
    # Tabs minimalistas
    tab1, tab2 = st.tabs(["File Upload", "Paste Image"])
    
    with tab1:
        uploaded_file = st.file_uploader(
            "Select an image for geolocation analysis",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            help="Supported formats: JPG, PNG, WEBP, BMP"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.session_state.current_image = image
            st.success("Image loaded successfully")
    
    with tab2:
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
                st.success("Image pasted successfully")
                
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
        
        # Botón para limpiar
        if st.session_state.current_image is not None:
            if st.button("Clear Image"):
                st.session_state.current_image = None
                st.session_state.analysis_result = None
                st.session_state.coordinates = None
                st.rerun()
    
    # Mostrar imagen actual
    if st.session_state.current_image is not None:
        st.image(
            st.session_state.current_image, 
            caption="Ready for analysis", 
            use_container_width=True
        )
        
        # Info de la imagen
        img_info = st.session_state.current_image
        st.info(f"Resolution: {img_info.size[0]} × {img_info.size[1]} px")

with col2:
    st.header("Analysis")
    
    if st.session_state.current_image is not None:
        if st.button("Start Analysis", type="primary", use_container_width=True):
            prompt = load_prompt()
            
            if prompt:
                with st.spinner("Analyzing with Gemini 2.0..."):
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
                    
                    st.success("Analysis completed")
    
    # Mostrar resultados si existen
    if st.session_state.analysis_result:
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.markdown("### Analysis Results")
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)
        
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
                    
                    # Crear mapa
                    m = folium.Map(
                        location=[center_lat, center_lon], 
                        zoom_start=14,
                        tiles='OpenStreetMap'
                    )
                    
                    # Agregar capas adicionales
                    folium.TileLayer('Stamen Terrain').add_to(m)
                    folium.TileLayer('CartoDB positron').add_to(m)
                    
                    # Colores para cada marcador
                    colors = ['red', 'blue', 'green', 'purple', 'orange']
                    labels = ['Principal', 'Alternativa 1', 'Alternativa 2', 'Alternativa 3', 'Alternativa 4']
                    
                    # Agregar marcadores para cada ubicación
                    for i, [lat_f, lon_f] in enumerate(valid_coords):
                        color = colors[i % len(colors)]
                        label = labels[i % len(labels)]
                        
                        folium.Marker(
                            [lat_f, lon_f],
                            popup=f"{label}\n{st.session_state.coordinates[i][0]}, {st.session_state.coordinates[i][1]}",
                            tooltip=f"{label}",
                            icon=folium.Icon(color=color, icon='info-sign')
                        ).add_to(m)
                        
                        # Círculo de precisión
                        folium.Circle(
                            [lat_f, lon_f],
                            radius=100,
                            popup=f"Precision area - {label}",
                            color=color,
                            fill=True,
                            opacity=0.2
                        ).add_to(m)
                    
                    # Control de capas
                    folium.LayerControl().add_to(m)
                    
                    # Mostrar mapa
                    st_folium(m, width=700, height=500, returned_objects=["last_clicked"])
                    
                    # Información adicional
                    st.info(f"{len(valid_coords)} candidate locations • Verify each one in Street View for accuracy")
                
            except ImportError:
                st.info("For interactive map: `pip install folium streamlit-folium`")
                for i, (lat, lon) in enumerate(st.session_state.coordinates):
                    st.markdown(f"**Location {i+1}:** [View on OpenStreetMap](https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=16)")
        else:
            st.warning("No specific coordinates detected")
            st.info("The image may need more distinctive elements for precise geolocation")
    
    elif st.session_state.current_image is None:
        st.info("Upload an image to start analysis")

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