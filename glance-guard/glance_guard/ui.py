from dataclasses import replace
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFormLayout, QCheckBox, QDoubleSpinBox, QSpinBox, QComboBox, QGroupBox, QMessageBox)

class Dashboard(QWidget):
    applied = Signal(object)
    pause_requested = Signal()
    calibrate_requested = Signal()
    reset_requested = Signal()
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("Glance Guard")
        self.setMinimumSize(560, 600)
        self.resize(620, 740)
        self.setStyleSheet("""
            QWidget { background:#101724; color:#dfe8f7; font:10pt 'Segoe UI'; }
            QLabel#title { font:26pt 'Segoe UI'; font-weight:600; }
            QLabel#status { color:#8ee8c2; font:16pt 'Segoe UI'; }
            QGroupBox { border:1px solid #354259; border-radius:10px; margin-top:14px; padding:18px 12px 10px; }
            QGroupBox::title { subcontrol-origin:margin; left:12px; }
            QPushButton { background:#26364f; border:1px solid #405576; border-radius:7px; padding:10px; }
            QPushButton:hover { background:#354a6b; }
            QSpinBox,QDoubleSpinBox,QComboBox { background:#202d42; padding:5px; border:1px solid #405576; }
            QCheckBox { padding:3px; }
        """)
        outer=QVBoxLayout(self)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); outer.addWidget(scroll)
        content=QWidget(); scroll.setWidget(content)
        layout=QVBoxLayout(content); layout.setContentsMargins(24,20,24,20); layout.setSpacing(10)
        title=QLabel("Glance Guard"); title.setObjectName("title"); layout.addWidget(title)
        layout.addWidget(QLabel("Look away. Keep your work private."))
        card=QGroupBox("LIVE PROTECTION"); card_layout=QVBoxLayout(card)
        self.state=QLabel("Starting…"); self.state.setObjectName("status")
        self.camera=QLabel("Waiting for camera")
        self.attention=QLabel("Waiting for attention detection")
        self.pause=QPushButton("Pause protection"); self.pause.clicked.connect(self.pause_requested.emit)
        for widget in (self.state,self.camera,self.attention,self.pause): card_layout.addWidget(widget)
        layout.addWidget(card)
        group=QGroupBox("SETTINGS"); form=QFormLayout(group)
        self.controls={}
        for name,label,low,high,step in [
            ("sensitivity","Sensitivity",.5,2,.1),
            ("away_delay","Conceal after (seconds)",.1,10,.1),
            ("return_delay","Reveal after (seconds)",.1,5,.1)]:
            control=QDoubleSpinBox(); control.setRange(low,high); control.setSingleStep(step)
            control.setValue(getattr(settings,name)); form.addRow(label,control); self.controls[name]=control
        for name,label,low,high in [("camera","Webcam index (0 = default)",0,20),("fps","Analysis frames per second",3,20)]:
            control=QSpinBox(); control.setRange(low,high); control.setValue(getattr(settings,name))
            form.addRow(label,control); self.controls[name]=control
        control=QComboBox(); control.addItems(["Midnight","Graphite","Black"])
        control.setCurrentText(settings.appearance); form.addRow("Opaque cover color",control); self.controls["appearance"]=control
        for name,label in [("all_monitors","Cover all monitors (off = primary only)"),
            ("missing_face_protect","Conceal when no face is detected"),
            ("camera_failure_protect","Conceal when camera fails"),
            ("uncertain_protect","Conceal when detection is uncertain"),
            ("startup","Start with Windows")]:
            control=QCheckBox(label); control.setChecked(getattr(settings,name))
            form.addRow(control); self.controls[name]=control
        save=QPushButton("Apply settings"); save.clicked.connect(self.apply); form.addRow(save)
        layout.addWidget(group)
        row=QHBoxLayout()
        calibration=QPushButton("Calibrate attention…"); calibration.clicked.connect(self.calibrate_requested.emit)
        reset=QPushButton("Reset calibration"); reset.clicked.connect(self.reset_requested.emit)
        row.addWidget(calibration); row.addWidget(reset); layout.addLayout(row)
        self.calibration_status=QLabel("Calibration: " + ("saved on this device" if settings.calibration else "default thresholds"))
        layout.addWidget(self.calibration_status)
        note=QLabel("Emergency pause: Ctrl + Shift + G • Closing this window keeps protection in the tray.\n"
                    "Local processing only. Visual privacy does not prevent screen capture.")
        note.setWordWrap(True); layout.addWidget(note)

    def apply(self):
        values={}
        for name,control in self.controls.items():
            if isinstance(control,QCheckBox): values[name]=control.isChecked()
            elif isinstance(control,QComboBox): values[name]=control.currentText()
            else: values[name]=control.value()
        self.applied.emit(replace(self.settings,**values))

    def closeEvent(self,event):
        event.ignore(); self.hide()
