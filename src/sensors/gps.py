from typing import Optional, Tuple

class GPS:
    def __init__(self, port: str | None = None, baud: int = 9600):
        self.port = port
        self.baud = baud
        self._serial = None
        try:
            if port:
                import serial  # noqa: F401
                # Defer opening until first read to avoid errors on desktops
        except Exception:
            pass

    def read_location(self) -> Optional[Tuple[float, float]]:
        # Stubbed: integrate pyserial + NMEA parsing when hardware present
        return None
