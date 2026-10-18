"""Local-only MediaPipe Tasks analysis; frames never leave this module's caller."""
import math
from pathlib import Path
import sys
from .attention import Classifier, Observation, Signal

def asset_path(name):
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "assets" / name

class Detector:
    def __init__(self, settings):
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        self.mp = mp
        self.classifier = Classifier(settings)
        model = asset_path("face_landmarker.task")
        if not model.exists():
            raise RuntimeError("Missing local face model. Run python tools/prepare_assets.py before launching.")
        self.model = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model)),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1, min_face_detection_confidence=.6,
            min_face_presence_confidence=.6, min_tracking_confidence=.6,
            output_facial_transformation_matrixes=True))
        self.timestamp = 0

    def analyze(self, frame, now):
        import cv2
        import numpy as np
        if float(frame.mean()) < 28:
            return Observation(Signal.UNCERTAIN)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.timestamp = max(self.timestamp + 1, int(now*1000))
        result = self.model.detect_for_video(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb), self.timestamp)
        if not result.face_landmarks:
            self.classifier.smoothed = None
            return Observation(Signal.MISSING)
        points = result.face_landmarks[0]
        if len(points) < 478 or not result.facial_transformation_matrixes:
            return Observation(Signal.UNCERTAIN)
        rotation = np.asarray(result.facial_transformation_matrixes[0])[:3,:3]
        # Normalize scale out of the face transform before extracting Euler angles.
        rotation = rotation / np.linalg.norm(rotation, axis=0)
        pitch = math.degrees(math.atan2(rotation[2,1], rotation[2,2]))
        yaw = math.degrees(math.atan2(-rotation[2,0], math.hypot(rotation[0,0], rotation[1,0])))
        h,w = frame.shape[:2]
        def pt(i):
            return np.array([points[i].x*w, points[i].y*h])
        def eye(a,b,top,bottom,iris):
            left,right = sorted((pt(a), pt(b)), key=lambda p:p[0])
            axis = right-left
            width = float(np.linalg.norm(axis))
            if width < 6:
                raise ValueError("Eye too small")
            horizontal = float(np.dot(pt(iris)-left, axis)/(width*width))
            upper,lower=pt(top),pt(bottom)
            vertical_axis=lower-upper
            height=float(np.linalg.norm(vertical_axis))
            vertical=float(np.dot(pt(iris)-upper,vertical_axis)/max(height*height,1))
            return horizontal,vertical,height/width
        try:
            e1=eye(33,133,159,145,468)
            e2=eye(362,263,386,374,473)
        except ValueError:
            return Observation(Signal.UNCERTAIN)
        features=(yaw,pitch,(e1[0]+e2[0])/2,(e1[1]+e2[1])/2)
        return self.classifier.classify(features, blink=min(e1[2],e2[2]) < .13)

    def close(self):
        self.model.close()
