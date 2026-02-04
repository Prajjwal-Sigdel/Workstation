import cv2
import face_recognition
import pickle
import numpy as np
import time
import os
import subprocess
import signal
import sys
from datetime import datetime

# Configuration
ENCODING_FILE = "data/me_encoding.pkl"
CONFIDENCE_THRESHOLD = 0.45
SCALE_FACTOR = 0.25
DETECTION_TIME = 5
LOG_FILE = "data/sleep_controller.log"

class SleepController:  # Fixed: was sleepController
    def __init__(self):
        self.known_encodings = self.load_encodings()
        self.log_file = LOG_FILE
        self.display_server = self.detect_display_server()

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

    def detect_display_server(self):
        """Detect if running on X11 or Wayland"""
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        xdg_session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        
        if wayland_display or xdg_session_type == 'wayland':
            return 'wayland'
        else:
            return 'x11'

    def load_encodings(self):
        """Load known face encodings"""
        try:
            with open(ENCODING_FILE, "rb") as f:
                encodings = pickle.load(f)
            self.log(f"Loaded {len(encodings)} known face encodings")
            return encodings
        except FileNotFoundError:
            self.log(f"Error: {ENCODING_FILE} not found. Run phase2_face_training.py first.")
            sys.exit(1)

    def log(self, message):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)

        try:
            with open(self.log_file, "a") as f:
                f.write(log_msg + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

    def analyze_webcam(self):
        """Analyze webcam feed for specified duration"""
        self.log("Starting webcam analysis...")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.log("Error: Could not open webcam")
            return "ERROR"
        
        # Optimize webcam settings
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        start_time = time.time()
        me_detections = 0
        unknown_detections = 0
        total_frames = 0
        frames_with_faces = 0

        self.log(f"Analyzing for {DETECTION_TIME} seconds on {self.display_server.upper()}...")

        while time.time() - start_time < DETECTION_TIME:
            ret, frame = cap.read()
            if not ret:
                continue

            total_frames += 1

            # Process every 3rd frame for performance
            if total_frames % 3 != 0:
                continue

            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=SCALE_FACTOR, fy=SCALE_FACTOR)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Detect faces and get encodings
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            if len(face_encodings) > 0:
                frames_with_faces += 1

                for face_encoding in face_encodings:
                    # Compare with known faces
                    distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                    best_match_distance = np.min(distances)

                    if best_match_distance < CONFIDENCE_THRESHOLD:
                        me_detections += 1
                    else:
                        unknown_detections += 1
        
        cap.release()

        # Analysis complete - make decision
        analysis_result = self.make_decision(me_detections, unknown_detections, frames_with_faces, total_frames)
        return analysis_result
    
    def make_decision(self, me_detections, unknown_detections, frames_with_faces, total_frames):
        """Make system decision based on analysis results"""

        self.log(f"Analysis Results:")
        self.log(f"  Total frames: {total_frames}")
        self.log(f"  Frames with faces: {frames_with_faces}")  # Fixed: was me_detections
        self.log(f"  ME detections: {me_detections}")  # Fixed: added this line
        self.log(f"  UNKNOWN detections: {unknown_detections}")

        # Decision logic
        if me_detections > 0:
            decision = "STAY_AWAKE"
            reason = f"User present (ME detected {me_detections} times)"
        elif unknown_detections > 0:
            decision = "SHUTDOWN"
            reason = f"Unknown person detected {unknown_detections} times"
        elif frames_with_faces == 0:
            decision = "ALLOW_SLEEP"
            reason = "No faces detected - user not present"  # Fixed: was reson
        else:
            decision = "ALLOW_SLEEP"
            reason = "Inconclusive detection results"

        self.log(f"DECISION: {decision} - {reason}")
        return decision
    
    def execute_action(self, decision, test_mode=True):
        """Execute the system action based on decision"""
        
        if test_mode:
            self.log("=== TEST MODE - No actual system actions taken ===")

        if decision == "STAY_AWAKE":
            if test_mode:
                self.log("ACTION: Would prevent sleep (reset idle timer)")
            else:
                self.prevent_sleep()

        elif decision == "SHUTDOWN":
            if test_mode:
                self.log("ACTION: Would shutdown system (security measure)")
            else:
                self.shutdown_system()

        elif decision == "ALLOW_SLEEP":
            if test_mode:
                self.log("ACTION: Would allow normal sleep")
            else:
                self.log("Allowing system to sleep normally")  # Fixed: was normallly

        else:  # ERROR
            if test_mode:
                self.log("ACTION: Would allow sleep due to error")
            else:
                self.log("Error occurred - allowing normal sleep as fallback")

    def prevent_sleep(self):
        """Prevent system sleep by simulating user activity - X11 & Wayland compatible"""
        self.log(f"Preventing sleep on {self.display_server.upper()}...")
        
        success = False
        
        if self.display_server == 'wayland':
            # Wayland-specific methods
            success = self._prevent_sleep_wayland()
        else:
            # X11-specific methods
            success = self._prevent_sleep_x11()
        
        # Fallback methods if primary methods fail
        if not success:
            success = self._prevent_sleep_fallback()
        
        if success:
            self.log("Sleep prevention successful")
        else:
            self.log("Warning: All sleep prevention methods failed")

    def _prevent_sleep_wayland(self):
        """Wayland-specific sleep prevention"""
        methods = [
            # Method 1: Use wlrctl (if available)
            lambda: self._run_command(["wlrctl", "keyboard", "key", "shift"]),
            
            # Method 2: Use ydotool (Wayland alternative to xdotool)
            lambda: self._run_command(["ydotool", "key", "42:1", "42:0"]),  # Shift key
            
            # Method 3: Use wtype (Wayland text input)
            lambda: self._run_command(["wtype", ""]),  # Empty input
            
            # Method 4: GNOME-specific (if on GNOME Wayland)
            lambda: self._run_command(["gdbus", "call", "--session", "--dest=org.gnome.ScreenSaver", 
                                     "--object-path=/org/gnome/ScreenSaver", 
                                     "--method=org.gnome.ScreenSaver.SimulateUserActivity"]),
        ]
        
        return self._try_methods(methods, "Wayland")

    def _prevent_sleep_x11(self):
        """X11-specific sleep prevention"""
        methods = [
            # Method 1: Use xdotool
            lambda: self._run_command(["xdotool", "key", "shift"]),
            
            # Method 2: Use xset to reset screen saver
            lambda: self._run_command(["xset", "s", "reset"]),
            
            # Method 3: Use xinput for mouse movement
            lambda: self._run_command(["xdotool", "mousemove_relative", "1", "1"]) and 
                     self._run_command(["xdotool", "mousemove_relative", "--", "-1", "-1"]),
            
            # Method 4: Use xprintidle to reset idle timer
            lambda: self._run_command(["xset", "dpms", "force", "on"]),
        ]
        
        return self._try_methods(methods, "X11")

    def _prevent_sleep_fallback(self):
        """Fallback methods that work on both X11 and Wayland"""
        methods = [
            # Method 1: systemd inhibit
            lambda: self._run_command(["systemd-inhibit", "--what=sleep:idle", "--who=sleep_checker", 
                                     "--why=User presence detected", "sleep", "1"]),
            
            # Method 2: Create temporary file to signal activity
            lambda: self._create_activity_file(),
            
            # Method 3: systemctl prevention (temporary)
            lambda: self._run_command(["pkill", "-USR1", "systemd-logind"]),
        ]
        
        return self._try_methods(methods, "Fallback")

    def _try_methods(self, methods, method_type):
        """Try multiple methods until one succeeds"""
        for i, method in enumerate(methods, 1):
            try:
                if method():
                    self.log(f"{method_type} sleep prevention method {i} succeeded")
                    return True
            except Exception as e:
                self.log(f"{method_type} method {i} failed: {e}")
        
        return False

    def _run_command(self, cmd):
        """Run a command and return success status"""
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _create_activity_file(self):
        """Create activity file as fallback"""
        try:
            activity_file = "/tmp/sleep_checker_activity"
            with open(activity_file, "w") as f:
                f.write(str(time.time()))
            return True
        except Exception:
            return False

    def shutdown_system(self):
        """Shutdown system immediately - Universal method"""
        try:
            self.log("SECURITY ALERT: Initiating system shutdown")
            
            # Try multiple shutdown methods
            shutdown_methods = [
                ["shutdown", "-h", "now"],
                ["systemctl", "poweroff"],
                ["poweroff"],
                ["halt", "-p"]
            ]
            
            for method in shutdown_methods:
                if self._run_command(method):
                    self.log(f"Shutdown initiated using: {' '.join(method)}")
                    return
            
            self.log("Warning: All shutdown methods failed")
            
        except Exception as e:
            self.log(f"Error during shutdown: {e}")

    def test_mode(self):
        """Run in test mode for development"""
        self.log("=" * 50)
        self.log(f"SLEEP CONTROLLER - TEST MODE ({self.display_server.upper()})")
        self.log("=" * 50)

        try:
            while True:
                self.log("\nPress ENTER to simulate sleep event (or 'q' to quit):")
                user_input = input().strip().lower()

                if user_input == 'q':
                    break

                self.log("Simulating sleep event...")
                decision = self.analyze_webcam()
                self.execute_action(decision, test_mode=True)
                self.log("-" * 30)

        except KeyboardInterrupt:
            self.log("\nTest mode interrupted by user")

        self.log("Test mode ended")

def signal_handler(sig, frame):
    """Handle interrupt signals gracefully"""
    print("\nSleep controller stopped")
    sys.exit(0)

def main():
    """Main function"""
    print("Phase 4 - Sleep Controller")
    print("=" * 50)

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    controller = SleepController()
    controller.test_mode()

if __name__ == "__main__":
    main()
