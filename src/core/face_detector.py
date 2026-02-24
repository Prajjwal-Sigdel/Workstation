"""
Face Dectector using YuNet model
Detects faces in images using OpenCV's FaceDetectorYN
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional

class FaceDetector:
    """YuNet-based face detection"""

    def __init__(self, model_path: str = "models/yunet.onnx", score_threshold: float = 0.5, nms_threshold: float = 0.3, top_k: int = 5000):
        """
        Initialize face detector
        
        Args:
            model_path: Path to YuNet ONNX model
            score_threshold: Confidence threshold (0-1)
            nms_threshold: Non-maximum suppression threshold
            top_k: Maximum number of detections to keep
        """
        self.model_path = Path(model_path)
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k

        if not self.model_path.exists():
            raise FileNotFoundError(f"YuNet model not found: {model_path}")
        
        # Initialize detector (will be set in detect() with image size)
        self.detector = None
        self.current_size = None

    def _initialize_detector(self, width: int, height: int) -> None:
        """Initialize or reinitialize detector with image size"""
        if self.detector is None or self.current_size != (width, height):
            self.detector = cv2. FaceDetectorYN.create(
                model=str(self.model_path),
                config="",
                input_size=(width, height),
                score_threshold=self.score_threshold,
                nms_threshold=self.nms_threshold,
                top_k=self.top_k
            )
            self.current_size = (width, height)

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int , float]]:
        """
        Detect faces in frame
        
        Args:
            frame: Input image (BGR format)
        
        Returns:
            List of tuples: (x, y, width, height, confidence)
        """
        if frame is None or frame.size == 0:
            return []
        
        height, width = frame.shape[:2]

        # Initialize detector with frame size
        self._initialize_detector(width, height)

        # Run detection
        _, faces = self.detector.detect(frame)

        if faces is None:
            return []
        
        # Convert to simple format: (x, y, w, h, confidence)
        detections = []
        for face in faces:
            x, y, w, h = face[:4].astype(int)
            confidence = float(face[-1])
            detections.append((x, y, w, h, confidence))

        return detections
    

    def set_score_threshold(self, threshold: float) -> None:
        """Update detections confidence threshold"""
        self.score_threshold = threshold
        if self.detector is not None:
            self.detector.setScoreThreshold(threshold)
    
    def get_largest_face(self, frame: np.ndarray) -> Optional[Tuple[int, int, int , int, float]]:
        """
        Get the largest detected face (usually the person in front)
        
        Args:
            frame: Input image
        
        Returns:
            Tuple (x, y, w, h, confidence) or None if no face found
        """
        detections = self.detect(frame)

        if not detections:
            return None
        
        # Find face with largest area
        largest = max(detections, key=lambda d: d[2] * d[3])
        return largest