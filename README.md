# GeoIntel OSINT Pro

A professional visual geolocation analysis platform powered by advanced AI technology. Designed for OSINT professionals, researchers, and intelligence analysts requiring precise location identification from visual imagery.

![GeoIntel](https://img.shields.io/badge/GeoIntel-OSINT%20Pro-black?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-black?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-black?style=for-the-badge&logo=streamlit)
![Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash-black?style=for-the-badge&logo=google)

## Features

### Advanced AI Analysis Engine
- **Google Gemini 2.0 Flash** primary analysis engine
- **Gemini 1.5 Pro** automatic fallback system
- **Google Lens integration** for visual search and object recognition
- **Multiple reverse image search** engines (Google, Yandex, TinEye)
- **Military-grade precision** coordinate extraction (6+ decimal places)
- **Forensic-level visual pattern recognition**
- **Multi-language support** with English output standardization

### Professional Analysis Capabilities
- **Single Image Analysis** - Precise location identification from individual images
- **360° Multi-Image Analysis** - Enhanced accuracy using multiple angles of the same location
- **Google Lens Integration** - Direct access to Google's visual search capabilities
- **Multi-Engine Reverse Search** - Cross-platform image searching (Google, Yandex, TinEye)
- **Cross-reference verification** system for improved reliability
- **Confidence scoring** for each location candidate
- **Interactive mapping** with professional satellite imagery

### Clean Professional Interface
- **Minimalist design** focused on functionality
- **Dark/Light theme** toggle for user preference
- **Professional typography** optimized for readability
- **Responsive layout** for desktop and mobile use
- **Distraction-free analysis environment**

### Advanced Input Methods
- **File upload** support (JPG, PNG, WEBP, BMP)
- **Clipboard integration** for quick image pasting
- **Multiple file processing** for 360° analysis
- **EXIF data extraction** and GPS coordinate detection
- **Metadata analysis** for additional intelligence
- **External search integration** with one-click access to multiple search engines

## Quick Start

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/geointel-osint-pro.git
cd geointel-osint-pro
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API access**
```bash
cp config.example.py config.py
```

Edit `config.py` with your Gemini API key:
```python
GEMINI_API_KEY = "your-gemini-api-key-here"
```

4. **Launch the application**
```bash
streamlit run app.py
```

### API Key Setup

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key (free tier available)
3. Copy the key to your `config.py` file
4. Restart the application

## Analysis Methodology

### Visual Intelligence Framework

The system employs a comprehensive 7-level analysis protocol:

**Level 1: Critical Signage Analysis**
- Traffic signs, road markers, street names
- Language identification and regional typography
- Speed limit formats (km/h vs mph)
- Commercial signage and text analysis

**Level 2: Infrastructure Assessment**
- Utility pole construction (wood/concrete/metal)
- Power line configurations and insulators
- Road surface materials and markings
- Drainage systems and street furniture

**Level 3: Transportation Elements**
- License plate formats and colors
- Vehicle model predominance by region
- Driving side identification
- Public transportation systems

**Level 4: Environmental Analysis**
- Flora species and climate indicators
- Topographical features
- Soil composition and coloration
- Seasonal vegetation patterns

**Level 5: Architectural Recognition**
- Building styles and materials
- Roof construction patterns
- Window and door designs
- Regional construction methods

**Level 6: Cultural Pattern Analysis**
- National and regional symbols
- Commercial activity patterns
- Sports facilities and recreational areas
- Urban planning characteristics

**Level 7: Micro-Detail Forensics**
- Postal system indicators
- Waste management systems
- Electrical standards and fixtures
- Address numbering systems

### Analysis Process

1. **Systematic Visual Scanning** - Comprehensive image examination
2. **Element Identification** - Recognition of distinctive regional features
3. **Geographic Elimination** - Ruling out incompatible regions
4. **Triangulation** - Cross-referencing multiple visual cues
5. **External Verification** - Google Lens and reverse image search integration
6. **Coordinate Generation** - Precise location calculation
7. **Confidence Assessment** - Evidence-based reliability scoring

### Google Lens Integration (Automatic)

**Built-in Google Lens Simulator**
- **Automatic text recognition (OCR)** - Extract text directly from images
- **Object and landmark detection** - Identify visual elements automatically
- **Location clue extraction** - Find addresses, street names, and geographic indicators
- **Dominant color analysis** - Analyze image color patterns
- **Shape detection** - Identify geometric patterns and structures
- **Web search integration** - Automatic search based on extracted information
- **Copy-paste functionality** - Easy text copying like Google Lens

**Multi-Engine Reverse Search**
- **Google Images** - Comprehensive image source tracking
- **Yandex Images** - Excellent for Eastern European content
- **TinEye** - Specialized reverse image search with detailed tracking
- **Cross-platform verification** for enhanced accuracy

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **AI Engine** | Google Gemini 2.0 Flash | Primary analysis |
| **Backup AI** | Google Gemini 1.5 Pro | Fallback system |
| **Frontend** | Streamlit | Web interface |
| **Mapping** | Folium + Multiple tile layers | Interactive maps |
| **Image Processing** | Pillow (PIL) | Image manipulation |
| **Metadata** | ExifRead | EXIF data extraction |
| **Styling** | Custom CSS | Professional UI |

## Professional Usage

### Google Lens Integration

The application includes a built-in Google Lens simulator that automatically:

1. **Upload Image** - Simply upload your image to the platform
2. **Click "Analyze with Google Lens"** - Automatic analysis begins
3. **Text Extraction** - All visible text is extracted and made copyable
4. **Object Detection** - Visual elements and landmarks are identified
5. **Location Clues** - Street names, addresses, and geographic indicators are found
6. **Results Display** - All information is presented in an organized format

**Key Features:**
- **Automatic OCR** - No manual text selection needed
- **Copy-paste functionality** - Click to copy extracted text
- **Location intelligence** - Automatic geographic clue detection
- **Visual analysis** - Color and shape pattern recognition

### Analysis Modes

**Single Image Analysis**
- Individual image processing
- Rapid location identification
- Suitable for quick assessments
- Ideal for single-source intelligence

**360° Multi-Image Analysis**
- Multiple angle processing
- Enhanced accuracy through triangulation
- Elimination of visual blind spots
- Cross-verification of elements
- Recommended for critical investigations

### Best Practices

**Image Quality**
- Use high-resolution images when possible
- Ensure clear visibility of distinctive elements
- Multiple angles improve accuracy
- Avoid heavily compressed images

**Analysis Verification**
- Always verify results using multiple sources
- Cross-check with satellite imagery
- Use Street View for ground truth validation
- Consider temporal factors (image age)

**Security Considerations**
- Images are processed in memory only
- No permanent storage of uploaded content
- API keys are protected via environment variables
- No user data collection or tracking

## Output Format

The system provides structured analysis in English:

```
LOCATION ANALYSIS:
Country: [Identified country]
City/Region: [Specific location]
Confidence Level: [High/Medium/Low]

COORDINATES:
Primary Location: [Precise coordinates]
Alternative Location 1: [Backup coordinates]
Alternative Location 2: [Additional option]

KEY EVIDENCE:
[Detailed analysis of visual elements]

FINAL ASSESSMENT:
[Summary and confidence rating]
```

## Contributing

We welcome contributions from the OSINT community:

1. **Fork** the repository
2. **Create** a feature branch
3. **Implement** improvements or fixes
4. **Test** thoroughly
5. **Submit** a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Include comprehensive comments
- Test with various image types
- Maintain professional code standards

## Security & Privacy

- **No data retention** - Images processed in memory only
- **API key protection** via secure configuration
- **No user tracking** or analytics
- **Local processing** where possible
- **Secure communication** with AI services

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

**Important Notice**: This tool provides AI-generated location estimates based on visual analysis. Results should be verified through multiple sources for critical applications.

**Intended Use**:
- Research and educational purposes
- OSINT investigations and analysis
- Geographic reference and verification
- Intelligence gathering support

**Not Suitable For**:
- Emergency response coordination
- Life-critical decision making
- Legal evidence without verification
- Real-time operational intelligence

## Acknowledgments

- **Google AI** for Gemini API access and advanced language models
- **Streamlit** for the exceptional web application framework
- **OpenStreetMap** and **Esri** for mapping services
- **OSINT Community** for continuous feedback and improvement suggestions

---

<div align="center">
<strong>GeoIntel OSINT Pro</strong><br>
Professional Visual Geolocation Analysis Platform<br>
Built for the Intelligence Community
</div>