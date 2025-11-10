from typing import Optional, Tuple

try:
    from config import GPS_SERIAL_PORT
except Exception:
    GPS_SERIAL_PORT = None


class GPS:
    def __init__(self, port: str | None = None, baud: int = 9600, timeout: float = 1.0):
        self.port = port or GPS_SERIAL_PORT
        self.baud = baud
        self.timeout = timeout
        self._serial = None
        self._warned = False
        try:
            if self.port:
                import serial  # noqa: F401
                import pynmea2  # noqa: F401
                # Defer opening until first read to avoid errors on desktops
        except Exception:
            # Missing dependencies are handled on read
            pass

    def _open_if_needed(self):
        if self._serial is not None:
            return True
        if not self.port:
            if not self._warned:
                print("⚠️ GPS port not configured (set GPS_SERIAL_PORT in .env)")
                self._warned = True
            return False
        try:
            import serial
            self._serial = serial.Serial(self.port, baudrate=self.baud, timeout=self.timeout)
            return True
        except Exception as e:
            if not self._warned:
                print(f"⚠️ GPS open error on {self.port}: {e}")
                self._warned = True
            return False

    def read_location(self) -> Optional[Tuple[float, float]]:
        """Read a single (lat, lon) from NMEA. Returns None if unavailable.
        Parses common talkers: GGA (fix), RMC (recommended minimum).
        """
        try:
            import pynmea2
        except Exception:
            if not self._warned:
                print("⚠️ pynmea2 not installed. Install: pip install pyserial pynmea2")
                self._warned = True
            return None

        if not self._open_if_needed():
            return None

        try:
            # Read a few lines to find a valid fix quickly
            for _ in range(30):
                line = self._serial.readline()
                if not line:
                    continue
                try:
                    s = line.decode('ascii', errors='replace').strip()
                except Exception:
                    continue
                if not (s.startswith('$GPGGA') or s.startswith('$GNGGA') or s.startswith('$GPRMC') or s.startswith('$GNRMC')):
                    continue
                try:
                    msg = pynmea2.parse(s)
                except Exception:
                    continue
                # Prefer RMC if it has valid status
                if msg.sentence_type == 'RMC':
                    # Status A = valid
                    status = getattr(msg, 'status', 'V')
                    if status == 'A' and msg.latitude and msg.longitude:
                        return float(msg.latitude), float(msg.longitude)
                elif msg.sentence_type == 'GGA':
                    # fix_quality > 0 means valid
                    fix_q = getattr(msg, 'gps_qual', 0)
                    if fix_q and msg.latitude and msg.longitude:
                        return float(msg.latitude), float(msg.longitude)
            return None
        except Exception as e:
            # Any serial error -> drop connection and report once
            try:
                if self._serial:
                    self._serial.close()
            except Exception:
                pass
            self._serial = None
            if not self._warned:
                print(f"⚠️ GPS read error: {e}")
                self._warned = True
            return None
