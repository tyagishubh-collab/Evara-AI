"""YOLOv8 object detection for obstacle identification."""
from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Optional

class Detector:
    """YOLO-based obstacle detector."""
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        """Initialize YOLO model."""
        try:
            self.model = YOLO(model_path)
            print(f"✅ YOLO model loaded: {model_path}")
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            self.model = None
    
    def infer(self, frame: np.ndarray, conf_threshold: float = 0.35, imgsz: int = 480) -> List[Dict]:
        """
        Run inference on frame.
        
        Returns:
            List of detections with keys: bbox, cls, conf, label
        """
        if self.model is None or frame is None:
            return []
        
        try:
            results = self.model(frame, imgsz=imgsz, conf=conf_threshold, verbose=False)[0]
            detections = []
            
            for box in results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cls = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                label = results.names.get(cls, f"class_{cls}")
                
                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "cls": cls,
                    "conf": conf,
                    "label": label
                })
            
            return detections
        except Exception as e:
            print(f"⚠️ Detection error: {e}")
            return []
    
    def filter_obstacles(self, detections: List[Dict],
                         obstacle_classes: Optional[List[str]] = None) -> List[Dict]:
        """
        Filter detections to only include obstacles.
        
        Common obstacles: person, car, bicycle, motorcycle, bus, truck,
                         chair, couch, bed, door, stairs, etc.
        """
        if obstacle_classes is None:
            obstacle_classes = [
                "person", "bicycle", "car", "motorcycle", "bus", "truck",
                "chair", "couch", "bed", "door", "stairs"
            ]
        
        return [d for d in detections if d["label"] in obstacle_classes]
