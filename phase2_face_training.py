import cv2
import face_recognition
import os
import pickle
import time

# Configuration
KNOWN_DIR = "data/known_faces"
ENCODING_FILE = "data/me_encoding.pkl"
CAPTURE_COOLDOWN = 1.0  # Seconds between captures to prevent spam

# Ensure directories exist
os.makedirs(KNOWN_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)

def get_next_filename():
    """Get the next available filename (me_0.jpg, me_1.jpg, etc.)"""
    existing_files = [f for f in os.listdir(KNOWN_DIR) if f.startswith("me_") and f.endswith(".jpg")]
    if not existing_files:
        return "me_0.jpg"
    
    numbers = []
    for filename in existing_files:
        try:
            num = int(filename[3:-4])  # Extract number from "me_X.jpg"
            numbers.append(num)
        except ValueError:
            continue
    
    return f"me_{max(numbers) + 1 if numbers else 0}.jpg"

def capture_face_images():
    """Capture face images for training"""
    # Initialize face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    
    # Initialize webcam with optimized settings
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return False
    
    # Optimize webcam settings
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("\nPhase 2a - Face Image Capture")
    print("Controls:")
    print("  's' = Save face image")
    print("  'q' = Quit capture mode")
    print("  SPACE = Manual test")
    print("-" * 40)
    
    frame_count = 0
    last_capture_time = 0
    saved_count = 0
    
    while True:
        start_time = time.time()
        frame_count += 1
        
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)  # Mirror effect
        if not ret:
            print("Failed to grab frame")
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Draw face rectangles
        can_capture = len(faces) == 1  # Only allow capture when exactly one face is detected
        current_time = time.time()
        cooldown_remaining = max(0, CAPTURE_COOLDOWN - (current_time - last_capture_time))
        
        for (x, y, w, h) in faces:
            color = (0, 255, 0) if can_capture and cooldown_remaining == 0 else (0, 255, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            
            # Add capture status
            if can_capture:
                if cooldown_remaining == 0:
                    status = "READY TO CAPTURE"
                else:
                    status = f"COOLDOWN: {cooldown_remaining:.1f}s"
            else:
                status = "MULTIPLE FACES" if len(faces) > 1 else "NO FACE"
            
            cv2.putText(frame, status, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Status display
        status_text = f"Faces: {len(faces)} | Saved: {saved_count}"
        status_color = (0, 255, 0) if can_capture else (255, 255, 255)
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Instructions
        cv2.putText(frame, "Press 's' to save face image", (10, frame.shape[0] - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to finish capture", (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Performance info
        fps = 1.0 / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
        cv2.putText(frame, f"FPS: {fps:.1f}", (frame.shape[1] - 100, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Display frame
        cv2.imshow("Phase 2 - Face Training Data Capture", frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s') and can_capture and cooldown_remaining == 0:
            # Save the face image
            filename = get_next_filename()
            filepath = os.path.join(KNOWN_DIR, filename)
            
            # Extract and save the face region
            x, y, w, h = faces[0]
            face_img = frame[y:y+h, x:x+w]
            cv2.imwrite(filepath, face_img)
            
            print(f"Saved: {filename}")
            saved_count += 1
            last_capture_time = current_time
            
        elif key == ord(' '):  # Manual test
            print(f"\nMANUAL TEST:")
            print(f"  Faces detected: {len(faces)}")
            print(f"  Can capture: {can_capture}")
            print(f"  Cooldown remaining: {cooldown_remaining:.1f}s")
            print(f"  Images saved: {saved_count}")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\nCapture complete! Saved {saved_count} face images.")
    return saved_count > 0

def encode_faces():
    """Encode all face images in the known_faces directory"""
    print("\nPhase 2b - Face Encoding Generation")
    print("-" * 40)
    
    if not os.path.exists(KNOWN_DIR):
        print(f"Error: {KNOWN_DIR} directory not found")
        return False
    
    # Get all jpg files
    image_files = [f for f in os.listdir(KNOWN_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"No image files found in {KNOWN_DIR}")
        return False
    
    print(f"Found {len(image_files)} image files")
    
    encodings = []
    successful_encodings = 0
    
    for filename in sorted(image_files):
        filepath = os.path.join(KNOWN_DIR, filename)
        
        try:
            # Load image
            image = face_recognition.load_image_file(filepath)
            
            # Generate face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 1:
                encodings.append(face_encodings[0])
                successful_encodings += 1
                print(f"Encoded: {filename}")
            elif len(face_encodings) == 0:
                print(f"Skipped: {filename} (no face detected)")
            else:
                print(f"Skipped: {filename} (multiple faces detected: {len(face_encodings)})")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    if not encodings:
        print("No valid face encodings generated")
        return False
    
    # Save encodings to pickle file
    try:
        with open(ENCODING_FILE, "wb") as f:
            pickle.dump(encodings, f)
        
        print(f"\nEncoding Summary:")
        print(f"  Total images processed: {len(image_files)}")
        print(f"  Successful encodings: {successful_encodings}")
        print(f"  Saved to: {ENCODING_FILE}")
        
        return True
        
    except Exception as e:
        print(f"Error saving encodings: {e}")
        return False

def main():
    """Main function to orchestrate face training workflow"""
    print("Phase 2 - Face Training System")
    print("=" * 50)
    
    # Check if user wants to capture new images
    capture_choice = input("\nDo you want to capture new face images? (y/n): ").lower().strip()
    
    if capture_choice in ['y', 'yes']:
        print("\nStarting face image capture...")
        if not capture_face_images():
            print("Face capture failed or cancelled")
            return
    else:
        print("Skipping face image capture")
    
    # Check if there are images to encode
    if not os.path.exists(KNOWN_DIR):
        print(f"No {KNOWN_DIR} directory found. Please capture some images first.")
        return
    
    image_files = [f for f in os.listdir(KNOWN_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"No images found in {KNOWN_DIR}. Please capture some images first.")
        return
    
    # Ask if user wants to encode faces
    encode_choice = input(f"\nFound {len(image_files)} images. Encode them? (y/n): ").lower().strip()
    
    if encode_choice in ['y', 'yes']:
        print("\nStarting face encoding...")
        if encode_faces():
            print("\nFace training completed successfully!")
        else:
            print("\nFace encoding failed")
    else:
        print("Encoding skipped")
    
    print("\nPhase 2 training complete!")

if __name__ == "__main__":
    main()