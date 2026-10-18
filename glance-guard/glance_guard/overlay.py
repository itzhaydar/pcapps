from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from .windows import set_topmost

class PrivacyCover(QWidget):
    def __init__(self, screen, appearance, emergency):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        color = {"Midnight":"#101a2d", "Graphite":"#25262b", "Black":"#000000"}[appearance]
        self.setStyleSheet(f"background:{color}; color:#d9e4f7; font-family:Segoe UI; font-size:16px;")
        layout = QVBoxLayout(self)
        layout.addStretch()
        for text in ("◉", "GLANCE GUARD", "Your screen is concealed", "Look back to continue"):
            label=QLabel(text); label.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(label)
        button=QPushButton("Pause protection  •  Ctrl + Shift + G")
        button.clicked.connect(emergency)
        button.setStyleSheet("padding:14px; border:1px solid #52617b; border-radius:8px;")
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        self.setGeometry(screen.geometry())
        self.show()
        self.windowHandle().setScreen(screen)
        self.setGeometry(screen.geometry())
        set_topmost(self)

class Overlays:
    def __init__(self, settings, emergency):
        self.settings, self.emergency = settings, emergency
        self.windows = []
        self.active = False
        self.connected_screens = set()
        app=QApplication.instance()
        app.screenAdded.connect(self.refresh)
        app.screenRemoved.connect(self.refresh)
        self.refresh()

    def refresh(self, *_):
        for screen in QApplication.screens():
            if screen not in self.connected_screens:
                screen.geometryChanged.connect(self.refresh)
                self.connected_screens.add(screen)
        if self.active:
            self.set_visible(False)
            self.set_visible(True)

    def set_visible(self, visible):
        if self.active == visible:
            return
        self.active = visible
        if visible:
            screens = QApplication.screens() if self.settings.all_monitors else [QApplication.primaryScreen()]
            self.windows = [PrivacyCover(s, self.settings.appearance, self.emergency) for s in screens if s]
        else:
            for window in self.windows:
                window.close(); window.deleteLater()
            self.windows.clear()

    def maintain(self):
        for window in self.windows:
            set_topmost(window)
