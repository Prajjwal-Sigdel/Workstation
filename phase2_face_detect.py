import cv2
import os

SAVE_DIR = "data/known_faces"
os.makedirs(SAVE_DIR, exist_ok=True)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cap = cv2.VideoCapture(0)

print("Press 's' to save face | 'q' to quit. ")

count = 0

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=7,
        minSize=(80, 80)
    )

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 225, 0), 2)

        face_img = frame[y:y+h, x:x+w]

    cv2.imshow("Capture Face", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("s") and len(faces) > 0:
        path = f"{SAVE_DIR}/me_{count}.jpg"
        cv2.imwrite(path, face_img)
        print(f"Saved {path}")
        count += 1

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()