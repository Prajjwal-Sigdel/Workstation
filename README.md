# Sleep Checker

A face recognition-based system for Linux that monitors user presence and controls system behavior (sleep, screen lock, etc.) based on whether you're at your computer.

## Versions

| Version | Description | Status |
|---------|-------------|--------|
| [v1_sleep_blocker](v1_sleep_blocker/) | Blocks system sleep when you're present | ✅ Working |
| v2_idle_monitor | Prevents screen dim/lock when you're present | 🚧 Coming Soon |

## Overview

Sleep Checker uses facial recognition to determine the appropriate system action:

| Detection Result | Action |
|------------------|--------|
| Owner detected | Block sleep / Keep screen awake |
| Unknown person detected | Shutdown system (security measure) |
| No face detected | Allow sleep / Allow screen lock |

## Features

- Real-time face detection and recognition using deep learning
- Configurable confidence thresholds and detection parameters
- Low-light image enhancement for improved detection
- JSON-based configuration with sensible defaults
- Comprehensive logging to file and systemd journal
- Multiple fallback methods for system commands
- Designed for systemd integration on Linux

## Requirements

- Python 3.8+
- Linux operating system with systemd
- Webcam/camera device
- Wayland or X11 display server

## Quick Start

### 1. Clone and setup

```bash
git clone https://github.com/yourusername/sleep_checker.git
cd sleep_checker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install ./face_recognition_models
```

### 2. Train face recognition

```bash
python v1_sleep_blocker/phase2_face_training.py
```

### 3. Install the service

See [v1_sleep_blocker/README.md](v1_sleep_blocker/README.md) for detailed installation instructions.

## Project Structure

```
sleep_checker/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── venv/                          # Virtual environment (shared)
│
├── v1_sleep_blocker/              # Sleep blocking system
│   ├── README.md                  # v1-specific documentation
│   ├── phase1_face_detect.py      # Basic face detection testing
│   ├── phase2_face_training.py    # Face image capture and encoding
│   ├── phase3_face_recognition.py # Real-time recognition testing
│   ├── phase4_system_controller.py# System integration testing
│   ├── phase5_service_daemon.py   # Main daemon script
│   └── service/
│       └── sleep-checker.service  # Systemd service template
│
├── v2_idle_monitor/               # Idle/screen lock prevention (coming soon)
│
├── data/                          # Shared data
│   ├── known_faces/               # Training face images
│   ├── me_encoding.pkl            # Generated face encodings
│   └── sleep_checker.log          # Daemon log file
│
└── face_recognition_models/       # Pre-trained model files
    └── models/
        ├── dlib_face_recognition_resnet_model_v1.dat
        ├── shape_predictor_68_face_landmarks.dat
        └── mmod_human_face_detector.dat
```

## Configuration

The daemon reads configuration from `/etc/sleep_checker/config.json`. If the file does not exist, default values are used.

```json
{
    "encoding_file": "/path/to/data/me_encoding.pkl",
    "log_file": "/path/to/data/sleep_checker.log",
    "confidence_threshold": 0.4,
    "detection_time": 5,
    "scale_factor": 0.25,
    "enable_shutdown_on_unknown": true,
    "enable_logging": true
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| encoding_file | string | - | Path to the pickle file containing face encodings |
| log_file | string | - | Path to the log file |
| confidence_threshold | float | 0.4 | Face match threshold (lower = stricter matching) |
| detection_time | int | 5 | Duration in seconds to analyze webcam |
| scale_factor | float | 0.25 | Frame resize factor for faster processing |
| enable_shutdown_on_unknown | bool | true | Shutdown when unknown person detected |
| enable_logging | bool | true | Enable file and console logging |

## Dependencies

- opencv-python - Computer vision and image processing
- numpy - Numerical computations
- face-recognition - High-level face recognition interface
- face-recognition-models - Pre-trained deep learning models

## Troubleshooting

### Webcam not detected

```bash
ls -la /dev/video*
```

### Service not triggering

```bash
systemctl show sleep-checker.service --property=RequiredBy
```

### Face not recognized

- Ensure adequate lighting during detection
- Regenerate face encodings with varied lighting conditions
- Adjust the confidence_threshold value

## License

This project is developed for educational purposes. Dependencies maintain their respective licenses:

- dlib models: Boost Software License
- OpenCV: Apache 2.0 License
- face_recognition: MIT License

## Privacy Notice

This system processes biometric data (face images). All data is stored and processed locally. No data is transmitted to external services.
