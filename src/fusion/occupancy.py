"""Sensor fusion: combine camera detections with ultrasonic range."""
import numpy as np
from typing import List, Dict, Optional

SECTORS = 3  # left, center, right

def sectors_from_detections(width: int, detections: List[Dict]) -> np.ndarray:
    """
    Convert detections to sector occupancy map.
    
    Args:
        width: Frame width in pixels
        detections: List of detection dicts with 'bbox' key
    
    Returns:
        Boolean array [left, center, right] indicating occupied sectors
    """
    occupancy = np.zeros(SECTORS, dtype=bool)
    
    for det in detections:
        x1, _, x2, _ = det["bbox"]
        center_x = (x1 + x2) / 2.0
        
        # Map to sectors
        if center_x < width / 3:
            occupancy[0] = True  # Left
        elif center_x > 2 * width / 3:
            occupancy[2] = True  # Right
        else:
            occupancy[1] = True  # Center
    
    return occupancy

def fuse_with_range(occupancy: np.ndarray,
                    distance_m: Optional[float],
                    danger_m: float = 1.5) -> np.ndarray:
    """
    Fuse vision-based occupancy with ultrasonic range.
    
    Args:
        occupancy: Boolean array [left, center, right]
        distance_m: Ultrasonic distance in meters
        danger_m: Danger threshold distance
    
    Returns:
        Fused occupancy array
    """
    fused = occupancy.copy()
    
    # If ultrasonic detects close obstacle, mark center as blocked
    if distance_m is not None and distance_m < danger_m:
        fused[1] = True  # Center blocked
    
    return fused

def describe_occupancy(occupancy: np.ndarray,
                       distance_m: Optional[float] = None) -> str:
    """
    Generate human-readable description of occupancy.
    
    Args:
        occupancy: Boolean array [left, center, right]
        distance_m: Optional distance in meters
    
    Returns:
        Description string
    """
    labels = []
    
    if occupancy[1]:  # Center
        labels.append("ahead")
    if occupancy[0]:  # Left
        labels.append("left")
    if occupancy[2]:  # Right
        labels.append("right")
    
    if not labels:
        desc = "clear path"
    else:
        desc = "obstacle " + " and ".join(labels)
    
    if distance_m is not None:
        desc += f", {distance_m:.1f} meters"
    
    return desc

def get_safe_direction(occupancy: np.ndarray) -> Optional[str]:
    """
    Determine safest direction to move.
    
    Returns:
        "left", "right", "forward", or None if all blocked
    """
    if not occupancy[1]:  # Center clear
        return "forward"
    elif not occupancy[0]:  # Left clear
        return "left"
    elif not occupancy[2]:  # Right clear
        return "right"
    else:
        return None  # All blocked
