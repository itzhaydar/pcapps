import logging
import time
from PySide6.QtCore import QThread, Signal
from .attention import Observation, Signal as AttentionSignal
from .vision import Detector

class CameraWorker(QThread):
    observation = Signal(object)
    status = Signal(str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        capture = detector = None
        try:
            import cv2
            import sys
            cv2.setNumThreads(1)
            detector = Detector(self.settings)
            while not self.isInterruptionRequested():
                if capture is None:
                    self.status.emit("Connecting to camera…")
                    capture = cv2.VideoCapture(self.settings.camera, cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY)
                    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    capture.set(cv2.CAP_PROP_FPS, self.settings.fps)
                started = time.monotonic()
                ok, frame = capture.read()
                if not ok:
                    self.observation.emit(Observation(AttentionSignal.FAILURE))
                    self.status.emit("Camera unavailable; retrying")
                    capture.release()
                    capture = None
                    # Repeat failures for the UI policy while waiting; no tight reconnect loop.
                    for _ in range(30):
                        if self.isInterruptionRequested():
                            break
                        self.msleep(100)
                    continue
                if frame.shape[1] > 640:
                    frame = cv2.resize(frame, (640, round(frame.shape[0]*640/frame.shape[1])))
                result = detector.analyze(frame, started)
                del frame
                self.observation.emit(result)
                self.status.emit("Camera connected • local processing")
                remaining = max(0, 1/self.settings.fps-(time.monotonic()-started))
                self.msleep(int(remaining*1000))
        except Exception as error:
            logging.exception("Camera processing stopped")
            self.status.emit(str(error))
            self.observation.emit(Observation(AttentionSignal.FAILURE))
        finally:
            if capture is not None:
                capture.release()
            if detector is not None:
                detector.close()
