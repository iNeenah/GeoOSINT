# GeoOSINT

A modern, ultra-minimalist web application for advanced visual geolocation analysis using cutting-edge AI technology. Built for OSINT professionals and researchers.

![GeoOSINT](https://img.shields.io/badge/GeoOSINT-v1.0-black?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-black?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-black?style=for-the-badge&logo=streamlit)
![Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash-black?style=for-the-badge&logo=google)

## ✨ Features

### 🤖 Advanced AI Analysis
- **Google Gemini 2.0 Flash** as primary engine
- **Gemini 1.5 Pro** automatic fallback
- **Ultra-precise coordinate extraction** (6+ decimal places)
- **Forensic-level visual analysis**

### 📍 Multi-Candidate System
- **3 location candidates** per analysis
- **Confidence scoring** for each location
- **Cross-reference verification**
- **Interactive comparison tools**

### 🎨 Modern Interface
- **Ultra-minimalist design** in pure black & white
- **Professional typography** with Inter font
- **Responsive layout** for all devices
- **Clean, distraction-free experience**

### 🔧 Advanced Input Methods
- **Direct file upload** (JPG, PNG, WEBP, BMP)
- **Clipboard paste integration**
- **Screenshot processing**
- **Drag & drop support**

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/iNeenah/GeoOSINT.git
cd GeoOSINT
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
```bash
cp config.example.py config.py
```
Edit `config.py` and add your Gemini API key:
```python
GEMINI_API_KEY = "your-actual-api-key-here"
```

### 4. Launch Application
```bash
streamlit run app.py
```

## 🔑 API Configuration

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key (free tier available)
3. Copy the key to `config.py`
4. Save and restart the application

## 🧠 Analysis Engine

### Visual Elements Analyzed
- **Signage & Text**: Traffic signs, street names, commercial signage, license plates
- **Infrastructure**: Utility poles, road markings, architectural styles, urban furniture
- **Geographic Features**: Vegetation types, terrain characteristics, climate indicators
- **Cultural Elements**: Vehicle models, architectural patterns, regional characteristics
- **Environmental Clues**: Sun position, shadows, weather conditions, lighting

### Analysis Process
1. **Systematic Visual Scanning**: Pixel-by-pixel examination
2. **Element Identification**: Recognition of distinctive regional features
3. **Geographic Triangulation**: Cross-referencing multiple visual cues
4. **Confidence Assessment**: Scoring based on evidence strength
5. **Multi-Candidate Generation**: Providing alternative possibilities

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit with custom CSS |
| **AI Engine** | Google Gemini 2.0 Flash |
| **Backup AI** | Google Gemini 1.5 Pro |
| **Image Processing** | Pillow (PIL) |
| **Mapping** | Folium + OpenStreetMap |
| **Language** | Python 3.8+ |
| **Styling** | Custom CSS with Inter font |

## 📱 Usage Guide

### Step-by-Step Process
1. **Upload Image**: Use file upload or paste from clipboard
2. **Start Analysis**: Click the analysis button
3. **Review Results**: Examine detailed analysis report
4. **Check Candidates**: Review 2-3 location possibilities
5. **Verify Locations**: Use provided Google Maps/Street View links
6. **Copy Coordinates**: Use formatted coordinate fields

### Best Practices
- Use **high-resolution images** for better accuracy
- Images with **distinctive landmarks** work best
- **Multiple visual elements** improve precision
- Always **verify results** using Street View
- Consider **multiple candidates** for validation

## 🔒 Security & Privacy

- **API keys protected** via `.gitignore`
- **No image storage** - processed in memory only
- **No user data collection**
- **Local processing** when possible

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Important**: Results are AI-generated estimates based on visual analysis. This tool is designed for:
- **Research purposes**
- **Educational use**
- **OSINT investigations**
- **Geographic reference**

Always verify locations using multiple sources for critical applications. Not suitable for emergency services or life-critical decisions.

## 🌟 Acknowledgments

- **Google AI** for Gemini API access
- **Streamlit** for the amazing framework
- **OpenStreetMap** for mapping services
- **OSINT Community** for inspiration and feedback

---

<div align="center">
<strong>GeoOSINT</strong> - Advanced Visual Geolocation Analysis<br>
Built with ❤️ for the OSINT community
</div>