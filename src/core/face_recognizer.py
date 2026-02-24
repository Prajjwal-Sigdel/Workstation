"""
Face Recognizer using OpenCV
Recognizes faces using OpenCV's LBPH (Local Binary Patterns Histograms) face recognizer
"""

import cv2
import numpy as np
import pickle
from pathlib import Path
from typing import Optional, Tuple, List


class FaceRecognizer:
    """OpenCV-based face recognition using LBPH algorithm"""
    
    def __init__(
        self,
        encodings_path: str = "models/face_encodings.pkl",
        confidence_threshold: float = 50.0
    ):
        """
        Initialize face recognizer
        
        Args:
            encodings_path: Path to saved face model
            confidence_threshold: Recognition threshold (lower = more strict, 0-100)
                                 Typical values: 40-60 (lower is stricter)
        """
        self.encodings_path = Path(encodings_path)
        self.confidence_threshold = confidence_threshold
        self.owner_name = "owner"
        
        # Create LBPH face recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=1,
            neighbors=8,
            grid_x=8,
            grid_y=8
        )
        
        self.is_model_trained = False
        
        # Load model if exists
        if self.encodings_path.exists():
            self.load_model()
    
    def load_model(self) -> bool:
        """
        Load trained face recognition model
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(self.encodings_path, 'rb') as f:
                data = pickle.load(f)
                
                # Extract model data
                model_data = data.get('model_data')
                self.owner_name = data.get('name', 'owner')
                
                if model_data:
                    # Save to temp file and load (OpenCV requirement)
                    temp_model = self.encodings_path.parent / "temp_model.yml"
                    with open(temp_model, 'wb') as tm:
                        tm.write(model_data)
                    
                    self.recognizer.read(str(temp_model))
                    temp_model.unlink()  # Delete temp file
                    
                    self.is_model_trained = True
                    return True
            
            return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def save_model(self) -> bool:
        """
        Save trained model to pickle file
        
        Returns:
            True if saved successfully
        """
        try:
            # Create directory if needed
            self.encodings_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save model to temp file first
            temp_model = self.encodings_path.parent / "temp_model.yml"
            self.recognizer.write(str(temp_model))
            
            # Read model data
            with open(temp_model, 'rb') as tm:
                model_data = tm.read()
            
            # Save to pickle
            data = {
                'model_data': model_data,
                'name': self.owner_name,
                'threshold': self.confidence_threshold
            }
            
            with open(self.encodings_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Cleanup temp file
            temp_model.unlink()
            
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def train(self, face_images: List[np.ndarray], labels: Optional[List[int]] = None) -> bool:
        """
        Train recognizer with face images
        
        Args:
            face_images: List of face images (grayscale, same size recommended)
            labels: List of labels (all same for owner, e.g., all 1)
        
        Returns:
            True if training successful
        """
        if not face_images:
            print("No face images provided for training")
            return False
        
        # Convert all images to grayscale and resize to standard size
        processed_faces = []
        for img in face_images:
            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Resize to standard size (100x100)
            img = cv2.resize(img, (100, 100))
            processed_faces.append(img)
        
        # Create labels (all same for owner)
        if labels is None:
            labels = [1] * len(processed_faces)  # Label 1 = owner
        
        try:
            # Train the recognizer
            self.recognizer.train(processed_faces, np.array(labels))
            self.is_model_trained = True
            
            # Save the model
            self.save_model()
            
            return True
        except Exception as e:
            print(f"Error training model: {e}")
            return False
    
    def recognize(self, face_image: np.ndarray) -> Tuple[bool, float]:
        """
        Recognize if face belongs to owner
        
        Args:
            face_image: Face image (BGR or grayscale)
        
        Returns:
            Tuple (is_owner, confidence)
            - is_owner: True if owner recognized
            - confidence: Lower is better (0 = perfect match)
        """
        if not self.is_model_trained:
            return False, 100.0
        
        try:
            # Convert to grayscale if needed
            if len(face_image.shape) == 3:
                gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_image
            
            # Resize to standard size
            gray = cv2.resize(gray, (100, 100))
            
            # Predict
            label, confidence = self.recognizer.predict(gray)
            
            # Label 1 = owner, confidence should be below threshold
            is_owner = (label == 1) and (confidence < self.confidence_threshold)
            
            return is_owner, float(confidence)
        
        except Exception as e:
            print(f"Error during recognition: {e}")
            return False, 100.0
    
    def set_threshold(self, threshold: float) -> None:
        """Update recognition confidence threshold"""
        self.confidence_threshold = threshold
    
    def is_trained(self) -> bool:
        """Check if model has been trained"""
        return self.is_model_trained