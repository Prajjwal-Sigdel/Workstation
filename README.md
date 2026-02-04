# Sleep Checker

A face recognition-based system daemon for Linux that monitors user presence before system sleep events. The daemon analyzes webcam input to make intelligent decisions about whether to allow sleep, prevent sleep, or shutdown the system.

## Overview

Sleep Checker intercepts system sleep events and uses facial recognition to determine the appropriate action:

| Detection Result | Action |
|------------------|--------|
| Owner detected | Block sleep (user is present) |
| Unknown person detected | Shutdown system (security measure) |
| No face detected | Allow sleep (user is away) |

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

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/sleep_checker.git
cd sleep_checker
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install ./face_recognition_models
```

### 4. Generate face encodings

Before using the daemon, you need to create face encodings for recognition:

```bash
python phase2_face_training.py
```

Follow the interactive prompts to capture face images and generate the encoding file.

### 5. Install as system service

```bash
# Copy the daemon script
sudo cp phase5_service_daemon.py /usr/local/bin/sleep_checker.py
sudo chmod +x /usr/local/bin/sleep_checker.py

# Create systemd service
sudo tee /etc/systemd/system/sleep-checker.service << 'EOF'
[Unit]
Description=Sleep Checker - Face Recognition Guard
Before=sleep.target suspend.target hibernate.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/sleep_checker.py pre
TimeoutSec=30

[Install]
WantedBy=sleep.target suspend.target hibernate.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable sleep-checker.service
```

## Configuration

The daemon reads configuration from `/etc/sleep_checker/config.json`. If the file does not exist, default values are used.

### Default Configuration

```json
{
    "encoding_file": "/path/to/me_encoding.pkl",
    "log_file": "/path/to/sleep_checker.log",
    "confidence_threshold": 0.4,
    "detection_time": 5,
    "scale_factor": 0.25,
    "enable_shutdown_on_unknown": true,
    "enable_logging": true
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| encoding_file | string | - | Path to the pickle file containing face encodings |
| log_file | string | - | Path to the log file |
| confidence_threshold | float | 0.4 | Face match threshold (lower = stricter matching) |
| detection_time | int | 5 | Duration in seconds to analyze webcam |
| scale_factor | float | 0.25 | Frame resize factor for faster processing |
| enable_shutdown_on_unknown | bool | true | Shutdown when unknown person detected |
| enable_logging | bool | true | Enable file and console logging |

## Usage

### Running as systemd service

Once installed, the service runs automatically when the system attempts to sleep:

```bash
# Check service status
systemctl status sleep-checker.service

# View logs
journalctl -u sleep-checker.service
```

### Manual testing

```bash
# Test face recognition without system actions
sudo /usr/local/bin/sleep_checker.py --test

# Run as pre-sleep hook
sudo /usr/local/bin/sleep_checker.py pre
```

### Command line arguments

| Argument | Description |
|----------|-------------|
| pre | Run as pre-sleep hook (main functionality) |
| post | Post-sleep hook (exits immediately) |
| --test | Test mode - analyze webcam without system actions |

## Project Structure

```
sleep_checker/
├── phase5_service_daemon.py    # Main daemon script
├── phase1_face_detect.py       # Basic face detection testing
├── phase2_face_training.py     # Face image capture and encoding
├── phase3_face_recognition.py  # Real-time recognition testing
├── phase4_system_controller.py # System integration testing
├── requirements.txt            # Python dependencies
├── data/
│   ├── known_faces/            # Training face images
│   ├── me_encoding.pkl         # Generated face encodings
│   └── sleep_checker.log       # Daemon log file
└── face_recognition_models/    # Pre-trained model files
    └── models/
        ├── dlib_face_recognition_resnet_model_v1.dat
        ├── shape_predictor_68_face_landmarks.dat
        └── mmod_human_face_detector.dat
```

## How It Works

1. The daemon is triggered by systemd before sleep/suspend events
2. Webcam captures frames for the configured detection duration
3. Each frame undergoes low-light enhancement and face detection
4. Detected faces are compared against stored face encodings
5. Based on the analysis results, the daemon makes a decision:
   - If owner is detected: exits with code 1 to signal sleep prevention
   - If unknown person is detected: initiates system shutdown
   - If no face is detected: exits with code 0 to allow sleep

## Dependencies

- opencv-python - Computer vision and image processing
- numpy - Numerical computations
- face-recognition - High-level face recognition interface
- face-recognition-models - Pre-trained deep learning models

## Troubleshooting

### Webcam not detected

Ensure the webcam is accessible:

```bash
ls -la /dev/video*
```

### Service not triggering

Verify the service is enabled and linked to sleep targets:

```bash
systemctl show sleep-checker.service --property=WantedBy
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
