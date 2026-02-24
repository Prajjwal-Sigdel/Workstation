# Sleep Checker - Complete Build Guide

## Project Folder Structure

```
sleep_checker/
├── README.md                              # Quick overview and installation
├── PROJECT_GUIDE.md                       # This file - complete build guide
├── requirements.txt                       # Python dependencies
├── idea.txt                              # Original problem statement
│
├── docs/                                  # Documentation
│   ├── ARCHITECTURE.md                   # System design and how components work together
│   ├── TROUBLESHOOTING.md                # Common issues and solutions
│   └── KDE_INTEGRATION.md                # KDE-specific idle detection setup
│
├── src/                                   # Main application source code
│   ├── __init__.py                       # Makes src a Python package
│   │
│   ├── core/                             # Core functionality modules
│   │   ├── __init__.py                   # Package initializer
│   │   ├── face_detector.py              # YuNet-based face detection
│   │   ├── face_recognizer.py            # Face recognition and comparison
│   │   ├── face_trainer.py               # Training face encodings from images
│   │   └── system_controller.py          # Inhibit screen dim/sleep/lock
│   │
│   ├── monitors/                         # Different monitoring strategies
│   │   ├── __init__.py                   # Package initializer
│   │   ├── idle_monitor.py               # Listens to KDE idle state via D-Bus
│   │   └── sleep_monitor.py              # Intercepts system sleep events (v1 approach)
│   │
│   ├── utils/                            # Helper utilities
│   │   ├── __init__.py                   # Package initializer
│   │   ├── config_manager.py             # Load/save JSON configuration
│   │   ├── logger.py                     # Structured logging to file and journal
│   │   └── image_utils.py                # Image enhancement for low-light conditions
│   │
│   └── daemon/                           # Systemd service daemon
│       ├── __init__.py                   # Package initializer
│       └── main_service.py               # Main daemon entry point
│
├── examples/                              # Step-by-step learning examples
│   ├── step1_webcam_test.py              # Test webcam access
│   ├── step2_basic_face_detection.py     # Detect any face using YuNet
│   ├── step3_capture_training_data.py    # Capture your face for training
│   ├── step4_train_face_model.py         # Generate face encodings
│   ├── step5_test_recognition.py         # Test face recognition in real-time
│   ├── step6_test_system_inhibitor.py    # Test preventing screen dim/sleep
│   ├── step7_test_idle_detection.py      # Test KDE idle event detection
│   └── step8_full_integration.py         # Test complete system before service
│
├── models/                                # Machine learning models
│   ├── yunet.onnx                        # YuNet face detection model (download)
│   └── face_encodings.pkl                # Your trained face encodings (generated)
│
├── data/                                  # Training and runtime data
│   ├── known_faces/                      # Training images directory
│   │   ├── owner/                        # Your face images (20-30 photos)
│   │   │   ├── photo_001.jpg
│   │   │   ├── photo_002.jpg
│   │   │   └── ...
│   │   └── .gitkeep
│   └── logs/                             # Application logs
│       ├── sleep_checker.log             # Main log file
│       └── .gitkeep
│
├── config/                                # Configuration files
│   ├── default_config.json               # Default configuration (committed to git)
│   └── user_config.json                  # User overrides (gitignored, optional)
│
├── scripts/                               # Helper scripts
│   ├── download_model.sh                 # Download YuNet model
│   ├── capture_faces.sh                  # Helper to capture training photos
│   ├── install_service.sh                # Install systemd service
│   ├── uninstall_service.sh              # Remove systemd service
│   └── test_camera.sh                    # Quick camera test
│
├── service/                               # Systemd integration
│   └── sleep-checker.service             # Systemd user service unit file
│
├── tests/                                 # Unit tests (optional, for future)
│   ├── __init__.py
│   ├── test_face_detector.py
│   └── test_config_manager.py
│
├── .gitignore                            # Git ignore file
└── venv/                                 # Python virtual environment (gitignored)
```

---

## Problem Statement

When studying or writing in front of the screen, after some inactivity, the PC automatically:
- Dims the screen
- Locks the screen
- Goes to sleep mode

**This interrupts work even when you're actively reading or thinking.**

---

## Solution Overview

A user-space service that:
1. **Monitors KDE idle events using D-Bus**
   - Connects to KDE's `org.freedesktop.ScreenSaver` D-Bus interface
   - Listens for `ActiveChanged` signal when user becomes idle
   - No polling required - event-driven approach
2. **When idle threshold is reached**, captures webcam image
3. **Runs face detection and recognition**
4. **Takes action based on detection**:
   - **User recognized** → Inhibit screen dim/lock/sleep via D-Bus (keep PC active)
   - **No face detected** → Allow normal behavior (dim/sleep)
   - **Unknown person detected** → Shutdown PC (security measure)

### Why D-Bus?

D-Bus (Desktop Bus) is the standard inter-process communication (IPC) system on Linux desktops:
- **Event-driven**: No need to constantly poll - KDE sends signals automatically
- **Low overhead**: Minimal CPU usage waiting for events
- **Standard protocol**: Works with KDE, GNOME, and other desktop environments
- **Bidirectional**: Can both listen to events and control system behavior

**Two D-Bus interfaces used:**
1. **`org.freedesktop.ScreenSaver`** - Receive idle state changes from KDE
2. **`org.freedesktop.PowerManagement.Inhibit`** - Prevent screen dim/lock/sleep

---

## Step-by-Step Build Guide

### Phase 0: Project Setup

#### Step 0.1: Create Project Directory
```bash
mkdir -p ~/Documents/Repo/sleep_checker
cd ~/Documents/Repo/sleep_checker
```

#### Step 0.2: Create Folder Structure
```bash
# Create all directories
mkdir -p src/{core,monitors,utils,daemon}
mkdir -p examples
mkdir -p models
mkdir -p data/{known_faces/owner,logs}
mkdir -p config
mkdir -p scripts
mkdir -p service
mkdir -p docs
mkdir -p tests

# Create __init__.py files to make them Python packages
touch src/__init__.py
touch src/core/__init__.py
touch src/monitors/__init__.py
touch src/utils/__init__.py
touch src/daemon/__init__.py
touch tests/__init__.py

# Create placeholder files
touch data/known_faces/.gitkeep
touch data/logs/.gitkeep
```

#### Step 0.3: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 0.4: Create requirements.txt
**File:** `requirements.txt`
```
opencv-python>=4.8.0
numpy>=1.24.0
face-recognition>=1.3.0
dbus-next>=0.2.3
```

Install dependencies:
```bash
pip install -r requirements.txt
```

#### Step 0.5: Create .gitignore
**File:** `.gitignore`
```
# Virtual environment
venv/
env/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg-info/
dist/
build/

# Data files
models/*.pkl
data/known_faces/**/*.jpg
data/known_faces/**/*.png
data/logs/*.log

# User configuration
config/user_config.json

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

### Phase 1: Download Required Models

#### Step 1.1: Create Model Download Script
**File:** `scripts/download_model.sh`

**Purpose:** Downloads the YuNet face detection model from OpenCV's repository.

**What it does:**
- Downloads `yunet.onnx` (lightweight face detection model)
- Places it in the `models/` directory
- Verifies the download

**Usage:**
```bash
chmod +x scripts/download_model.sh
./scripts/download_model.sh
```

#### Step 1.2: Verify Model Downloaded
```bash
ls -lh models/yunet.onnx
# Should show ~227KB file
```

---

### Phase 2: Configuration Setup

#### Step 2.1: Create Default Configuration
**File:** `config/default_config.json`

**Purpose:** Stores all system settings in one place.

**What it contains:**
- Camera settings (device index, resolution)
- Face detection thresholds
- Recognition confidence levels
- Idle timeout settings
- System behavior settings (inhibit/shutdown)
- Logging configuration

**Structure:**
```json
{
  "camera": {
    "device_index": 0,
    "width": 640,
    "height": 480,
    "warmup_time": 0.5
  },
  "detection": {
    "score_threshold": 0.5,
    "recognition_threshold": 0.6
  },
  "idle": {
    "check_interval": 5,
    "kde_idle_timeout": 300
  },
  "actions": {
    "unknown_person_action": "shutdown",
    "inhibit_on_owner": true
  },
  "logging": {
    "level": "INFO",
    "file": "data/logs/sleep_checker.log"
  }
}
```

#### Step 2.2: Create User Config Template
**File:** `config/user_config.json.example`

**Purpose:** Shows users how to override default settings.

**Usage:** Users copy this to `user_config.json` and modify values.

---

### Phase 3: Utility Modules

#### Step 3.1: Configuration Manager
**File:** `src/utils/config_manager.py`

**Purpose:** Loads and merges configuration from JSON files.

**Key functions:**
- `load_config()` - Loads default config, merges with user config
- `get(key, default)` - Gets configuration value
- `save_user_config()` - Saves user preferences

#### Step 3.2: Logger Setup
**File:** `src/utils/logger.py`

**Purpose:** Provides structured logging to file and systemd journal.

**Key functions:**
- `setup_logger(name, log_file)` - Initializes logger
- Logs to both file and console
- Rotates log files automatically
- Integrates with systemd journal

#### Step 3.3: Image Utilities
**File:** `src/utils/image_utils.py`

**Purpose:** Image preprocessing and enhancement.

**Key functions:**
- `enhance_low_light(image)` - Improves dark images
- `resize_frame(image, max_width)` - Resizes for performance
- `flip_horizontal(image)` - Mirror webcam feed

---

### Phase 4: Core Modules

#### Step 4.1: Face Detector
**File:** `src/core/face_detector.py`

**Purpose:** Detects faces in webcam frames using YuNet model.

**Key class:** `FaceDetector`

**Key methods:**
- `__init__(model_path)` - Loads YuNet model
- `detect(frame)` - Returns bounding boxes of detected faces
- `set_score_threshold(value)` - Adjusts detection sensitivity

**How it works:**
1. Loads ONNX model using OpenCV's FaceDetectorYN
2. Takes input frame
3. Returns list of face coordinates and confidence scores
4. Fast and lightweight (runs on CPU efficiently)

#### Step 4.2: Face Recognizer
**File:** `src/core/face_recognizer.py`

**Purpose:** Recognizes if detected face matches the owner.

**Key class:** `FaceRecognizer`

**Key methods:**
- `__init__(encodings_path)` - Loads trained face encodings
- `load_encodings()` - Loads from .pkl file
- `recognize(face_image)` - Compares face against known faces
- `get_face_encoding(face_image)` - Generates encoding from face crop

**How it works:**
1. Uses face_recognition library (dlib-based)
2. Compares face encodings using Euclidean distance
3. Returns True if distance < threshold (owner recognized)

#### Step 4.3: Face Trainer
**File:** `src/core/face_trainer.py`

**Purpose:** Generates face encodings from training images.

**Key class:** `FaceTrainer`

**Key methods:**
- `__init__(data_dir)` - Sets training data directory
- `train()` - Processes all images, generates encodings
- `save_encodings(output_path)` - Saves to .pkl file

**How it works:**
1. Scans `data/known_faces/owner/` directory
2. For each image, detects face and generates encoding
3. Averages multiple encodings for robustness
4. Saves to `models/face_encodings.pkl`

#### Step 4.4: System Controller
**File:** `src/core/system_controller.py`

**Purpose:** Controls system behavior (inhibit sleep, shutdown) using D-Bus.

**Key class:** `SystemController`

**Key methods:**
- `inhibit_idle()` - Prevents screen dim/lock/sleep
- `uninhibit_idle()` - Releases inhibitor lock
- `shutdown_system()` - Initiates system shutdown
- `is_inhibited()` - Checks current inhibitor status

**How it works via D-Bus:**
1. Connects to session D-Bus
2. Calls `Inhibit()` method on `org.freedesktop.PowerManagement.Inhibit`
3. Receives **inhibitor cookie** (unique ID)
4. Holds cookie while user is detected
5. Calls `UnInhibit(cookie)` when releasing

**D-Bus Details:**
- **Service:** `org.freedesktop.PowerManagement.Inhibit`
- **Object Path:** `/org/freedesktop/PowerManagement/Inhibit`
- **Interface:** `org.freedesktop.PowerManagement.Inhibit`
- **Methods:**
  - `Inhibit(application_name, reason)` → Returns uint32 cookie
  - `UnInhibit(cookie)` → Releases inhibitor
  - `HasInhibit()` → Returns boolean
  - `ListInhibitors()` → Returns array of active inhibitors

**Example D-Bus Call:**
```bash
# Manually inhibit (for testing)
dbus-send --session --print-reply \
  --dest=org.freedesktop.PowerManagement.Inhibit \
  /org/freedesktop/PowerManagement/Inhibit \
  org.freedesktop.PowerManagement.Inhibit.Inhibit \
  string:"SleepChecker" string:"User is present"

# List active inhibitors
busctl --user call org.freedesktop.PowerManagement.Inhibit \
  /org/freedesktop/PowerManagement/Inhibit \
  org.freedesktop.PowerManagement.Inhibit ListInhibitors
```

**What gets inhibited:**
- Screen dimming
- Screen lock (screensaver)
- System suspend/sleep
- Automatic hibernation

---

### Phase 5: Monitor Modules

#### Step 5.1: Idle Monitor
**File:** `src/monitors/idle_monitor.py`

**Purpose:** Listens to KDE idle state changes via D-Bus.

**Key class:** `IdleMonitor`

**Key methods:**
- `__init__(callback)` - Sets up D-Bus listener
- `start()` - Begins monitoring idle events
- `on_idle_changed(is_idle)` - Callback when idle state changes

**How it works:**
1. Connects to **session D-Bus** (user-specific bus, not system bus)
2. Subscribes to `org.freedesktop.ScreenSaver` interface
3. Listens for `ActiveChanged` signal
4. When idle threshold reached → triggers face detection
5. Signal carries boolean: `True` = idle, `False` = active

**D-Bus Details:**
- **Service Name:** `org.freedesktop.ScreenSaver`
- **Object Path:** `/org/freedesktop/ScreenSaver` or `/ScreenSaver`
- **Interface:** `org.freedesktop.ScreenSaver`
- **Signal:** `ActiveChanged(boolean is_idle)`
- **Connection Type:** Session bus (not system bus)

**KDE Integration:**
KDE's Power Management service emits this signal based on:
- Mouse/keyboard inactivity timeout (configured in System Settings)
- No video playback or audio
- No application holding inhibitor lock

**Testing D-Bus Connection:**
```bash
# Monitor the signal in real-time
dbus-monitor --session "type='signal',interface='org.freedesktop.ScreenSaver'"

# Check if ScreenSaver service is available
dbus-send --session --print-reply \
  --dest=org.freedesktop.ScreenSaver \
  /org/freedesktop/ScreenSaver \
  org.freedesktop.DBus.Introspectable.Introspect
```

#### Step 5.2: Sleep Monitor (Alternative)
**File:** `src/monitors/sleep_monitor.py`

**Purpose:** Intercepts system sleep events (older approach).

**Key class:** `SleepMonitor`

**How it works:**
1. Systemd service runs before sleep.target
2. On sleep attempt, triggers face detection
3. If owner present, blocks sleep
4. If no one present, allows sleep

---

### Phase 6: Main Daemon

#### Step 6.1: Main Service
**File:** `src/daemon/main_service.py`

**Purpose:** Main entry point that orchestrates all components.

**Key class:** `SleepCheckerDaemon`

**Key methods:**
- `__init__()` - Initializes all components
- `run()` - Main event loop
- `handle_idle_event()` - Called when system goes idle
- `check_user_presence()` - Captures webcam, runs detection/recognition
- `take_action(result)` - Takes appropriate action based on detection

**Flow:**
1. Loads configuration
2. Initializes face detector, recognizer, system controller
3. Starts idle monitor
4. When idle event received:
   - Captures webcam frame
   - Detects faces
   - If face found, recognizes it
   - Takes action (inhibit/allow/shutdown)
5. Logs all actions

---

### Phase 7: Example Scripts (Learning Path)

#### Step 7.1: Webcam Test
**File:** `examples/step1_webcam_test.py`

**Purpose:** Verify webcam is accessible and working.

**What it does:**
- Opens camera device
- Displays live feed
- Tests resolution settings
- Checks FPS

**Run:**
```bash
python examples/step1_webcam_test.py
```

#### Step 7.2: Basic Face Detection
**File:** `examples/step2_basic_face_detection.py`

**Purpose:** Test YuNet face detection on webcam feed.

**What it does:**
- Loads YuNet model
- Detects faces in real-time
- Draws bounding boxes
- Shows confidence scores

#### Step 7.3: Capture Training Data
**File:** `examples/step3_capture_training_data.py`

**Purpose:** Capture your face photos for training.

**What it does:**
- Opens webcam
- Captures 20-30 images of your face
- Saves to `data/known_faces/owner/`
- Various angles and lighting

**Instructions:**
1. Run the script
2. Position face in different angles
3. Press SPACE to capture
4. Capture 20-30 photos
5. Press Q to quit

#### Step 7.4: Train Face Model
**File:** `examples/step4_train_face_model.py`

**Purpose:** Generate face encodings from captured photos.

**What it does:**
- Loads images from `data/known_faces/owner/`
- Detects face in each image
- Generates face encoding
- Saves to `models/face_encodings.pkl`

#### Step 7.5: Test Recognition
**File:** `examples/step5_test_recognition.py`

**Purpose:** Test face recognition in real-time.

**What it does:**
- Loads trained encodings
- Opens webcam
- Recognizes your face
- Shows "OWNER" or "UNKNOWN"

#### Step 7.6: Test System Inhibitor
**File:** `examples/step6_test_system_inhibitor.py`

**Purpose:** Test preventing screen dim/lock.

**What it does:**
- Calls D-Bus Inhibit method
- Holds lock for 60 seconds
- Releases lock
- Verify screen doesn't dim

#### Step 7.7: Test Idle Detection
**File:** `examples/step7_test_idle_detection.py`

**Purpose:** Test KDE idle event detection via D-Bus.

**What it does:**
- Connects to D-Bus ScreenSaver
- Listens for idle events
- Prints when idle/active
- Verify timeout matches KDE settings

**D-Bus Testing Commands:**
```bash
# Check if ScreenSaver service exists
qdbus org.freedesktop.ScreenSaver /ScreenSaver

# Or using busctl
busctl --user tree org.freedesktop.ScreenSaver

# Monitor signals in real-time
dbus-monitor --session "type='signal',interface='org.freedesktop.ScreenSaver'"

# Manually trigger idle (some systems)
qdbus org.freedesktop.ScreenSaver /ScreenSaver SetActive true
```

#### Step 7.8: Full Integration Test
**File:** `examples/step8_full_integration.py`

**Purpose:** Test complete system before installing as service.

**What it does:**
- Combines all components
- Monitors idle
- Runs face detection/recognition
- Takes actions
- Logs everything

**Run for 10-15 minutes and verify:**
- Idle detection works
- Face recognition accurate
- Inhibitor prevents screen dim
- Logs are clear

---

### Phase 8: Systemd Service Installation

#### Step 8.1: Create Service Unit File
**File:** `service/sleep-checker.service`

**Purpose:** Defines systemd user service.

**Content:**
```ini
[Unit]
Description=Sleep Checker - Intelligent Idle Monitor
After=graphical-session.target

[Service]
Type=simple
ExecStart=/home/YOUR_USERNAME/Documents/Repo/sleep_checker/venv/bin/python \
          /home/YOUR_USERNAME/Documents/Repo/sleep_checker/src/daemon/main_service.py
Restart=on-failure
RestartSec=5
Environment="DISPLAY=:0"
Environment="DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus"

[Install]
WantedBy=default.target
```

**Key points:**
- **Type=simple**: Long-running service
- **Restart=on-failure**: Auto-restart on crash
- **Environment**: Needed for GUI and D-Bus access
- **WantedBy=default.target**: Starts on login

#### Step 8.2: Create Install Script
**File:** `scripts/install_service.sh`

**Purpose:** Automates service installation.

**What it does:**
1. Replaces YOUR_USERNAME with actual username
2. Copies service file to `~/.config/systemd/user/`
3. Reloads systemd daemon
4. Enables service (auto-start on login)
5. Starts service immediately

**Run:**
```bash
chmod +x scripts/install_service.sh
./scripts/install_service.sh
```

#### Step 8.3: Create Uninstall Script
**File:** `scripts/uninstall_service.sh`

**Purpose:** Removes the service.

**What it does:**
1. Stops the service
2. Disables auto-start
3. Removes service file
4. Reloads systemd daemon

---

### Phase 9: Testing and Verification

#### Step 9.1: Check Service Status
```bash
systemctl --user status sleep-checker.service
```

Should show:
- Active: active (running)
- Process ID
- Recent log entries

#### Step 9.2: View Logs
```bash
# Journal logs
journalctl --user -u sleep-checker.service -f

# File logs
tail -f data/logs/sleep_checker.log
```

#### Step 9.3: Test Scenarios

**Test 1: Normal Operation**
1. Let system sit idle for 5 minutes
2. Watch logs - should trigger face detection
3. If you're present, screen shouldn't dim
4. Move away, screen should dim/lock

**Test 2: Unknown Person**
1. Have someone else sit in front of camera
2. Wait for idle timeout
3. System should shutdown (test carefully!)

**Test 3: No Camera Access**
1. Cover camera or disconnect
2. System should log error but not crash
3. Should fall back to allowing normal sleep

#### Step 9.4: Performance Monitoring
```bash
# CPU usage
top -p $(pgrep -f main_service.py)

# Memory usage
ps aux | grep main_service.py
```

Should use:
- CPU: <5% when idle, <20% during face detection
- Memory: <200MB

---

### Phase 10: Configuration and Tuning

#### Step 10.1: Adjust Detection Threshold
Edit `config/user_config.json`:
```json
{
  "detection": {
    "score_threshold": 0.4  // Lower = more sensitive (more false positives)
  }
}
```

Restart service:
```bash
systemctl --user restart sleep-checker.service
```

#### Step 10.2: Adjust Recognition Threshold
```json
{
  "detection": {
    "recognition_threshold": 0.5  // Lower = more strict matching
  }
}
```

#### Step 10.3: Change Idle Timeout
**Note:** This is controlled by KDE, not the service.

**Set in KDE System Settings:**
1. System Settings → Power Management → Energy Saving
2. Set "Dim screen" timeout (e.g., 5 minutes)
3. Service will trigger when KDE sends D-Bus signal at this timeout

**Verify KDE Idle Settings:**
```bash
# Check current idle timeout (in milliseconds)
kwriteconfig5 --file powermanagementprofilesrc --group AC --group DimDisplay --key idleTime

# Or check with qdbus
qdbus org.kde.Solid.PowerManagement \
  /org/kde/Solid/PowerManagement \
  org.kde.Solid.PowerManagement.idleTime
```

**KDE → D-Bus → Service Flow:**
```
KDE Timer (5 min) → D-Bus Signal → IdleMonitor → Face Check → Inhibit
     ↓                    ↓              ↓             ↓           ↓
  Inactivity      ActiveChanged(true)  Webcam    Recognition   D-Bus
  Detected         on Session Bus      Capture    Process      Inhibit()
```

#### Step 10.4: Retrain Face Model
If recognition accuracy is poor:
```bash
# Capture more photos (different lighting, angles)
python examples/step3_capture_training_data.py

# Retrain
python examples/step4_train_face_model.py

# Restart service
systemctl --user restart sleep-checker.service
```

---

## File Descriptions Summary

### Configuration Files
- **requirements.txt**: Python package dependencies
- **config/default_config.json**: Default settings for all components
- **config/user_config.json**: User-specific overrides (gitignored)

### Core Modules (`src/core/`)
- **face_detector.py**: YuNet-based face detection
- **face_recognizer.py**: dlib-based face recognition
- **face_trainer.py**: Generates face encodings from photos
- **system_controller.py**: D-Bus interface for system inhibition

### Monitor Modules (`src/monitors/`)
- **idle_monitor.py**: KDE idle event detection via D-Bus
- **sleep_monitor.py**: Alternative sleep event interception

### Utility Modules (`src/utils/`)
- **config_manager.py**: Configuration loading and merging
- **logger.py**: Structured logging setup
- **image_utils.py**: Image preprocessing helpers

### Daemon (`src/daemon/`)
- **main_service.py**: Main orchestration and event loop

### Examples (`examples/`)
- **step1-8**: Progressive learning scripts to understand each component

### Scripts (`scripts/`)
- **download_model.sh**: Download YuNet model
- **install_service.sh**: Install systemd service
- **uninstall_service.sh**: Remove systemd service
- **capture_faces.sh**: Quick face capture helper

### Service Files (`service/`)
- **sleep-checker.service**: Systemd user service unit file

### Data Directories
- **models/**: ML models (yunet.onnx, face_encodings.pkl)
- **data/known_faces/owner/**: Your training photos
- **data/logs/**: Application logs

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      KDE Desktop Environment                 │
│  (Power Management → Idle Timer → D-Bus Signal)             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ ActiveChanged(true)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Sleep Checker Service                     │
│                   (main_service.py)                          │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ IdleMonitor  │  │ FaceDetector │  │ System       │      │
│  │ (D-Bus)      │→ │ (YuNet)      │→ │ Controller   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                   │                   │            │
│         │                   ↓                   │            │
│         │          ┌──────────────┐            │            │
│         │          │ Face         │            │            │
│         │          │ Recognizer   │            │            │
│         │          │ (dlib)       │            │            │
│         │          └──────────────┘            │            │
│         │                   │                   │            │
│         └───────────────────┴───────────────────┘            │
│                             ↓                                │
│                  ┌─────────────────┐                         │
│                  │ Decision Logic  │                         │
│                  └─────────────────┘                         │
│                             │                                │
└─────────────────────────────┼────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ↓             ↓             ↓
         Owner Found    No Face      Unknown Person
                │             │             │
                ↓             ↓             ↓
         Inhibit Idle   Allow Normal   Shutdown
         (Keep Active)   Sleep/Dim     System
```

---

## Troubleshooting

### Service won't start
```bash
# Check logs
journalctl --user -u sleep-checker.service -n 50

# Common issues:
# - DISPLAY not set: Check Environment in service file
# - Camera busy: Close other apps using webcam
# - Missing model: Run download_model.sh
# - D-Bus not accessible: Check DBUS_SESSION_BUS_ADDRESS
```

### D-Bus Connection Issues

**Problem:** Service can't connect to D-Bus
```bash
# Verify D-Bus session is running
echo $DBUS_SESSION_BUS_ADDRESS
# Should show: unix:path=/run/user/1000/bus (or similar)

# Check if ScreenSaver service is available
qdbus --session org.freedesktop.ScreenSaver
# Should list available methods

# Test D-Bus from Python
python3 -c "from dbus_next.aio import MessageBus; import asyncio; asyncio.run(MessageBus().connect())"
# Should complete without errors
```

**Solution:** Ensure service file has correct environment:
```ini
Environment="DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus"
```

**Problem:** Idle signal not received
```bash
# Monitor D-Bus for signals
dbus-monitor --session "type='signal',interface='org.freedesktop.ScreenSaver'"
# Wait for idle timeout, should see ActiveChanged signal

# Check KDE idle settings
systemsettings5  # Navigate to Power Management
```

**Problem:** Inhibitor not working
```bash
# Check if inhibitor is registered
busctl --user call org.freedesktop.PowerManagement.Inhibit \
  /org/freedesktop/PowerManagement/Inhibit \
  org.freedesktop.PowerManagement.Inhibit ListInhibitors

# Should show sleep-checker with "User present" reason

# Manually test inhibitor
dbus-send --session --print-reply \
  --dest=org.freedesktop.PowerManagement.Inhibit \
  /org/freedesktop/PowerManagement/Inhibit \
  org.freedesktop.PowerManagement.Inhibit.Inhibit \
  string:"Test" string:"Testing inhibitor"
# Returns cookie number - screen shouldn't dim now
```

### Face not recognized
```bash
# Retrain with more photos
python examples/step3_capture_training_data.py  # Capture 30+ photos
python examples/step4_train_face_model.py       # Retrain
systemctl --user restart sleep-checker.service
```

### Screen still dims
```bash
# Check if inhibitor is active
busctl --user call org.freedesktop.PowerManagement.Inhibit \
  /org/freedesktop/PowerManagement/Inhibit \
  org.freedesktop.PowerManagement.Inhibit ListInhibitors

# Should show sleep-checker with reason "User present"
```

### High CPU usage
```bash
# Adjust check interval in config
{
  "idle": {
    "check_interval": 10  // Increase to reduce CPU
  }
}
```

---

## Next Steps

1. **Complete Phase 0-2**: Setup project and download models
2. **Run examples sequentially**: Understand each component
3. **Capture and train**: Get good training data
4. **Test integration**: Run step8 before installing service
5. **Install service**: Use install script
6. **Monitor and tune**: Adjust thresholds based on accuracy

---

## Additional Resources

- **OpenCV YuNet**: https://github.com/opencv/opencv_zoo/tree/master/models/face_detection_yunet
- **face_recognition library**: https://github.com/ageitgey/face_recognition
- **D-Bus Python**: https://python-dbus-next.readthedocs.io/
- **systemd user services**: https://wiki.archlinux.org/title/Systemd/User

---

## License

MIT License - Feel free to modify and distribute.

## Contributing

This is a personal learning project, but suggestions and improvements are welcome!
