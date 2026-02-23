import cv2
import numpy as np
import time
import os

# Model loading with safety checks
model_path = "/home/prajjwal/Documents/Repo/sleep_checker/v2_sleep_blocker/data/yunet.onnx"
print("Model path:", model_path)
if not os.path.exists(model_path):
    print("ERROR: Model file not found!")
    exit(1)
if os.path.getsize(model_path) == 0:
    print("ERROR: Model file is empty (0 bytes)!")
    exit(1)
print("File size:", os.path.getsize(model_path), "bytes")  # Expect ~232589

detector = cv2.FaceDetectorYN.create(model_path, "", (0, 0))

# Set confidence threshold (tune this: lower for more detections, but more false positives)
detector.setScoreThreshold(0.5)  # 0.3 for debug – raise to 0.5 for production

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open webcam")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Warmup delay – gives camera time to adjust exposure/focus on your i5's integrated cam
time.sleep(0.5)

# Live detection loop – runs at ~30FPS on your Iris G1, <10% CPU in htop
while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame,1)
    if not ret:
        print("Frame grab failed")
        break
    
    # Dynamic input size – matches your 640x480, efficient on ext4 load
    h, w = frame.shape[:2]
    detector.setInputSize((w, h))
    
    # Run YuNet detection – quick CNN pass, outputs [1, num_faces, 15] array
    _, detections = detector.detect(frame)
    
    # Process each detection
    if detections is not None:
        for det in detections:
            conf = det[4]
            if conf > 0.5:  # Filter – visualize as confidence gate
                x, y, w, h = map(int, det[0:4])  # Box coords (float → int pixels)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green box, 2px
                cv2.putText(frame, f"Conf: {conf:.2f}", (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)  # Score label
    
    # Display in Wayland window – KWin handles it smoothly
    cv2.imshow("Live Face Detect", frame)
    
    # Exit on 'q' – 1ms wait keeps loop responsive without pegging cores
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup – frees /dev/video0 and closes window
cap.release()
cv2.destroyAllWindows()