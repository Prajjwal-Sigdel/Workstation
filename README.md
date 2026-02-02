# Sleep Checker 😴👁️

**Intelligent Sleep Prevention System for Linux**

## 🎯 Problem Statement
When reading ebooks on Linux, the system automatically goes to sleep during periods of inactivity (AFK). This interrupts reading sessions and requires manual intervention to wake the system.

## 💡 The Solution
A smart webcam-based monitoring system that runs just before the PC is about to sleep, analyzes the situation, and takes intelligent action:

- **✅ My face detected** → Reset sleep timer (keep system awake)
- **⚠️ Someone else detected** → Shutdown system (security measure)  
- **💤 No face detected** → Allow normal sleep (I'm not here)

## 🚀 Development Phases

### **Phase 1: Traditional Face Detection** ✅ **COMPLETED**
**File**: `phase1_face_detect.py`
- **Technology**: OpenCV Haar Cascades
- **Purpose**: Basic real-time face detection proof-of-concept
- **Status**: ✅ Working - detects faces in webcam feed
- **Learning**: Understand computer vision basics

### **Phase 2: Personal Face Training System** ✅ **COMPLETED**
**Files**: `phase2_face_detect.py` + `phase2_encode_face.py`
- **Purpose**: Create personal face recognition dataset
- **Process**: 
  - Capture face images → Generate deep learning encodings
  - Store mathematical face representations for comparison
- **Status**: ✅ Working - 4 face encodings generated and saved
- **Output**: `data/me_encoding.pkl` (personal face database)

### **Phase 3: Real-Time Face Recognition** 🔄 **IN PROGRESS**
**File**: `phase3_face_recognition.py` *(to be created)*
- **Purpose**: Live webcam face recognition and classification
- **Features**:
  - Load personal face encodings
  - Real-time face detection and recognition
  - Classify: "Me", "Unknown Person", or "Nobody"
  - Display confidence scores and bounding boxes
- **Technology**: `face_recognition` library + OpenCV
- **Testing**: Manual testing via webcam before system integration

### **Phase 4: System Integration** 🔲 **PLANNED**
**File**: `phase4_system_controller.py` *(to be created)*
- **Purpose**: Interface with Linux power management
- **Features**:
  - Hook into sleep/suspend events (systemd/pm-utils)
  - Execute face recognition before sleep
  - System actions: prevent sleep, shutdown, or allow sleep
  - Logging and notifications
- **Integration**: Linux power management hooks

### **Phase 5: Production Deployment** 🔲 **PLANNED**  
**File**: `phase5_service_daemon.py` *(to be created)*
- **Purpose**: Background service for seamless operation
- **Features**:
  - Systemd service configuration
  - Error handling and recovery
  - Configuration file support
  - Performance optimization
  - Auto-start on boot

### **Phase 6: Advanced Features** 🔲 **FUTURE**
**Potential enhancements**:
- **Smart Learning**: Adapt to lighting conditions and appearance changes
- **Multi-User Support**: Multiple authorized face profiles
- **Remote Notifications**: Alert via email/phone when unknown person detected
- **Activity Detection**: Distinguish between reading vs. sleeping
- **Privacy Mode**: Disable during certain hours
- **Backup Authentication**: Fallback methods if camera fails

## 📁 Project Structure
```
sleep_checker/
├── phase1_face_detect.py      # ✅ Basic face detection
├── phase2_face_detect.py      # ✅ Training data capture  
├── phase2_encode_face.py      # ✅ Face encoding generation
├── phase3_face_recognition.py # 🔄 Live recognition (next)
├── phase4_system_controller.py# 🔲 System integration 
├── phase5_service_daemon.py   # 🔲 Production service
├── data/
│   ├── known_faces/          # ✅ Personal face images
│   └── me_encoding.pkl       # ✅ Encoded face data
├── face_recognition_models/  # ✅ Custom model package
├── requirements.txt          # ✅ Dependencies
└── README.md                # 📖 This roadmap
```

## 🛠️ Technology Stack
- **Computer Vision**: OpenCV, face_recognition (dlib)
- **Deep Learning**: ResNet-based face embeddings
- **System Integration**: Linux systemd, power management
- **Language**: Python 3.14+
- **Environment**: Virtual environment (venv)

## 🎯 Current Status: Phase 3 Ready
**Next Steps**:
1. **Build Phase 3**: Real-time face recognition system
2. **Test Recognition**: Verify accuracy with live webcam
3. **System Integration**: Hook into Linux sleep events
4. **Production Deployment**: Create background service

## 🚀 Quick Start
```bash
# Setup environment
source venv/bin/activate
pip install -r requirements.txt

# Test current phases
python phase1_face_detect.py  # Basic detection
python phase2_encode_face.py  # Generate encodings (if needed)

# Next: Build phase3_face_recognition.py
```

---
*"Stay awake when I'm reading, sleep when I'm not. Simple."* 💭
