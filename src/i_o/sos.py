import time
from typing import Optional, Tuple

from sensors.gps import GPS
from config import (
    TWILIO_SID, TWILIO_AUTH, TWILIO_FROM, TWILIO_WHATSAPP_FROM,
    EMERGENCY_CONTACT, EMERGENCY_CONTACT_WHATSAPP,
    EMERGENCY_EMAIL, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
)

try:
    from i_o.tts import speak_async as _speak
except Exception:
    def _speak(text: str):
        try:
            print(f"[TTS] {text}")
        except Exception:
            pass


def _maps_link(lat: float, lon: float) -> str:
    return f"https://maps.google.com/?q={lat},{lon}"


def _normalize_e164(number: str | None) -> str | None:
    if not number:
        return None
    n = number.strip()
    # Fix accidental double '+'
    while n.startswith('++'):
        n = n[1:]
    if not n.startswith('+'):
        n = '+' + n
    return n


def _normalize_whatsapp(from_number: str | None) -> str | None:
    if not from_number:
        return None
    n = from_number.strip()
    if not n.startswith('whatsapp:'):
        n = 'whatsapp:' + _normalize_e164(n)
    return n


def _send_twilio_sms(msg: str) -> bool:
    if not (TWILIO_SID and TWILIO_AUTH and TWILIO_FROM and EMERGENCY_CONTACT):
        return False
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_AUTH)
        from_num = _normalize_e164(TWILIO_FROM)
        to_num = _normalize_e164(EMERGENCY_CONTACT)
        client.messages.create(body=msg, from_=from_num, to=to_num)
        return True
    except Exception as e:
        print(f"⚠️ Twilio SMS error: {e}")
        return False


def _send_twilio_whatsapp(msg: str) -> bool:
    # Use explicit WA sender if provided; else derive from TWILIO_FROM
    from_wa = TWILIO_WHATSAPP_FROM or _normalize_whatsapp(TWILIO_FROM)
    if not (TWILIO_SID and TWILIO_AUTH and from_wa and EMERGENCY_CONTACT_WHATSAPP):
        return False
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_AUTH)
        to_wa = EMERGENCY_CONTACT_WHATSAPP
        if not to_wa.startswith('whatsapp:'):
            to_wa = 'whatsapp:' + _normalize_e164(to_wa)
        client.messages.create(body=msg, from_=from_wa, to=to_wa)
        return True
    except Exception as e:
        print(f"⚠️ Twilio WhatsApp error: {e}")
        return False


def _send_email(msg: str) -> bool:
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and EMERGENCY_EMAIL):
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText
        mime = MIMEText(msg)
        mime["Subject"] = "Emergency Alert"
        mime["From"] = SMTP_USER
        mime["To"] = EMERGENCY_EMAIL
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(mime)
        return True
    except Exception as e:
        print(f"⚠️ Email error: {e}")
        return False


class SOS:
    def __init__(self, enabled: bool = True, press_window_s: float = 1.5, retries: int = 3):
        self.enabled = enabled
        self.press_window_s = press_window_s
        self._press_times: list[float] = []
        self._gps = GPS()
        self._retries = retries

    def press(self):
        if not self.enabled:
            return
        now = time.time()
        self._press_times = [t for t in self._press_times if now - t <= self.press_window_s]
        self._press_times.append(now)
        if len(self._press_times) >= 3:
            self._press_times.clear()
            self.trigger()

    def _get_location(self) -> Tuple[Optional[float], Optional[float]]:
        loc = self._gps.read_location()
        if loc:
            return loc[0], loc[1]
        return None, None

    def trigger(self, message: Optional[str] = None):
        if not self.enabled:
            return
        lat, lon = self._get_location()
        link = _maps_link(lat, lon) if lat is not None and lon is not None else "location unavailable"
        payload = message or "SOS triggered"
        print(f"🔴 SOS: {payload} — {link}")

        _speak("Sending emergency alert")

        body = f"🚨 SOS Alert! {payload}. Location: {link}"
        sent = False
        for attempt in range(1, self._retries + 1):
            # Try WhatsApp first (if configured), then SMS, then Email
            if _send_twilio_whatsapp(body):
                sent = True
            elif _send_twilio_sms(body):
                sent = True
            elif _send_email(body):
                sent = True
            if sent:
                break
            time.sleep(0.5)

        if sent:
            _speak("SOS sent successfully")
            print("✅ SOS sent successfully")
        else:
            _speak("SOS failed. Please call for help")
            print("❌ SOS delivery failed. Check credentials/network.")

    # Optional: GPIO button watcher (call in a thread on Raspberry Pi)
    def poll_button(self, pin: int = 18):
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            press_count = 0
            last_press = 0.0
            while True:
                if not GPIO.input(pin):
                    now = time.time()
                    if now - last_press < self.press_window_s:
                        press_count += 1
                    else:
                        press_count = 1
                    last_press = now
                    if press_count >= 3:
                        self.trigger()
                        press_count = 0
                        last_press = 0.0
                    time.sleep(0.2)
                time.sleep(0.05)
        except Exception as e:
            print(f"⚠️ Button watcher error: {e}")
