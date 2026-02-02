import face_recognition
import os
import pickle

KNOWN_DIR = "data/known_faces"
ENCODING_FILE = "data/me_encoding.pkl"

encodings = []

for file in os.listdir(KNOWN_DIR):
    if not file.endswith(".jpg"):
        continue

    path = os.path.join(KNOWN_DIR, file)
    image = face_recognition.load_image_file(path)

    face_encs = face_recognition.face_encodings(image)

    if len(face_encs) == 1:
        encodings.append(face_encs[0])
        print(f"Encoded {file}")
    else:
        print(f"Skipped {file} (no face of multiple faces)")

if not encodings:
    raise RuntimeError("No valid face encodings found")

with open(ENCODING_FILE, "wb") as f:
    pickle.dump(encodings, f)

print(f"Saved encoding to {ENCODING_FILE}")