"""Ultrasonic distance sensor (HC-SR04 or similar)."""
import statistics
import time
import math
from typing import Optional

class Ultrasonic:
    """HC-SR04 ultrasonic distance sensor."""
    
    def __init__(self, trigger_pin: int = 23, echo_pin: int = 24):
        """
        Initialize ultrasonic sensor.
        
        Args:
            trigger_pin: GPIO pin for trigger
            echo_pin: GPIO pin for echo
        """
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.gpio = None
        self._sim_manual: Optional[float] = None  # meters; if set, use this value
        self._sim_t0 = time.time()
        
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.trigger_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)
            self.gpio = GPIO
            print(f"✅ Ultrasonic sensor initialized (trigger={trigger_pin}, echo={echo_pin})")
        except ImportError:
            print("⚠️ RPi.GPIO not available. Running in simulation mode.")
        except Exception as e:
            print(f"⚠️ GPIO setup error: {e}. Running in stub mode.")
    
    def read_distance(self) -> Optional[float]:
        """
        Read distance in meters.
        
        Returns:
            Distance in meters or None if invalid
        """
        if self.gpio is None:
            # Simulation: oscillate between ~0.4m and ~3.0m unless manually overridden
            if self._sim_manual is not None:
                return max(0.05, min(4.0, float(self._sim_manual)))
            t = time.time() - self._sim_t0
            # Smooth sine wave between 0.4 and 3.0 meters
            base = 1.7 + 1.3 * math.sin(2 * math.pi * (t / 5.0))
            return max(0.4, min(3.0, base))
        
        try:
            # Send trigger pulse
            self.gpio.output(self.trigger_pin, False)
            time.sleep(0.00001)
            self.gpio.output(self.trigger_pin, True)
            time.sleep(0.00001)
            self.gpio.output(self.trigger_pin, False)
            
            # Wait for echo
            start_time = time.time()
            timeout = start_time + 0.1  # 100ms timeout
            
            while self.gpio.input(self.echo_pin) == 0:
                if time.time() > timeout:
                    return None
                start_time = time.time()
            
            echo_start = time.time()
            timeout = echo_start + 0.1
            
            while self.gpio.input(self.echo_pin) == 1:
                if time.time() > timeout:
                    return None
                echo_end = time.time()
            
            # Calculate distance (speed of sound = 343 m/s)
            duration = echo_end - echo_start
            distance = (duration * 343.0) / 2.0  # Divide by 2 for round trip
            
            # Valid range: 2cm to 4m
            if 0.02 <= distance <= 4.0:
                return distance
            return None
            
        except Exception as e:
            print(f"⚠️ Ultrasonic read error: {e}")
            return None
    
    def median(self, n: int = 5) -> Optional[float]:
        """
        Get median distance from multiple readings.
        
        Args:
            n: Number of readings
        
        Returns:
            Median distance in meters or None
        """
        vals = []
        for _ in range(n):
            d = self.read_distance()
            if d is not None:
                vals.append(d)
            time.sleep(0.02)  # 20ms between readings
        
        return statistics.median(vals) if vals else None
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        if self.gpio:
            try:
                self.gpio.cleanup()
            except Exception:
                pass

    # --- Simulation helpers ---
    def set_sim_distance(self, meters: Optional[float]):
        """Set manual simulated distance. Use None to clear and return to oscillation."""
        self._sim_manual = meters

    def clear_sim_override(self):
        """Clear manual override and resume oscillation."""
        self._sim_manual = None
