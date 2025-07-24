# GeoIntel

A modern, minimalist web application for visual geolocation analysis using advanced AI technology.

## Features

- **Advanced AI Analysis**: Powered by Google Gemini 2.0 Flash
- **Multi-Candidate Locations**: Provides 2-3 location candidates for better accuracy
- **High-Precision Coordinates**: 6+ decimal precision for exact locations
- **Interactive Maps**: Integrated Folium maps with multiple layers
- **Modern Interface**: Clean, minimalist design in black and white
- **Multiple Input Methods**: File upload and clipboard paste support

## Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/geointel.git
cd geointel
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API Key**
```bash
cp config.example.py config.py
# Edit config.py and add your Gemini API key
```

4. **Run the application**
```bash
streamlit run app.py
```

## Configuration

Get your free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) and add it to `config.py`.

## Analysis Capabilities

The AI analyzes multiple visual elements:

- **Signage & Text**: Traffic signs, street names, commercial signage
- **Infrastructure**: Utility poles, road markings, architectural styles
- **Geographic Features**: Vegetation, terrain, climate indicators
- **Cultural Elements**: Vehicle types, architectural patterns, regional characteristics

## Technology Stack

- **Frontend**: Streamlit with custom CSS
- **AI Engine**: Google Gemini 2.0 Flash (with 1.5 Pro fallback)
- **Image Processing**: Pillow (PIL)
- **Mapping**: Folium with OpenStreetMap
- **Language**: Python 3.8+

## Usage

1. Upload an image or paste from clipboard
2. Click "Start Analysis"
3. Review multiple candidate locations
4. Copy coordinates to Google Maps for verification
5. Use interactive map to compare locations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Disclaimer

Results are AI-generated estimates based on visual analysis. Always verify locations using multiple sources for critical applications.