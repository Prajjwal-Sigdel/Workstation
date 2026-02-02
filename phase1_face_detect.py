import cv2
import time

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Initialize webcam with optimized settings
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Could not open camera !!!")

# Optimize webcam settings for better performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

print("Phase 1 - Traditional Face Detection")
print("Camera running. Press 'q' to quit.")
print("-" * 40)

face_present_frames = 0
FACE_THRESHOLD = 5  # Increased from 3 for more stable detection
frame_count = 0
last_detection_time = time.time()

while True:
    start_time = time.time()
    frame_count += 1
    
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)  # Mirror effect
    if not ret:
        print("Failed to grab frame")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Improved detection parameters for better performance
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,  # Smaller scale factor for better detection
        minNeighbors=5,   # Reduced from 7 for faster processing
        minSize=(80, 80), # Increased minimum size for more reliable detection
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    # Update face presence tracking
    if len(faces) > 0:
        face_present_frames += 1
        last_detection_time = time.time()
    else:
        face_present_frames = max(0, face_present_frames - 1)  # Gradual decrease instead of immediate reset

    # Determine status
    is_face_confirmed = face_present_frames >= FACE_THRESHOLD
    time_since_detection = time.time() - last_detection_time
    
    # Draw face rectangles and status
    if len(faces) > 0:
        for (x, y, w, h) in faces:
            # Use different colors based on confirmation status
            color = (0, 255, 0) if is_face_confirmed else (0, 255, 255)  # Green if confirmed, Yellow if detecting
            thickness = 3 if is_face_confirmed else 2
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, thickness)
            
            # Add confidence indicator
            confidence_text = "CONFIRMED" if is_face_confirmed else "DETECTING"
            cv2.putText(frame, confidence_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # Status display
    status_text = f"Faces: {len(faces)} | Frames: {face_present_frames}/{FACE_THRESHOLD}"
    status_color = (0, 255, 0) if is_face_confirmed else (255, 255, 255)  # Green if face confirmed, white otherwise
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    
    # Presence status
    if is_face_confirmed:
        presence_status = "FACE PRESENCE CONFIRMED"
        presence_color = (0, 255, 0)
    elif len(faces) > 0:
        presence_status = "DETECTING FACE..."
        presence_color = (0, 255, 255)
    else:
        presence_status = "NO FACE DETECTED"
        presence_color = (0, 0, 255)
    
    cv2.putText(frame, presence_status, (10, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, presence_color, 2)
    
    # Performance info
    fps = 1.0 / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
    cv2.putText(frame, f"FPS: {fps:.1f}", (frame.shape[1] - 100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, f"Frame: {frame_count}", (frame.shape[1] - 120, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # Display frame
    cv2.imshow("Phase 1 - Traditional Face Detection (OpenCV)", frame)

    # Handle key presses
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):  # Spacebar for manual test
        print(f"\nMANUAL TEST:")
        print(f"  Faces detected: {len(faces)}")
        print(f"  Consecutive frames: {face_present_frames}/{FACE_THRESHOLD}")
        print(f"  Status: {presence_status}")
        print(f"  Time since last detection: {time_since_detection:.2f}s")

# Cleanup
cap.release()
cv2.destroyAllWindows()
print("\nFace detection stopped!")
print(f"Total frames processed: {frame_count}")