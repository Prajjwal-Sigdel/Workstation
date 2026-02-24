"""
Face Trainer
Trains face recognition model for captured images
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple
import os

from src.core.face_detector import FaceDetector
from src.core.face_recognizer import FaceRecognizer
from src.utils.logger import get_logger

class FaceTrainer:
    """Trains face recognition model from image directory"""

    def __init__(self, data_dir: str = "data/known_faces/owner", model_path: str = "models/yunet.onnx", output_path: str = "models/face_encodings.pkl"):
        """
        Initialize face trainer
        
        Args:
            data_dir: Directory containing training images
            model_path: Path to YuNet detection model
            output_path: Path to save trained model
        """
        self.data_dir = Path(data_dir)
        self.output_path = Path(output_path)
        self.logger = get_logger(__name__)

        # Initialize detector and recognizer
        self.detector = FaceDetector(model_path)
        self.recognizer = FaceRecognizer(str(output_path))

        self.face_images: List[np.ndarry] = []

    def load_images(self) -> int:
        """
        Load all images from training directory
        
        Returns:
            Number of images loaded
        """
        if not self.data_dir.exists():
            self.logger.error(f"Training directory not found: {self.data_dir}")
            return 0
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        image_files = []

        for ext in image_extensions:
            image_files.extend(self.data_dir.glob(f'*{ext}'))
            image_files.extend(self.data_dir.glob(f'*{ext.upper()}'))

        self.logger.info(f"Found {len(image_files)} images in {self.data_dir}")

        for img_path in image_files:
            img = cv2.imread(str(img_path))
            if img is not None:
                self.face_images.append(img)
            else:
                self.logger.warning(f"Failed to load: {img_path}")

        return len(self.face_images)
    
    def extract_faces(self) -> List[np.ndarray]:
        """
        Extract face regions from all images
        
        Returns:
            List of cropped face images
        """
        faces = []

        for idx, img in enumerate(self.face_images):
            self.logger.debug(f"Processing image {idx + 1}/{len(self.face_images)}")

            # Detect faces
            detections = self.detector.detect(img)

            if not detections:
                self.logger.warning(f"No face detected in image {idx + 1}")
                continue

            # Get largest face (assume it's the main subject)
            x, y, w, h, conf = max(detections, key=lambda d: d[2] * d[3])

            # Crop face with some padding
            padding = 20
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(img.shape[1], x + w + padding)
            y2 = min(img.shape[0], y + h + padding)

            face_crop = img[y1:y2, x1:x2]

            if face_crop.size > 0:
                faces.append(face_crop)
                self.logger.debug(f"Extracted face: {w}x{h}, confidence: {conf:.2f}")
            else:
                self.logger.warning(f"Invalid face crop in image {idx + 1}")

        self.logger.info(f"Extracted {len(faces)} faces from {len(self.face_images)} images")
        return faces
    
    def train(self) -> bool:
        """
        Train the face recognition model
        
        Returns:
            True if training successful
        """
        self.logger.info("Starting face recognition training...")

        # Load images
        num_images = self.load_images()
        if num_images == 0:
            self.logger.error("No training images found")
            return False
        
        # Extract faces
        faces = self.extract_faces()
        if len(faces) < 5:
            self.logger.error(f"Too few faces extracted ({len(faces)}). Need at least 5")
            return False
        
        # Train recognizer
        self.logger.info(f"Training with {len(faces)} face samples...")
        success = self.recognizer.train(faces)

        if success:
            self.logger.info(f"Training complete! Model saved to {self.output_path}")
            return True
        else:
            self.logger.error("Training failed")
            return False
        
    def get_statistics(self) -> dict:
        """
        Get training statistics
        
        Returns:
            Dictionary with training stats
        """
        return {
            'total_images': len(self.face_images),
            'data_directory': str(self.data_dir),
            'output_path': str(self.output_path),
            'is_trained': self.recognizer.is_trained()
        }

def main():
    """Standalone training script"""
    import argparse

    parser = argparse.ArgumentParser(description='Train face recognition model')
    parser.add_argument(
        '--data-dir',
        default='data/known_faces/owner',
        help='Directory containing training images'
    )
    parser.add_argument(
        '--output',
        default='models/face_encodings.pkl',
        help='Output path for trained model'
    )
    
    args = parser.parse_args()

    # Setup logging
    from src.utils.logger import setup_logger
    logger = setup_logger('face_trainer', 'data/logs/training.log', 'INFO')

    # Create trainer
    trainer = FaceTrainer(
        data_dir=args.data_dir,
        output_path=args.output
    )

    # Train 
    success = trainer.train()

    # Print statistics
    stats = trainer.get_statistics()
    logger.info("Training Statistics:")
    logger.info(f"  Images processed: {stats['total_images']}")
    logger.info(f"  Data directory: {stats['data_directory']}")
    logger.info(f"  Model saved: {stats['output_path']}")
    logger.info(f"  Status: {'SUCCESS' if success else 'FAILED'}")

    return 0 if success else 1

if __name__== '__main__':
    exit(main())