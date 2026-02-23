#!/home/prajjwal/Documents/Repo/sleep_checker/venv/bin/python
import cv2
import face_recognition
import pickle
import numpy as np
import time
import os
import subprocess
import signal
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configuration file path
CONFIG_FILE = Path("/etc/sleep_checker/config.json")
DEFAULT_CONFIG = {
    "encoding_file": "/home/prajjwal/Documents/Repo/sleep_checker/data/me_encoding.pkl",
    "log_file": "/home/prajjwal/Documents/Repo/sleep_checker/data/sleep_checker.log",
    "confidence_threshold": 0.4,
    "detection_time": 5,
    "scale_factor": 0.25,
    "enable_shutdown_on_unknown": True,
    "enable_logging": True
}

# Full paths for system commands (required when PATH may not be set)
SYSTEM_COMMANDS = {
    "systemctl": "/usr/bin/systemctl",
    "shutdown": "/usr/bin/shutdown",
    "poweroff": "/usr/bin/poweroff",
}

class SleepCheckerDaemon:
    def __init__(self):
        # Ensure PATH is set for subprocess calls
        os.environ['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
        
        self.config = self.load_config()
        self.validate_config()
        self.known_encodings = self.load_encodings()
        
        # Ensure log directory exists
        log_dir = Path(self.config['log_file']).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict:
        """Load configuration from file or use defaults"""
        try:
            if CONFIG_FILE.exists():
                with CONFIG_FILE.open('r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                return DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error loading config, using defaults: {e}")
            return DEFAULT_CONFIG.copy()
    
    def validate_config(self) -> None:
        """Basic validation of config values"""
        if not (0 <= self.config['confidence_threshold'] <= 1):
            raise ValueError("confidence_threshold must be between 0 and 1")
        if self.config['detection_time'] <= 0:
            raise ValueError("detection_time must be positive")
        if self.config['scale_factor'] <= 0 or self.config['scale_factor'] > 1:
            raise ValueError("scale_factor must be between 0 and 1")
    
    def load_encodings(self) -> List[np.ndarray]:
        """Load known face encodings"""
        encoding_path = Path(self.config['encoding_file'])
        try:
            with encoding_path.open("rb") as f:
                encodings = pickle.load(f)
            self.log(f"Loaded {len(encodings)} known face encodings")
            return encodings
        except FileNotFoundError:
            self.log(f"Error: {encoding_path} not found")
            sys.exit(0)  # Allow sleep if encodings not found
        except Exception as e:
            self.log(f"Error loading encodings: {e}")
            sys.exit(0)  # Allow sleep on error
    
    def log(self, message: str) -> None:
        """Log messages with timestamp"""
        if not self.config.get('enable_logging', True):
            return
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        
        # Always print to stdout for systemd journal
        print(log_msg, flush=True)
        
        try:
            log_path = Path(self.config['log_file'])
            with log_path.open("a") as f:
                f.write(log_msg + "\n")
                f.flush()
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}", flush=True)
    
    def analyze_webcam(self) -> str:
        """Analyze webcam feed and return decision"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.log("Error: Could not open webcam - allowing sleep")
            return "ALLOW_SLEEP"
        
        # Optimize webcam settings
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Camera warmup
        time.sleep(0.3)
        
        start_time = time.time()
        me_detections = 0
        unknown_detections = 0
        total_frames = 0
        frames_with_faces = 0
        
        while time.time() - start_time < self.config['detection_time']:
            ret, frame = cap.read()
            if not ret:
                continue
            
            total_frames += 1
            
            # Process every 3rd frame for performance
            if total_frames % 3 != 0:
                continue
            
            # Low-light enhancement
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            enhanced_gray = cv2.equalizeHist(gray)
            enhanced_frame = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)
            
            # Resize frame for faster processing
            small_frame = cv2.resize(enhanced_frame, (0, 0), 
                                     fx=self.config['scale_factor'], 
                                     fy=self.config['scale_factor'])
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            try:
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            except Exception as e:
                self.log(f"Face recognition error: {e}")
                continue
            
            if len(face_encodings) > 0:
                frames_with_faces += 1
                
                me_detected_in_frame = False
                unknown_in_frame = False
                
                for face_encoding in face_encodings:
                    distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                    best_match_distance = np.min(distances)
                    
                    if best_match_distance < self.config['confidence_threshold']:
                        me_detected_in_frame = True
                    else:
                        unknown_in_frame = True
                
                if me_detected_in_frame:
                    me_detections += 1
                elif unknown_in_frame:
                    unknown_detections += 1
        
        cap.release()
        
        self.log(f"Analysis: frames={total_frames}, faces={frames_with_faces}, me={me_detections}, unknown={unknown_detections}")
        
        # Make decision
        if me_detections > 0:
            self.log("DECISION: STAY_AWAKE - User present")
            return "STAY_AWAKE"
        elif unknown_detections > 0 and self.config['enable_shutdown_on_unknown']:
            self.log("DECISION: SHUTDOWN - Unknown person detected")
            return "SHUTDOWN"
        else:
            self.log("DECISION: ALLOW_SLEEP - No user present")
            return "ALLOW_SLEEP"
    
    def shutdown_system(self) -> None:
        """Shutdown system"""
        self.log("SECURITY ALERT: Unknown person detected - shutting down!")
        
        shutdown_methods = [
            [SYSTEM_COMMANDS["systemctl"], "poweroff"],
            [SYSTEM_COMMANDS["poweroff"]],
            [SYSTEM_COMMANDS["shutdown"], "-h", "now"],
        ]
        
        for method in shutdown_methods:
            try:
                self.log(f"Executing: {' '.join(method)}")
                subprocess.run(method, check=True, timeout=10)
                return
            except Exception as e:
                self.log(f"Failed: {e}")
        
        self.log("Error: All shutdown methods failed")


def signal_handler(sig: int, frame: Optional[object]) -> None:
    print("Sleep checker stopping", flush=True)
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == '--test':
            print("Test mode - no system actions")
            daemon = SleepCheckerDaemon()
            decision = daemon.analyze_webcam()
            print(f"Decision: {decision}")
            sys.exit(0)
        
        elif arg == 'post':
            # Post-sleep - nothing to do
            sys.exit(0)
        
        elif arg != 'pre':
            print(f"Usage: {sys.argv[0]} [pre|post|--test]")
            sys.exit(0)
    
    # Main execution for pre-sleep hook
    daemon = SleepCheckerDaemon()
    daemon.log("=== Sleep checker activated ===")
    
    decision = daemon.analyze_webcam()
    
    if decision == "STAY_AWAKE":
        daemon.log(">>> BLOCKING SLEEP (exit 1) <<<")
        sys.exit(1)  # NON-ZERO EXIT BLOCKS SLEEP
    
    elif decision == "SHUTDOWN":
        daemon.shutdown_system()
        sys.exit(0)
    
    else:  # ALLOW_SLEEP
        daemon.log(">>> ALLOWING SLEEP (exit 0) <<<")
        sys.exit(0)


if __name__ == "__main__":
    main()