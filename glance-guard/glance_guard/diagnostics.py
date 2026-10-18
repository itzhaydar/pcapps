"""Run with the installed dependencies and prepared assets (no webcam needed)."""
import time
import numpy as np
from PySide6.QtWidgets import QApplication
from glance_guard.settings import Settings
from glance_guard.vision import Detector, asset_path
from glance_guard.ui import Dashboard
from glance_guard.attention import Signal
from glance_guard.overlay import Overlays

def run():
    app=QApplication([])
    settings=Settings()
    window=Dashboard(settings)
    window.show(); app.processEvents()
    cover=Overlays(settings,lambda:None)
    cover.set_visible(True); app.processEvents()
    assert cover.windows
    cover.set_visible(False); app.processEvents()
    assert not cover.windows
    assert asset_path("icon.ico").exists()
    detector=Detector(settings)
    try:
        result=detector.analyze(np.full((480,640,3),128,dtype=np.uint8),time.monotonic())
        assert result.signal == Signal.MISSING
    finally:
        detector.close()
    window.hide()
    print("Qt dashboard, cover lifecycle, icon, and actual MediaPipe model load passed")
