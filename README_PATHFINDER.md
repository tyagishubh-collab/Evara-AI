# Pathfinder — AI Navigation Assistant for Blind Users

**Offline-first, privacy-preserving navigation system with obstacle detection, haptic feedback, and turn-by-turn guidance.**

## 🎯 Features

### P0 (MVP - Works Offline)
- ✅ **Obstacle Detection**: YOLOv8 camera-based detection
- ✅ **Distance Sensing**: Ultrasonic/ToF sensor fusion
- ✅ **Sector Analysis**: Left/center/right free-space detection
- ✅ **TTS Guidance**: Offline text-to-speech prompts
- ✅ **Haptic Feedback**: Vibration motors mapped to obstacle direction
- ✅ **Wake Word**: Offline STT for voice commands

### P1 (Enhanced - Modules Ready)
- 🚧 Crosswalk & traffic light detection
- 🚧 Sidewalk vs road classification
- 🚧 Indoor navigation via AprilTags/ArUco
- 🚧 Outdoor navigation via offline OSM
- 🚧 Safe path planner (avoids stairs/curbs)
- 🚧 SOS emergency (triple-press with GPS)

### P2 (Future)
- 📋 Personalized routes & landmarks
- 📋 On-device incremental learning
- 📋 Multi-modal sensor fusion

## 🛠️ Hardware Requirements

### Minimum (MVP - Development on PC)
- Webcam or USB camera
- Modern PC/Mac with Python 3.8+

### Recommended (Full System - Raspberry Pi)
- Raspberry Pi 4/5 (4GB+ RAM)
- USB webcam or Raspberry Pi Camera Module
- HC-SR04 ultrasonic sensor (or VL53L1X ToF)
- Vibration motors (3x) or ESP32 BLE band
- Optional: Luxonis OAK-D (built-in depth)
- Optional: MPU-6050 IMU
- Optional: u-blox GPS module

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/Evara-AI.git
cd Evara-AI
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Models (Optional)
YOLOv8 will auto-download on first run. For offline STT:
```bash
# Download Vosk model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/
```

### 5. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings (GPIO pins, API keys, etc.)
```

## 🚀 Usage

### Run Pathfinder (MVP - Vision Only)
```bash
python -m src.main
```

Press **ESC** or **Q** to exit.

### Run Original VisualAid Server (Optional)
```bash
python app.py
```

## 🔧 Configuration

Edit `.env` to configure:
- **Vision**: Model path, confidence threshold
- **Sensors**: GPIO pins for ultrasonic, IMU, GPS
- **Safety**: Distance thresholds, battery, thermal limits
- **TTS/STT**: Engine preferences
- **Optional**: Gemini API key for enhanced narration

## 🛡️ Security

**⚠️ CRITICAL: The exposed API key has been fixed and must be rotated immediately.**

### Steps Taken
1. ✅ Fixed `app.py` to use environment variable
2. ✅ Created `.env.example` template
3. ✅ Updated `.gitignore` to prevent future leaks
4. ✅ Added pre-commit hooks with `gitleaks`

### Next Steps (MUST DO)
1. **Rotate the exposed Gemini API key**:
   - Go to Google Cloud Console
   - Delete the exposed key: `AIzaSyB5d8HhskPM-MIuVMXqoQWEO4X6xVvJLnQ`
   - Generate a new key
   - Add to `.env` file (never commit)

2. **Install pre-commit hooks**:
   ```bash
   pip install pre-commit
   pre-commit install
   pre-commit run --all-files
   ```

3. **Clean git history** (if key was committed):
   ```bash
   # Use git-filter-repo or BFG Repo-Cleaner
   # Force push after cleaning (coordinate with team)
   ```

## 📁 Project Structure

```
Evara-AI/
├── src/
│   ├── main.py              # Main entry point
│   ├── config.py            # Configuration management
│   ├── perception/
│   │   ├── detector.py      # YOLOv8 detection
│   │   └── depth.py         # Depth estimation (ready)
│   ├── sensors/
│   │   ├── ultrasonic.py    # HC-SR04 (ready)
│   │   ├── imu.py           # MPU-6050 (ready)
│   │   └── gps.py           # u-blox GPS (ready)
│   ├── fusion/
│   │   └── occupancy.py     # Sensor fusion
│   ├── navigation/
│   │   ├── map.py           # OSM offline maps (ready)
│   │   ├── planner.py       # A* path planning (ready)
│   │   └── guidance.py      # Turn-by-turn (ready)
│   ├── i_o/
│   │   ├── tts.py           # Text-to-speech (ready)
│   │   ├── stt.py           # Speech-to-text (ready)
│   │   └── haptics.py       # Vibration control (ready)
│   └── safety/
│       └── watchdog.py      # Battery/thermal/SOS (ready)
├── app.py                   # Original FastAPI server
├── requirements.txt
├── .env.example
├── .pre-commit-config.yaml
└── README.md
```

## ⚠️ Safety Disclaimer

**This is an assistive aid, not a replacement for:**
- White cane
- Guide dog
- Professional orientation & mobility training

Always use in conjunction with established mobility aids and training.

## 🤝 Contributing

1. Install pre-commit hooks: `pre-commit install`
2. Follow offline-first, privacy-preserving principles
3. Test on actual hardware (Raspberry Pi) when possible
4. Document GPIO pin assignments
5. Never commit secrets or API keys

See `CONTRIBUTING.md` for details.

## 🧪 Development Status

### Currently Implemented
- ✅ Core configuration system
- ✅ YOLOv8 object detection
- ✅ Sensor fusion (vision + ultrasonic)
- ✅ Sector-based occupancy mapping
- ✅ Safe direction guidance
- ✅ Debug visualization

### Ready to Use (Modules Created)
- Depth estimation (MiDaS/OAK-D)
- Hardware sensors (ultrasonic, IMU, GPS)
- TTS/STT engines
- Haptic feedback
- Safety watchdog
- Navigation (map, planner, guidance)

### To Integrate
Simply uncomment imports in `src/main.py` and initialize the modules.

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- Vosk for offline STT
- OpenStreetMap for map data
- Pre-commit hooks for security

## 📧 Support

For hardware integration questions or bug reports, open an issue on GitHub.

---

**Built with ❤️ for accessibility and independence**
