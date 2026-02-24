"""
Face Recognizer
Recognizes faces using face_recognition library (dlib-based)
"""

import face_recognition
import numpy as np
import pickle
from pathlib import Path
from typing import Optional, List, Tuple

class FaceRecognizer:
    """Face recognition and comparision using face_recognition library"""

    def __init__(self, encodings_path: str = "models/face_encodings.pkl", tolerance: float = 0.6, model: str = "large"):
        """
        Initialize face recognizer
        
        Args:
            encodings_path: Path to saved face encodings
            tolerance: Recognition threshold (lower = more strict)
            model: Recognition model ('large' or 'small')
        """
        self.encodings_path = Path(encodings_path)
        self.tolerance = tolerance
        self.model = model
        self.known_encodings: List[np.ndarray] = []
        self.owner_name = "owner"

        # Load encodings if file exists
        if self.encodings_path.exists():
            self.load_encodings()

    def load_encodings(self) -> bool:
        """
        Load face encodings from pickle file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(self.encodings_path, 'rb') as f:
                data = pickle.load(f)
                self.known_encodings = data.get('encodings', [])
                self.owner_name = data.get('name', 'owner')
            return len(self.known_encodings) > 0
        except Exception as e:
            print(f"Error loading encodings: {e}")
            return False
    
    def get_face_encoding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate face encoding from image
        
        Args:
            face_image: Face image (RGB format)
        
        Returns:
            128-dimensional face encoding or None
        """
        try:
            # Detect faces in the image
            face_locations = face_recognition.face_locations(face_image, model=self.model)

            if not face_locations:
                return None
            
            # Get encoding for the first face
            encodings = face_recognition.face_encodings(face_image, face_locations)

            if encodings:
                return encodings[0]
            
            return None
        except Exception as e:
            print(f"Error generating encoding: {e}")
            return None
        
    def recognize(self, face_image: np.ndarray) -> Tuple[bool, float]:
        """
        Recognize if face belongs to owner
        
        Args:
            face_image: Face image (RGB format)
        
        Returns:
            Tuple (is_owner, confidence_distance)
            - is_owner: True if owner recognized
            - confidence_distance: Lower is better (0 = perfect match)
        """
        if not self.known_encodings:
            return False, 1.0
        
        # Get encoding for input face
        face_encoding = self.get_face_encoding(face_image)

        if face_encoding is None:
            return False, 1.0
        
        # Compare against all known encodings
        distances = face_recognition.face_distance(self.known_encodings, face_encoding)

        # Get the best match
        min_distance = float(np.min(distances))
        is_match = min_distance <= self.tolerance

        return is_match, min_distance
    
    def recognize_multiple(self, face_image: np.ndarray) -> List[Tuple[bool, float]]:
        """
        Recognize all faces in image
        
        Args:
            face_image: Image with potentially multiple faces
        
        Returns:
            List of (is_owner, distance) for each face
        """
        if not self.known_encodings:
            return []
        
        # Detect all faces
        face_locations = face_recognition.face_locations(face_image, model=self.model)

        if not face_locations:
            return []
        
        # Get encodings for all faces
        face_encodings = face_recognition.face_encodings(face_image, face_locations)

        results = []
        for encoding in face_encodings:
            distances = face_recognition.face_distance(self.known_encodings, encoding)
            min_distance = float(np.min(distances))
            is_match = min_distance <= self.tolerance
            results.append((is_match, min_distance))

        return results

    def set_tolerance(self, tolerance: float) -> None:
        """Update recognition tolerance threshold"""
        self.tolerance = tolerance

    def is_trained(self) -> bool:
        """Check if model has been trained"""
        return len(self.known_encodings)>0