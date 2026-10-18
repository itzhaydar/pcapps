import logging
from logging.handlers import RotatingFileHandler
import statistics
import sys
import time
from dataclasses import replace
from PySide6.QtCore import QTimer, QLockFile, QStandardPaths
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from .attention import AttentionPolicy, Observation, Signal
from .camera import CameraWorker
from .overlay import Overlays
from .settings import Settings, data_directory
from .ui import Dashboard
from .vision import asset_path
from .windows import EmergencyHotkey, set_startup

class Controller:
    def __init__(self, app, settings, path):
        self.app, self.settings, self.path = app, settings, path
        self.paused = False
        self.quitting = False
        self.worker = None
        self.restarting = False
        self.last_observation = Observation(Signal.FAILURE)
        self.last_received = time.monotonic()
        self.policy = AttentionPolicy(settings)
        self.calibrating_until = None
        self.samples = []
        self.window = Dashboard(settings)
        self.window.pause_requested.connect(self.toggle)
        self.window.applied.connect(self.apply)
        self.window.calibrate_requested.connect(self.calibrate)
        self.window.reset_requested.connect(self.reset_calibration)
        self.overlays = Overlays(settings, self.pause)
        self.tray = QSystemTrayIcon(QIcon(str(asset_path("icon.ico"))), app)
        menu = QMenu()
        for label,callback in [("Dashboard / Settings",self.show), ("Pause",self.pause),
                               ("Resume",self.resume), ("Exit",self.exit)]:
            action=QAction(label,menu); action.triggered.connect(callback); menu.addAction(action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.show() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.tray.show()
        self.hotkey=EmergencyHotkey(self.pause)
        app.installNativeEventFilter(self.hotkey)
        self.timer=QTimer(); self.timer.timeout.connect(self.tick); self.timer.start(100)
        if sys.platform == "win32" and not self.hotkey.registered:
            self.paused=True
            self.window.state.setText("Paused: emergency shortcut unavailable")
            self.show()
            QMessageBox.warning(self.window,"Shortcut unavailable",
                "Ctrl+Shift+G is already in use. Close the conflicting application and restart Glance Guard. Protection stays paused.")
        else:
            self.start_worker()

    def show(self):
        self.window.show(); self.window.raise_(); self.window.activateWindow()

    def start_worker(self):
        if self.paused or self.quitting or self.restarting:
            return
        self.last_received=time.monotonic()
        self.last_observation=Observation(Signal.FAILURE)
        self.worker=CameraWorker(self.settings)
        self.worker.observation.connect(self.receive)
        self.worker.status.connect(self.window.camera.setText)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def worker_finished(self):
        if self.quitting:
            self.app.quit()
        elif self.restarting:
            self.restarting=False
            self.start_worker()
        # A detector initialization failure remains explicit; Resume retries it.

    def receive(self, observation):
        if self.paused or self.quitting or self.restarting:
            return
        self.last_received=time.monotonic()
        self.last_observation=observation
        self.window.attention.setText(observation.signal.value)
        if self.calibrating_until and observation.features is not None:
            self.samples.append(observation.features)

    def tick(self):
        if self.quitting or self.paused:
            return
        now=time.monotonic()
        if self.calibrating_until:
            remaining=self.calibrating_until-now
            self.window.calibration_status.setText(f"Look at screen center • {max(0,remaining):.0f}s remaining")
            if remaining <= 0:
                self.calibrating_until=None
                if len(self.samples) >= 15 and all(statistics.pstdev(column) < limit
                    for column,limit in zip(zip(*self.samples),(5,5,.06,.08))):
                    baseline=[statistics.median(column) for column in zip(*self.samples)]
                    updated=replace(self.settings,calibration=baseline)
                    if self.apply(updated):
                        self.window.calibration_status.setText("Calibration saved on this device")
                else:
                    self.window.calibration_status.setText("Calibration failed: keep face visible and gaze steady; try again")
                self.samples.clear()
            return
        observation=self.last_observation
        if now-self.last_received > 2:
            observation=Observation(Signal.FAILURE)
        covered=self.policy.update(observation,now)
        self.overlays.set_visible(covered)
        self.overlays.maintain()
        text="Screen concealed" if covered else "Protection enabled"
        self.window.state.setText(text)
        self.tray.setToolTip("Glance Guard • " + text)

    def pause(self):
        self.paused=True
        self.calibrating_until=None; self.samples.clear()
        self.overlays.set_visible(False)
        self.policy=AttentionPolicy(self.settings)
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
        self.window.state.setText("Protection paused")
        self.window.pause.setText("Resume protection")
        self.tray.setToolTip("Glance Guard • paused")

    def resume(self):
        if sys.platform == "win32" and not self.hotkey.registered:
            return
        if not self.paused and self.worker and self.worker.isRunning():
            return
        self.paused=False
        self.window.pause.setText("Pause protection")
        self.policy=AttentionPolicy(self.settings)
        if self.worker and self.worker.isRunning():
            self.restarting=True
        else:
            self.start_worker()

    def toggle(self):
        self.resume() if self.paused else self.pause()

    def apply(self, settings):
        old=self.settings
        try:
            settings.validate()
            set_startup(settings.startup)
            settings.save(self.path)
        except Exception as error:
            try:
                set_startup(old.startup)
            except Exception:
                logging.exception("Could not restore startup setting")
            QMessageBox.warning(self.window,"Could not save settings",str(error))
            return False
        self.settings=settings
        self.window.settings=settings
        self.overlays.set_visible(False)
        self.overlays.settings=settings
        self.policy=AttentionPolicy(settings)
        if self.worker and self.worker.isRunning():
            self.restarting=not self.paused
            self.worker.requestInterruption()
        elif not self.paused:
            self.start_worker()
        return True

    def calibrate(self):
        if self.paused or not self.worker or not self.worker.isRunning():
            QMessageBox.information(self.window,"Resume first","Resume protection and connect a webcam before calibrating.")
            return
        result=QMessageBox.question(self.window,"Calibrate attention",
            "For the next 5 seconds, look steadily at the center of your screen. The cover is temporarily disabled. "
            "Save four numeric head/eye offsets locally? No images or video will be saved.")
        if result != QMessageBox.StandardButton.Yes:
            return
        self.overlays.set_visible(False)
        self.samples=[]
        self.calibrating_until=time.monotonic()+5

    def reset_calibration(self):
        if self.apply(replace(self.settings,calibration=None)):
            self.window.calibration_status.setText("Calibration reset to default thresholds")

    def exit(self):
        self.quitting=True
        self.timer.stop()
        self.overlays.set_visible(False)
        self.hotkey.close()
        self.tray.hide()
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.window.state.setText("Releasing camera…")
        else:
            self.app.quit()

def main():
    app=QApplication(sys.argv)
    app.setApplicationName("Glance Guard")
    app.setQuitOnLastWindowClosed(False)
    folder=data_directory(); folder.mkdir(parents=True,exist_ok=True)
    lock=QLockFile(str(folder / "instance.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(None,"Glance Guard","Glance Guard is already running. Open it from the system tray.")
        return 0
    handler=RotatingFileHandler(folder / "glance-guard.log",maxBytes=200_000,backupCount=2,encoding="utf-8")
    logging.basicConfig(handlers=[handler],level=logging.WARNING)
    try:
        settings=Settings.load(folder / "settings.json")
    except (ValueError,TypeError,OSError) as error:
        QMessageBox.warning(None,"Settings reset",f"Could not load settings: {error}. Defaults will be used.")
        settings=Settings()
    controller=Controller(app,settings,folder / "settings.json")
    app.setWindowIcon(QIcon(str(asset_path("icon.ico"))))
    if "--tray" not in sys.argv or not QSystemTrayIcon.isSystemTrayAvailable():
        controller.show()
    result=app.exec()
    controller.hotkey.close()
    lock.unlock()
    return result
