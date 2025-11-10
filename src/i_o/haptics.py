class Haptics:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._warned = False
        try:
            import bleak  # noqa: F401
            self._ble_available = True
        except Exception:
            self._ble_available = False

    def map_intensity(self, occupied: bool, distance_m: float | None, danger_m: float = 1.5, max_m: float = 3.0) -> int:
        if not occupied:
            return 0
        if distance_m is None:
            return 40
        if distance_m <= 0:
            return 100
        if distance_m >= max_m:
            return 20
        scale = max(danger_m, 0.2)
        v = int(min(100, max(20, 100 * (scale / max(distance_m, 0.05)))))
        return v

    def send(self, left: int, center: int, right: int):
        if not self.enabled:
            return
        if not self._ble_available:
            if not self._warned:
                print("⚠️ BLE not available; haptics disabled")
                self._warned = True
            return
        try:
            pass
        except Exception:
            pass
