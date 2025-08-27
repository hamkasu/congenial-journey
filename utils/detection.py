# utils/detection.py
from ultralytics import YOLO
import cv2
import numpy as np

class CorrosionDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
    
    def detect(self, image_path: str):
        results = self.model(image_path)
        return results[0]  # Return first result
    
    def calculate_corrosion_percentage(self, result):
        if not result.boxes:
            return 0.0
        
        # Get image dimensions
        img = cv2.imread(result.path)
        height, width = img.shape[:2]
        total_pixels = height * width
        
        # Calculate area of all detections
        corrosion_pixels = 0
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            corrosion_pixels += (x2 - x1) * (y2 - y1)
        
        # Return percentage
        return (corrosion_pixels / total_pixels) * 100