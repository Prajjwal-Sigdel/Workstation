import os

def face_recognition_model_location(model_name=None):
    if model_name is None:
        model_name = "dlib_face_recognition_resnet_model_v1.dat"
    return os.path.join(os.path.dirname(__file__), "models", model_name)

def pose_predictor_model_location():
    return face_recognition_model_location("shape_predictor_68_face_landmarks.dat")

def pose_predictor_five_point_model_location():
    return face_recognition_model_location("shape_predictor_5_face_landmarks.dat")

def face_recognition_model_v1_location():
    return face_recognition_model_location("dlib_face_recognition_resnet_model_v1.dat")

def cnn_face_detector_model_location():
    return face_recognition_model_location("mmod_human_face_detector.dat")