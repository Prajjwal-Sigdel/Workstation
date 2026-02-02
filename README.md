# Sleep Checker v1.0

**Intelligent Sleep Prevention System for Linux**

A computer vision-based system that prevents unwanted sleep interruptions during reading sessions by monitoring user presence through facial recognition.

## Table of Contents
- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Development Phases](#development-phases)
- [Performance](#performance)
- [Future Enhancements](#future-enhancements)
- [References](#references)
- [License](#license)

## Problem Statement

When reading ebooks on Linux systems, automatic sleep/suspend functionality interrupts reading sessions during periods of keyboard/mouse inactivity. This creates a frustrating experience where users must manually wake their systems to continue reading.

## Solution Overview

Sleep Checker is an intelligent monitoring system that uses computer vision and facial recognition to analyze user presence before system sleep events. The system makes smart decisions based on who (if anyone) is detected:

- **My face detected** → Reset sleep timer (stay awake for continued reading)
- **Unknown person detected** → Shutdown system (security measure)
- **No face detected** → Allow normal sleep (user is away)

## Technologies Used

### Computer Vision
- **OpenCV 4.x** - Traditional face detection using Haar cascades
- **dlib** - Advanced facial recognition with deep learning models
- **NumPy** - Numerical computations for image processing

### Deep Learning Models
- **ResNet Architecture** - Face recognition embeddings (`dlib_face_recognition_resnet_model_v1.dat`)
- **Landmark Detection** - 68-point and 5-point facial landmark predictors
- **CNN Face Detection** - Modern face detection using convolutional neural networks

### Python Libraries
- **face_recognition** - High-level interface for face recognition tasks
- **pickle** - Serialization of face encoding data
- **cv2** - OpenCV Python bindings
- **time** - Performance monitoring and timing controls

### Development Environment
- **Python 3.14+** - Core programming language
- **Virtual Environment (venv)** - Isolated dependency management
- **Git** - Version control with privacy-focused .gitignore configurations

## Project Structure

```
sleep_checker/
├── phase1_face_detect.py      # Traditional face detection (Haar cascades)
├── phase2_face_training.py    # Face data collection and encoding generation
├── phase3_face_recognition.py # Real-time face recognition system
├── data/
│   ├── known_faces/          # Training face images (29+ samples)
│   │   ├── me_0.jpg ... me_28.jpg
│   │   └── .gitignore        # Privacy protection for personal images
│   ├── me_encoding.pkl       # Serialized 128D face embeddings
│   └── .gitignore            # Protection for generated data
├── face_recognition_models/  # Self-contained model package
│   ├── face_recognition_models/
│   │   ├── __init__.py       # Model path definitions
│   │   └── models/           # Pre-trained model files (~100MB)
│   │       ├── dlib_face_recognition_resnet_model_v1.dat
│   │       ├── shape_predictor_68_face_landmarks.dat
│   │       ├── shape_predictor_5_face_landmarks.dat
│   │       └── mmod_human_face_detector.dat
│   ├── setup.py              # Package installation configuration
│   └── .gitignore            # Excludes large model files from Git
├── requirements.txt          # Python dependencies
├── .gitignore               # Main project Git exclusions
├── README.md                # Project documentation
└── venv/                    # Python virtual environment
```

## Installation

### Prerequisites
- Python 3.8+ (developed with Python 3.14)
- Webcam/camera device
- Linux operating system
- Git (for cloning)

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd sleep_checker
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install custom face recognition models:**
   ```bash
   pip install ./face_recognition_models
   ```

5. **Verify installation:**
   ```bash
   python phase1_face_detect.py
   ```

## Usage

### Phase 1: Basic Face Detection
Test traditional computer vision face detection:
```bash
python phase1_face_detect.py
```
- **Controls:** 'q' to quit, SPACE for manual testing
- **Purpose:** Verify camera functionality and basic detection

### Phase 2: Face Training System
Collect personal face data and generate encodings:
```bash
python phase2_face_training.py
```
- **Interactive workflow:** Choose to capture new images and/or encode existing ones
- **Capture controls:** 's' to save face images, 'q' to finish
- **Output:** Generates `data/me_encoding.pkl` with your face embeddings

### Phase 3: Real-Time Recognition
Live face recognition and classification:
```bash
python phase3_face_recognition.py
```
- **Controls:** 'q' to quit, SPACE for detailed recognition results
- **Visual feedback:** Green=You, Red=Unknown person, Yellow=No face
- **Purpose:** Production-ready recognition system

## How It Works

### 1. Face Detection Pipeline
- **Haar Cascade Classifiers** detect face regions in real-time video
- **Optimized parameters** balance speed and accuracy
- **Region of Interest** extraction for further processing

### 2. Face Recognition Process
- **ResNet-based CNN** generates 128-dimensional face embeddings
- **Euclidean distance comparison** against stored personal embeddings
- **Confidence thresholding** determines identity classification

### 3. Decision Logic
```python
if face_detected and distance < threshold:
    classification = "ME" → Action: Stay awake
elif face_detected and distance >= threshold:
    classification = "UNKNOWN" → Action: Shutdown
else:
    classification = "NO_FACE" → Action: Allow sleep
```

## Development Phases

### Phase 1: Traditional Computer Vision ✅ **COMPLETED**
- **Technology:** OpenCV Haar cascade classifiers
- **Purpose:** Proof-of-concept face detection
- **Learning:** Understanding computer vision fundamentals
- **Performance:** ~30 FPS on 640x480 resolution

### Phase 2: Personal Face Training ✅ **COMPLETED**
- **Technology:** Deep learning face recognition (dlib/ResNet)
- **Process:** Interactive image capture → Encoding generation
- **Dataset:** 29+ personal face images with varied lighting/angles
- **Output:** 128-dimensional face embeddings for comparison

### Phase 3: Real-Time Recognition ✅ **COMPLETED**
- **Technology:** Live video processing with cached recognition
- **Performance:** Optimized to process every 5th frame
- **Features:** Visual feedback, confidence scoring, FPS monitoring
- **Status:** Production-ready recognition system

## Performance

### Optimization Techniques
- **Frame rate optimization:** Process every 5th frame for 5x speed improvement
- **Resolution scaling:** 0.25x scale factor for faster face detection
- **Result caching:** Smooth visual feedback between processing frames
- **Webcam configuration:** Limited to 640x480@30fps for consistent performance

### Measured Performance
- **Face Detection:** ~25-30 FPS (Phase 1)
- **Face Recognition:** ~6 FPS effective processing (Phase 3)
- **Model Loading:** ~2-3 seconds startup time
- **Memory Usage:** ~200MB including loaded models

### Recognition Accuracy
- **Confidence Threshold:** 0.6 (balance between security and usability)
- **False Positive Rate:** Low (tested with multiple unknown individuals)
- **False Negative Rate:** Minimal (robust to lighting changes and angles)

## Future Enhancements

### Phase 4: System Integration (Planned)
- Integration with Linux power management (systemd)
- Automatic execution before sleep/suspend events
- System action implementation (prevent sleep/shutdown)

### Phase 5: Production Service (Planned)
- Background daemon service
- Configuration file support
- Logging and monitoring
- Auto-start on boot

### Advanced Features (Future)
- **Multi-user support:** Multiple authorized face profiles
- **Adaptive learning:** Automatic model improvement over time
- **Activity detection:** Distinguish between active reading and sleeping
- **Remote notifications:** Email/SMS alerts for security events
- **Privacy controls:** Scheduled disable periods

## References

### Research Papers
- **Deep Face Recognition:** Schroff, Florian, et al. "FaceNet: A unified embedding for face recognition and clustering." CVPR 2015.
- **ResNet Architecture:** He, Kaiming, et al. "Deep residual learning for image recognition." CVPR 2016.

### Libraries and Frameworks
- **OpenCV:** Bradski, Gary. "The OpenCV library." Dr. Dobb's journal 25.11 (2000): 120-125.
- **dlib:** King, Davis E. "Dlib-ml: A machine learning toolkit." JMLR 10 (2009): 1755-1758.
- **face_recognition:** Geitgey, Adam. "face_recognition library" - https://github.com/ageitgey/face_recognition

### Model Sources
- **dlib models:** https://github.com/davisking/dlib-models
- **Haar cascades:** Viola, Paul, and Michael Jones. "Rapid object detection using a boosted cascade of simple features." CVPR 2001.

### Educational Resources
- **Computer Vision:** Szeliski, Richard. "Computer vision: algorithms and applications." Springer 2010.
- **Deep Learning:** Goodfellow, Ian, et al. "Deep learning." MIT Press 2016.

## License

This project is developed for educational purposes. Model files and libraries maintain their respective licenses:
- **dlib models:** Boost Software License
- **OpenCV:** Apache 2.0 License
- **face_recognition library:** MIT License

---

**Note:** This system processes personal biometric data (face images). Ensure compliance with local privacy laws and regulations. All face data is stored locally and not transmitted to external services.

**First Project Achievement:** This represents a complete computer vision pipeline from basic detection to production-ready recognition, demonstrating proficiency in OpenCV, deep learning, Python development, and system integration concepts.