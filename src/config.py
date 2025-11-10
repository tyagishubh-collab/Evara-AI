"""Configuration management for Pathfinder."""
import os
from dotenv import load_dotenv

load_dotenv()

# Vision
VISION_MODEL = os.getenv("VISION_MODEL", "yolov8n.pt")

# TTS/STT
TTS_ENGINE = os.getenv("TTS_ENGINE", "pyttsx3")
STT_MODEL = os.getenv("STT_MODEL", "vosk-model-small-en-us-0.15")
TTS_FORCE_SAPI = os.getenv("TTS_FORCE_SAPI", "false").lower() == "true"
TTS_VOICE_INDEX = int(os.getenv("TTS_VOICE_INDEX", "0"))

# Sensors
ULTRASONIC_TRIGGER_PIN = int(os.getenv("ULTRASONIC_TRIGGER_PIN", "23"))
ULTRASONIC_ECHO_PIN = int(os.getenv("ULTRASONIC_ECHO_PIN", "24"))
IMU_I2C_ADDRESS = int(os.getenv("IMU_I2C_ADDRESS", "0x68"), 16)
GPS_SERIAL_PORT = os.getenv("GPS_SERIAL_PORT", "/dev/ttyUSB0")

# Safety
DANGER_DISTANCE_M = float(os.getenv("DANGER_DISTANCE_M", "1.5"))
BATTERY_LOW_VOLTAGE = float(os.getenv("BATTERY_LOW_VOLTAGE", "3.3"))
THERMAL_MAX_C = float(os.getenv("THERMAL_MAX_C", "70"))

# Navigation
OSM_DATA_DIR = os.getenv("OSM_DATA_DIR", "./data/osm")
INDOOR_TAGS_DIR = os.getenv("INDOOR_TAGS_DIR", "./data/tags")

# Optional: Gemini (for enhanced narration)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USE_GEMINI = bool(GEMINI_API_KEY)

# SOS / Alerts
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_FROM = os.getenv("TWILIO_FROM")
EMERGENCY_CONTACT = os.getenv("EMERGENCY_CONTACT")  # E.164 phone, e.g., +91XXXXXXXXXX
EMERGENCY_CONTACT_WHATSAPP = os.getenv("EMERGENCY_CONTACT_WHATSAPP")  # e.g., whatsapp:+91XXXXXXXXXX
EMERGENCY_EMAIL = os.getenv("EMERGENCY_EMAIL")

# SMTP (optional, for email backup)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
