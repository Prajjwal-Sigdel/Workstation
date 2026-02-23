import cv2
import face_recognition
import pickle
import numpy as np
import os

# Paths relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ENCODING_FILE = os.path.join(PROJECT_ROOT, "data/me_encoding.pkl")
CONFIDENCE_THRESHOLD = 0.4 # Lower = more strict matching 
SCALE_FACTOR = 0.25 # Process smaller frames for speed

# Load known encodings
print("Loading known face encodings...")
try:
    with open(ENCODING_FILE, "rb") as f:
        known_encodings = pickle.load(f)
    print(f"Loaded {len(known_encodings)} known face encodings")
except FileNotFoundError:
    print(f"Error: {ENCODING_FILE} not found. Run phase2_encode_face.py to collect training data !!!")
    exit(1)

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error:: Could not open webcam")
    exit(1)

# Optimize webcam settings for better performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

print("\n LIVE FACE RECOGNITION")
print("Controls:")
print("     SPACE = Test recognition")
print("     'q' = Quit")
print("-" * 40)

frame_count = 0
# Cache for recognition results
last_faces_info = []
last_status = "NO FACE - Allow sleep"
last_status_color = (0, 255, 255)

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame,1)
    if not ret:
        print("Failed to grab frame")
        break

    # Process every 5th frame for better performance
    frame_count += 1
    
    # Only process face recognition every 5th frame
    if frame_count % 5 == 0:
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0,0), fx=SCALE_FACTOR, fy=SCALE_FACTOR)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces and get the encodings
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        # Process each detected face and cache results
        faces_info = []
        for (top, right, bottom , left), face_encoding in zip(face_locations, face_encodings):
            # Scale back up face locations since we scaled down
            top= int(top / SCALE_FACTOR)
            right = int(right / SCALE_FACTOR)
            bottom = int(bottom / SCALE_FACTOR)
            left = int(left / SCALE_FACTOR)

            # Compare with known faces
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match_distance = np.min(distances)

            # Determine if it's me or unknown person
            if best_match_distance < CONFIDENCE_THRESHOLD:
                name = "ME"
                color = (0, 255, 0) # Green - fixed from 225 to 255
                confidence = round((1 - best_match_distance)*100, 1)
            else:
                name = "UNKNOWN PERSON"
                color = (0, 0, 255) # Red
                confidence = round((1 - best_match_distance)*100, 1)
            
            faces_info.append({
                'bbox': (left, top, right, bottom),
                'name': name,
                'color': color,
                'confidence': confidence
            })

        # Update status based on detection results
        if len(face_encodings) > 0:
            # Check if any face is "ME"
            me_detected = any(face['name'] == "ME" for face in faces_info)
            if me_detected:
                last_status = "ME DETECTED - Stay awake"
                last_status_color = (0, 255, 0) # Green - fixed from 225 to 255
            else:
                last_status = "UNKNOWN PERSON - Shutdown"
                last_status_color = (0, 0, 255) # Red - fixed from 225 to 255
        else:
            last_status = "NO FACE - Allow sleep"
            last_status_color = (0, 255, 255) # Yellow - fixed from 225 to 255
        
        # Cache results
        last_faces_info = faces_info

    # Draw using cached results (this runs every frame for smooth display)
    for face in last_faces_info:
        left, top, right, bottom = face['bbox']
        cv2.rectangle(frame, (left, top), (right, bottom), face['color'], 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), face['color'], cv2.FILLED)
        cv2.putText(frame, f"{face['name']} ({face['confidence']}%)", (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

    # Display status (changed font from SCRIPT_SIMPLEX to SIMPLEX for better performance)
    cv2.putText(frame, last_status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, last_status_color, 2)
    cv2.putText(frame, f"Face detected: {len(last_faces_info)}",(10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Show frame
    cv2.imshow('Sleep Checker - Face Recognition', frame)

    # Handle key presses
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '): # Spacebar for testing
        print(f"TEST RESULT: {last_status}")
        if last_faces_info:
            for i, face in enumerate(last_faces_info):
                print(f" Face {i+1}: {face['name']} (confidence: {face['confidence']}%)")

# Cleanup
cap.release()
cv2.destroyAllWindows()
print("\n Face Recognition Stopped !!!")