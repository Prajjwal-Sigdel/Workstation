"""
Image Utilities
Helper functions for image preprocessing and enhancement
"""

import cv2
import numpy as np
from typing import Tuple, Optional


def enhance_low_light(image: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
    """
    Enhance image quality in low-light conditions using CLAHE
    
    Args:
        image: Input image (BGR format)
        clip_limit: Contrast limit for CLAHE
    
    Returns:
        Enhanced image
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    
    # Merge channels and convert back to BGR
    lab_enhanced = cv2.merge([l_enhanced, a, b])
    enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
    
    return enhanced


def resize_frame(image: np.ndarray, max_width: int = 640) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio
    
    Args:
        image: Input image
        max_width: Maximum width in pixels
    
    Returns:
        Resized image
    """
    height, width = image.shape[:2]
    
    if width <= max_width:
        return image
    
    # Calculate new dimensions
    ratio = max_width / width
    new_width = max_width
    new_height = int(height * ratio)
    
    # Resize
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return resized


def flip_horizontal(image: np.ndarray) -> np.ndarray:
    """
    Flip image horizontally (mirror effect)
    
    Args:
        image: Input image
    
    Returns:
        Flipped image
    """
    return cv2.flip(image, 1)


def crop_face(image: np.ndarray, bbox: Tuple[int, int, int, int], 
              padding: float = 0.2) -> Optional[np.ndarray]:
    """
    Crop face from image with padding
    
    Args:
        image: Input image
        bbox: Bounding box (x, y, width, height)
        padding: Padding ratio around face (0.2 = 20% padding)
    
    Returns:
        Cropped face image or None if invalid
    """
    x, y, w, h = bbox
    
    # Add padding
    pad_w = int(w * padding)
    pad_h = int(h * padding)
    
    # Calculate crop coordinates
    x1 = max(0, x - pad_w)
    y1 = max(0, y - pad_h)
    x2 = min(image.shape[1], x + w + pad_w)
    y2 = min(image.shape[0], y + h + pad_h)
    
    # Validate coordinates
    if x2 <= x1 or y2 <= y1:
        return None
    
    # Crop
    face_crop = image[y1:y2, x1:x2]
    
    return face_crop


def draw_face_box(image: np.ndarray, bbox: Tuple[int, int, int, int],
                  label: str = "", color: Tuple[int, int, int] = (0, 255, 0),
                  thickness: int = 2) -> np.ndarray:
    """
    Draw bounding box and label on image
    
    Args:
        image: Input image
        bbox: Bounding box (x, y, width, height)
        label: Text label to display
        color: Box color (BGR)
        thickness: Line thickness
    
    Returns:
        Image with drawn box
    """
    x, y, w, h = bbox
    
    # Draw rectangle
    cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness)
    
    # Draw label if provided
    if label:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 2
        
        # Get text size for background
        (text_width, text_height), baseline = cv2.getTextSize(
            label, font, font_scale, font_thickness
        )
        
        # Draw background rectangle
        cv2.rectangle(
            image,
            (x, y - text_height - 10),
            (x + text_width, y),
            color,
            -1  # Filled
        )
        
        # Draw text
        cv2.putText(
            image,
            label,
            (x, y - 5),
            font,
            font_scale,
            (255, 255, 255),  # White text
            font_thickness
        )
    
    return image


def normalize_face(face_image: np.ndarray, size: Tuple[int, int] = (128, 128)) -> np.ndarray:
    """
    Normalize face image for recognition
    
    Args:
        face_image: Cropped face image
        size: Target size (width, height)
    
    Returns:
        Normalized face image
    """
    # Resize to standard size
    normalized = cv2.resize(face_image, size, interpolation=cv2.INTER_AREA)
    
    # Convert to RGB (face_recognition expects RGB)
    normalized = cv2.cvtColor(normalized, cv2.COLOR_BGR2RGB)
    
    return normalized

