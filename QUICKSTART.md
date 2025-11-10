# Pathfinder Quick Start Guide

## ⚡ Get Started in 5 Minutes

### 1. Setup (First Time Only)

```bash
# Clone and enter directory
cd Evara-AI

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env
```

### 2. Run Pathfinder MVP

```bash
# Make sure you're in the Evara-AI directory
python -m src.main
```

**Controls:**
- Press **ESC** or **Q** to exit
- The window shows:
  - Green boxes: detected objects
  - Blue circles: sector status (green=clear, red=blocked)
  - White text: distance info

### 3. What You'll See

The system will:
1. Open your webcam
2. Detect obstacles in real-time
3. Print guidance messages like:
   - `[GUIDANCE] clear path. Safe direction: forward`
   - `[GUIDANCE] obstacle ahead, 2.0 meters. Safe direction: left`

## 🔧 Troubleshooting

### Camera Not Opening
- Ensure webcam is connected
- Close other apps using the camera
- Try different camera index: edit `src/main.py` line 55, change `0` to `1`

### Module Import Errors
```bash
# Make sure you're running as a module:
python -m src.main

# NOT: python src/main.py
```

### YOLO Model Download
First run downloads ~6MB model automatically. Wait for:
```
✅ YOLO model loaded: yolov8n.pt
```

## 🎯 Next Steps

### Add Hardware Sensors
1. Connect HC-SR04 ultrasonic sensor to GPIO pins
2. Update `.env` with pin numbers:
   ```
   ULTRASONIC_TRIGGER_PIN=23
   ULTRASONIC_ECHO_PIN=24
   ```
3. Uncomment sensor imports in `src/main.py`

### Enable Voice Guidance
```bash
# Install TTS
pip install pyttsx3

# Uncomment TTS imports in src/main.py
# Replace print(f"[GUIDANCE] {message}") with:
# self.tts.speak(message)
```

### Test Original VisualAid Server
```bash
python app.py
# Visit http://localhost:8000
```

## 🛡️ Security Reminder

**Before committing any changes:**

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run security scan
pre-commit run --all-files
```

**Never commit:**
- `.env` file (contains secrets)
- Large model files (*.pt, *.onnx)
- Personal data

## 📖 Full Documentation

- `README_PATHFINDER.md` - Complete system overview
- `.env.example` - All configuration options
- `src/config.py` - Configuration values
- Hardware module files in `src/sensors/`, `src/i_o/`, `src/navigation/`

## 🆘 Need Help?

1. Check if webcam works: `python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"`
2. Check Python version: `python --version` (need 3.8+)
3. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

---

**Ready to go! 🚀**
