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
│   │   ├── idle_monitor.py               # Listens to custom KWin D-Bus signal for idle dim
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
│   ├── step7_test_idle_detection.py      # Test KWin idle dim signal detection
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
├── kwin-scripts/                          # KWin scripting for idle dim detection
│   └── sleep-checker-idle/               # KWin script package
│       ├── metadata.json                 # KWin script metadata (id, name, version, api)
│       ├── contents/
│       │   └── code/
│       │       └── main.js               # KWin script: emits D-Bus signal on screen dim
│       └── install.sh                    # Script to install/register KWin script
│
├── scripts/                               # Helper scripts
│   ├── download_model.sh                 # Download YuNet model
│   ├── capture_faces.sh                  # Helper to capture training photos
│   ├── install_service.sh                # Install systemd service
│   ├── uninstall_service.sh              # Remove systemd service
│   ├── install_kwin_script.sh            # Install KWin idle dim script
│   ├── uninstall_kwin_script.sh          # Remove KWin idle dim script
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
1. **Detects when KDE dims the screen due to inactivity using a custom KWin script**
   - A KWin script hooks into the compositor's idle dim event
   - When screen dims, the KWin script emits a custom D-Bus signal
   - The Python service subscribes to this custom signal
   - Purely event-driven - no polling required
2. **When the dim signal fires**, captures webcam image
3. **Runs face detection and recognition**
4. **Takes action based on detection**:
   - **User recognized** → Inhibit screen dim/lock/sleep via D-Bus (keep PC active)
   - **No face detected** → Allow normal behavior (dim/sleep)
   - **Unknown person detected** → Shutdown PC (security measure)

### Why KWin Scripting + D-Bus?

**The Problem with Standard D-Bus Signals on Wayland:**
- `org.freedesktop.ScreenSaver.ActiveChanged` fires only when screensaver activates or screen locks, NOT when screen merely dims
- KDE PowerDevil handles brightness changes internally without reliably emitting D-Bus signals on Wayland
- Standard idle detection APIs (like `org.kde.KIdleTime`) may not be accessible on all Wayland sessions
- Polling-based approaches waste CPU and are not truly event-driven

**The Solution - KWin Script as Event Source:**
- KWin is KDE's window compositor and has full access to screen state changes
- KWin scripts run inside the compositor process and can detect the exact moment the screen dims due to inactivity
- KWin scripts can call `callDBus()` to emit custom D-Bus signals
- This gives us a **reliable, event-driven signal** that fires precisely when the screen dims from inactivity — not from lid close, not from sleep button, only from idle timeout

**Two D-Bus interfaces used:**
1. **`org.sleepchecker.IdleNotifier`** (Custom) - Receive screen dim event from KWin script
2. **`org.freedesktop.PowerManagement.Inhibit`** - Prevent screen dim/lock/sleep

### How KWin Scripting Works

KWin scripts are JavaScript files that run inside KDE's KWin compositor. They have access to:
- **Workspace API** - Window management, virtual desktops, screen state
- **`callDBus()`** - Emit D-Bus signals or call D-Bus methods from inside the compositor
- **Idle/dim events** - React to compositor-level screen changes

**KWin Script Lifecycle:**
1. Script is installed to `~/.local/share/kwin/scripts/`
2. Registered and enabled via `kwriteconfig6` or KDE System Settings
3. Loaded automatically by KWin on login
4. Runs inside KWin process with compositor-level access
5. Persists across sessions until explicitly disabled

**Our Custom Signal Flow:**
```
KDE Idle Timer (configured in Power Management)
    ↓
KWin detects idle → begins screen dim
    ↓
KWin script intercepts dim event
    ↓
callDBus() emits signal on org.sleepchecker.IdleNotifier
    ↓
Python IdleMonitor receives signal
    ↓
Face detection pipeline triggered
```

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
mkdir -p kwin-scripts/sleep-checker-idle/contents/code
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
opencv-contrib-python>=4.8.0
numpy>=1.24.0
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
- Custom D-Bus signal settings (service name, interface, signal name)
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
    "recognition_threshold": 50.0
  },
  "idle": {
    "dbus_service": "org.sleepchecker.IdleNotifier",
    "dbus_path": "/org/sleepchecker/IdleNotifier",
    "dbus_interface": "org.sleepchecker.IdleNotifier",
    "dbus_signal": "ScreenDimmed"
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
- `__init__(encodings_path)` - Loads trained face model
- `load_model()` - Loads LBPH model from .pkl file
- `recognize(face_image)` - Compares face against trained model
- `train(face_images)` - Trains LBPH model with face samples

**How it works:**
1. Uses OpenCV's LBPH (Local Binary Patterns Histograms) face recognizer
2. Compares face patterns against trained model
3. Returns (is_owner, confidence) where lower confidence = better match
4. No external dependencies beyond opencv-contrib-python

#### Step 4.3: Face Trainer
**File:** `src/core/face_trainer.py`

**Purpose:** Generates trained face model from captured images.

**Key class:** `FaceTrainer`

**Key methods:**
- `__init__(data_dir)` - Sets training data directory
- `train()` - Processes all images, trains LBPH model
- Uses FaceDetector internally to extract face regions from images

**How it works:**
1. Scans `data/known_faces/owner/` directory
2. For each image, detects face using YuNet and crops it
3. Trains OpenCV LBPH recognizer with all cropped faces
4. Saves trained model to `models/face_encodings.pkl`

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

**Example D-Bus Call:**
```bash
# Manually inhibit (for testing)
dbus-send --session --print-reply \
  --dest=org.freedesktop.PowerManagement.Inhibit \
  /org/freedesktop/PowerManagement/Inhibit \
  org.freedesktop.PowerManagement.Inhibit.Inhibit \
  string:"SleepChecker" string:"User is present"
```

---

### Phase 5: KWin Script for Idle Dim Detection

#### Why KWin Scripting?

On KDE Wayland, there is no standard D-Bus signal that fires specifically when the screen dims due to user inactivity. Screen dimming is handled internally by the KWin compositor and KDE PowerDevil, without exposing a reliable signal to external applications.

KWin scripts run **inside the compositor process** and have direct access to screen state changes. By writing a small KWin script, we can detect the exact moment the screen dims from inactivity and emit our own custom D-Bus signal that the Python service can subscribe to.

**This gives us:**
- A true event-driven trigger (no polling)
- Fires only on inactivity-based dimming (not lid close or sleep button)
- Works reliably on both X11 and Wayland KDE sessions

#### Step 5.1: KWin Script Metadata
**File:** `kwin-scripts/sleep-checker-idle/metadata.json`

**Purpose:** Defines the KWin script package identity and version.

**What it contains:**
- Script ID (unique identifier for KWin)
- Display name and description
- KWin scripting API version
- Author and version info

#### Step 5.2: KWin Script Main Logic
**File:** `kwin-scripts/sleep-checker-idle/contents/code/main.js`

**Purpose:** The actual KWin script that detects screen dim events and emits a custom D-Bus signal.

**What it does:**
1. Hooks into KWin's screen/compositor idle dim event
2. When screen dims due to inactivity, calls `callDBus()` to emit a signal
3. Emits on the custom D-Bus service `org.sleepchecker.IdleNotifier`
4. Signal name: `ScreenDimmed` with a boolean payload (true = dimmed, false = restored)
5. Also detects when screen brightness is restored (user returned)

**Custom D-Bus Signal Details:**
- **Service:** `org.sleepchecker.IdleNotifier`
- **Object Path:** `/org/sleepchecker/IdleNotifier`
- **Interface:** `org.sleepchecker.IdleNotifier`
- **Signal:** `ScreenDimmed(boolean is_dimmed)`
  - `true` → Screen just dimmed due to inactivity
  - `false` → Screen restored (user activity detected)

**KWin API used:**
- `callDBus(service, path, interface, method, ...)` - Emit D-Bus signal from inside KWin
- Compositor idle/dim hooks available through KWin's scripting workspace API

#### Step 5.3: KWin Script Installation
**File:** `scripts/install_kwin_script.sh`

**Purpose:** Installs and enables the KWin script.

**What it does:**
1. Copies the script package to `~/.local/share/kwin/scripts/sleep-checker-idle/`
2. Registers the script with KWin using `kwriteconfig6`
3. Enables the script in KWin's configuration
4. Reloads KWin scripts using `dbus-send` to `org.kde.KWin` so the script takes effect without logout

**Usage:**
```bash
chmod +x scripts/install_kwin_script.sh
./scripts/install_kwin_script.sh
```

**Verification:**
```bash
# Check if script is installed
ls ~/.local/share/kwin/scripts/sleep-checker-idle/

# Check if script is enabled in KWin config
kreadconfig6 --file kwinrc --group Plugins --key sleep-checker-idleEnabled

# Monitor the custom D-Bus signal
dbus-monitor --session "type='signal',interface='org.sleepchecker.IdleNotifier'"
# Then let screen dim naturally - should see ScreenDimmed signal appear
```

#### Step 5.4: KWin Script Uninstallation
**File:** `scripts/uninstall_kwin_script.sh`

**Purpose:** Removes and disables the KWin script.

**What it does:**
1. Disables the script in KWin configuration
2. Removes the script directory from `~/.local/share/kwin/scripts/`
3. Reloads KWin scripts

---

### Phase 6: Monitor Modules

#### Step 6.1: Idle Monitor
**File:** `src/monitors/idle_monitor.py`

**Purpose:** Listens to the custom KWin D-Bus signal for screen dim events.

**Key class:** `IdleMonitor`

**Key methods:**
- `__init__(callback)` - Sets up D-Bus listener for custom signal
- `start()` - Subscribes to `org.sleepchecker.IdleNotifier.ScreenDimmed` signal
- `stop()` - Disconnects from D-Bus
- `run_forever()` - Main event loop

**How it works:**
1. Connects to **session D-Bus**
2. Adds a message handler that filters for `ScreenDimmed` signal on `org.sleepchecker.IdleNotifier`
3. When signal received with `true` → triggers face detection callback
4. When signal received with `false` → notifies that user is active
5. Purely event-driven - zero polling, zero CPU when idle

**D-Bus Details:**
- **Service Name:** `org.sleepchecker.IdleNotifier`
- **Object Path:** `/org/sleepchecker/IdleNotifier`
- **Interface:** `org.sleepchecker.IdleNotifier`
- **Signal:** `ScreenDimmed(boolean is_dimmed)`
- **Connection Type:** Session bus

**Signal Source:**
The signal originates from the KWin script (`kwin-scripts/sleep-checker-idle/`) which runs inside KDE's compositor. It fires only when:
- ✓ Screen dims due to keyboard/mouse inactivity
- ✗ NOT when lid is closed
- ✗ NOT when sleep button is pressed
- ✗ NOT when user manually adjusts brightness

**Testing the Signal:**
```bash
# Monitor the custom signal
dbus-monitor --session "type='signal',interface='org.sleepchecker.IdleNotifier'"

# Let screen dim naturally due to inactivity
# Should see: ScreenDimmed(true)
# Move mouse
# Should see: ScreenDimmed(false)
```

#### Step 6.2: Sleep Monitor (Alternative)
**File:** `src/monitors/sleep_monitor.py`

**Purpose:** Intercepts system sleep events (older approach, fallback).

**Key class:** `SleepMonitor`

**How it works:**
1. Systemd service runs before sleep.target
2. On sleep attempt, triggers face detection
3. If owner present, blocks sleep
4. If no one present, allows sleep

---

### Phase 7: Main Daemon

#### Step 7.1: Main Service
**File:** `src/daemon/main_service.py`

**Purpose:** Main entry point that orchestrates all components.

**Key class:** `SleepCheckerDaemon`

**Key methods:**
- `__init__()` - Initializes all components
- `run()` - Main event loop
- `handle_idle_event(is_dimmed)` - Called when KWin script emits dim signal
- `check_user_presence()` - Captures webcam, runs detection/recognition
- `take_action(result)` - Takes appropriate action based on detection

**Flow:**
1. Loads configuration
2. Initializes face detector, recognizer, system controller
3. Starts idle monitor (subscribes to custom D-Bus signal)
4. When `ScreenDimmed(true)` signal received from KWin script:
   - Captures webcam frame
   - Detects faces
   - If face found, recognizes it
   - Takes action (inhibit/allow/shutdown)
5. When `ScreenDimmed(false)` signal received:
   - Releases any active inhibitors
6. Logs all actions

---

### Phase 8: Example Scripts (Learning Path)

#### Step 8.1: Webcam Test
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

#### Step 8.2: Basic Face Detection
**File:** `examples/step2_basic_face_detection.py`

**Purpose:** Test YuNet face detection on webcam feed.

**What it does:**
- Loads YuNet model
- Detects faces in real-time
- Draws bounding boxes
- Shows confidence scores

#### Step 8.3: Capture Training Data
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

#### Step 8.4: Train Face Model
**File:** `examples/step4_train_face_model.py`

**Purpose:** Train OpenCV LBPH face recognizer from captured photos.

**What it does:**
- Loads images from `data/known_faces/owner/`
- Detects face in each image using YuNet
- Trains LBPH recognizer with cropped faces
- Saves to `models/face_encodings.pkl`

#### Step 8.5: Test Recognition
**File:** `examples/step5_test_recognition.py`

**Purpose:** Test face recognition in real-time.

**What it does:**
- Loads trained LBPH model
- Opens webcam
- Recognizes your face
- Shows "OWNER" or "UNKNOWN"

#### Step 8.6: Test System Inhibitor
**File:** `examples/step6_test_system_inhibitor.py`

**Purpose:** Test preventing screen dim/lock.

**What it does:**
- Calls D-Bus Inhibit method
- Holds lock for 60 seconds
- Releases lock
- Verify screen doesn't dim

#### Step 8.7: Test Idle Detection
**File:** `examples/step7_test_idle_detection.py`

**Purpose:** Test custom KWin D-Bus signal detection.

**What it does:**
- Connects to D-Bus session bus
- Subscribes to `org.sleepchecker.IdleNotifier.ScreenDimmed` signal
- Prints when screen dims (signal: true) and restores (signal: false)
- Verify signal fires when idle timeout is reached

**Prerequisites:**
- KWin script must be installed (`scripts/install_kwin_script.sh`)
- KDE idle timeout must be configured in System Settings → Power Management

**D-Bus Testing Commands:**
```bash
# Check if KWin script is loaded
qdbus org.kde.KWin /Scripting

# Monitor the custom signal
dbus-monitor --session "type='signal',interface='org.sleepchecker.IdleNotifier'"

# Let screen dim from inactivity to test
```

#### Step 8.8: Full Integration Test
**File:** `examples/step8_full_integration.py`

**Purpose:** Test complete system before installing as service.

**What it does:**
- Combines all components
- Monitors custom D-Bus signal from KWin script
- Runs face detection/recognition on dim event
- Takes actions
- Logs everything

**Run for 10-15 minutes and verify:**
- KWin script fires signal when screen dims
- Face recognition accurate
- Inhibitor prevents screen dim
- Logs are clear

---

### Phase 9: Systemd Service Installation

#### Step 9.1: Create Service Unit File
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

#### Step 9.2: Create Install Script
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

#### Step 9.3: Create Uninstall Script
**File:** `scripts/uninstall_service.sh`

**Purpose:** Removes the service.

**What it does:**
1. Stops the service
2. Disables auto-start
3. Removes service file
4. Reloads systemd daemon

---

### Phase 10: Testing and Verification

#### Step 10.1: Check Service Status
```bash
systemctl --user status sleep-checker.service
```

Should show:
- Active: active (running)
- Process ID
- Recent log entries

#### Step 10.2: View Logs
```bash
# Journal logs
journalctl --user -u sleep-checker.service -f

# File logs
tail -f data/logs/sleep_checker.log
```

#### Step 10.3: Test Scenarios

**Test 1: Normal Operation**
1. Let system sit idle for configured timeout
2. KWin script fires `ScreenDimmed(true)` signal
3. Watch logs - should trigger face detection
4. If you're present, screen shouldn't dim
5. Move away, screen should dim/lock

**Test 2: Unknown Person**
1. Have someone else sit in front of camera
2. Wait for idle timeout and dim signal
3. System should shutdown (test carefully!)

**Test 3: No Camera Access**
1. Cover camera or disconnect
2. System should log error but not crash
3. Should fall back to allowing normal sleep

**Test 4: KWin Script Verification**
1. Monitor custom D-Bus signal in one terminal
2. Let screen dim from inactivity
3. Verify signal fires with `true` payload
4. Move mouse, verify signal fires with `false` payload
5. Close laptop lid - verify signal does NOT fire

#### Step 10.4: Performance Monitoring
```bash
# CPU usage
top -p $(pgrep -f main_service.py)

# Memory usage
ps aux | grep main_service.py
```

Should use:
- CPU: <1% when waiting for signal, <20% during face detection
- Memory: <200MB

---

### Phase 11: Configuration and Tuning

#### Step 11.1: Adjust Detection Threshold
Edit `config/user_config.json`:
```json
{
  "detection": {
    "score_threshold": 0.4
  }
}
```

Restart service:
```bash
systemctl --user restart sleep-checker.service
```

#### Step 11.2: Adjust Recognition Threshold
```json
{
  "detection": {
    "recognition_threshold": 40.0
  }
}
```

Lower value = more strict matching (fewer false positives, more false negatives).

#### Step 11.3: Change Idle Timeout
**Note:** This is controlled by KDE, not the service.

**Set in KDE System Settings:**
1. System Settings → Power Management → Energy Saving
2. Set "Dim screen" timeout (e.g., 5 minutes)
3. The KWin script will fire the custom D-Bus signal when this timeout is reached

**KDE → KWin Script → D-Bus → Service Flow:**
```
KDE Idle Timer (5 min)
    ↓
KWin compositor dims screen
    ↓
KWin script detects dim event
    ↓
callDBus() → org.sleepchecker.IdleNotifier.ScreenDimmed(true)
    ↓
IdleMonitor receives signal
    ↓
Webcam capture → Face detection → Recognition
    ↓
Owner found → Inhibit(keep active)  |  No face → Allow sleep  |  Unknown → Shutdown
```

#### Step 11.4: Retrain Face Model
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
- **face_recognizer.py**: OpenCV LBPH face recognition
- **face_trainer.py**: Trains face model from captured photos
- **system_controller.py**: D-Bus interface for system inhibition

### Monitor Modules (`src/monitors/`)
- **idle_monitor.py**: Subscribes to custom KWin D-Bus signal for idle dim detection
- **sleep_monitor.py**: Alternative sleep event interception (fallback)

### Utility Modules (`src/utils/`)
- **config_manager.py**: Configuration loading and merging
- **logger.py**: Structured logging setup
- **image_utils.py**: Image preprocessing helpers

### Daemon (`src/daemon/`)
- **main_service.py**: Main orchestration and event loop

### KWin Scripts (`kwin-scripts/`)
- **sleep-checker-idle/metadata.json**: KWin script package metadata
- **sleep-checker-idle/contents/code/main.js**: KWin script that detects screen dim and emits custom D-Bus signal

### Examples (`examples/`)
- **step1-8**: Progressive learning scripts to understand each component

### Scripts (`scripts/`)
- **download_model.sh**: Download YuNet model
- **install_kwin_script.sh**: Install KWin idle dim detection script
- **uninstall_kwin_script.sh**: Remove KWin script
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
│  (Power Management → Idle Timer → Screen Dim)               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ KWin compositor dims screen
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                KWin Script (sleep-checker-idle)              │
│  Detects dim event → callDBus() →                           │
│  org.sleepchecker.IdleNotifier.ScreenDimmed(true)           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Custom D-Bus signal (Session Bus)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Sleep Checker Service                     │
│                   (main_service.py)                          │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ IdleMonitor  │  │ FaceDetector │  │ System       │      │
│  │ (D-Bus sub)  │→ │ (YuNet)      │→ │ Controller   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                   │                   │            │
│         │                   ↓                   │            │
│         │          ┌──────────────┐            │            │
│         │          │ Face         │            │            │
│         │          │ Recognizer   │            │            │
│         │          │ (LBPH)       │            │            │
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

### KWin Script Issues

**Problem:** KWin script not installed
```bash
# Check if script directory exists
ls ~/.local/share/kwin/scripts/sleep-checker-idle/

# Reinstall
./scripts/install_kwin_script.sh
```

**Problem:** KWin script installed but not enabled
```bash
# Check enabled state
kreadconfig6 --file kwinrc --group Plugins --key sleep-checker-idleEnabled

# Enable manually
kwriteconfig6 --file kwinrc --group Plugins --key sleep-checker-idleEnabled true

# Reload KWin scripts
dbus-send --session --type=method_call \
  --dest=org.kde.KWin /Scripting org.kde.kwin.Scripting.start
```

**Problem:** KWin script not firing signal
```bash
# Monitor the custom signal
dbus-monitor --session "type='signal',interface='org.sleepchecker.IdleNotifier'"

# Check KWin script console for errors
journalctl --user -u plasma-kwin_wayland.service -f
# or for X11:
journalctl --user -u plasma-kwin_x11.service -f
```

**Problem:** KWin script fires but Python doesn't receive
```bash
# Verify Python can see the signal
python3 -c "
import asyncio
from dbus_next.aio import MessageBus
from dbus_next import BusType, MessageType

async def test():
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    def handler(msg):
        if msg.message_type == MessageType.SIGNAL:
            print(f'Signal: {msg.interface}.{msg.member} = {msg.body}')
        return True
    bus.add_message_handler(handler)
    print('Listening for signals... let screen dim')
    while True:
        await asyncio.sleep(1)

asyncio.run(test())
"
```

### Service won't start
```bash
# Check logs
journalctl --user -u sleep-checker.service -n 50

# Common issues:
# - DISPLAY not set: Check Environment in service file
# - Camera busy: Close other apps using webcam
# - Missing model: Run download_model.sh
# - D-Bus not accessible: Check DBUS_SESSION_BUS_ADDRESS
# - KWin script not installed: Run install_kwin_script.sh
```

### D-Bus Connection Issues

**Problem:** Service can't connect to D-Bus
```bash
# Verify D-Bus session is running
echo $DBUS_SESSION_BUS_ADDRESS
# Should show: unix:path=/run/user/1000/bus (or similar)

# Test D-Bus from Python
python3 -c "from dbus_next.aio import MessageBus; import asyncio; asyncio.run(MessageBus().connect())"
# Should complete without errors
```

**Solution:** Ensure service file has correct environment:
```ini
Environment="DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus"
```

**Problem:** Inhibitor not working
```bash
# Check if inhibitor is registered
busctl --user call org.freedesktop.PowerManagement.Inhibit \
  /org/freedesktop/PowerManagement/Inhibit \
  org.freedesktop.PowerManagement.Inhibit HasInhibit

# Manually test inhibitor
dbus-send --session --print-reply \
  --dest=org.freedesktop.PowerManagement.Inhibit \
  /org/freedesktop/PowerManagement/Inhibit \
  org.freedesktop.PowerManagement.Inhibit.Inhibit \
  string:"Test" string:"Testing inhibitor"
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
  org.freedesktop.PowerManagement.Inhibit HasInhibit

# Check if KWin signal was received in logs
tail -20 data/logs/sleep_checker.log
```

---

## Next Steps

1. **Complete Phase 0-2**: Setup project and download models
2. **Phase 3-4**: Build utility and core modules
3. **Phase 5**: Create and install KWin script for idle dim detection
4. **Phase 6**: Build idle monitor that subscribes to custom signal
5. **Run examples sequentially**: Understand each component
6. **Capture and train**: Get good training data
7. **Test integration**: Run step8 before installing service
8. **Install service**: Use install script
9. **Monitor and tune**: Adjust thresholds based on accuracy

---

## Additional Resources

- **OpenCV YuNet**: https://github.com/opencv/opencv_zoo/tree/master/models/face_detection_yunet
- **OpenCV Face Recognition (LBPH)**: https://docs.opencv.org/4.x/da/d60/tutorial_face_main.html
- **KWin Scripting**: https://develop.kde.org/docs/plasma/kwin/api/
- **KWin callDBus**: https://develop.kde.org/docs/plasma/kwin/api/#callDBus
- **D-Bus Python (dbus-next)**: https://python-dbus-next.readthedocs.io/
- **systemd user services**: https://wiki.archlinux.org/title/Systemd/User

---

## License

MIT License - Feel free to modify and distribute.

## Contributing

This is a personal learning project, but suggestions and improvements are welcome!