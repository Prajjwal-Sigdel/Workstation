import cv2

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Could not open camera !!!")

print("Camera running. Press 'q' to quit.")

face_present_frames = 0
FACE_THRESHOLD = 3

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame,1)
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=7,
        minSize=(60,60)
    )

    if len(faces)>0:
        face_present_frames += 1
    else:
        face_present_frames = 0

    if face_present_frames >= FACE_THRESHOLD:
        for (x ,y ,w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 225, 0), 2)

    cv2.imshow("Phase 1 - Face Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()