# Implementation research — 18 October 2026

Primary sources consulted before implementation:

- [MediaPipe Python Face Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python): Tasks VIDEO mode, local model files, landmarks, transformation matrices. [Official implementation](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/tasks/python/vision/face_landmarker.py) and [tests](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/tasks/python/test/vision/face_landmarker_test.py) provide reference API usage. Use one face, CPU, bounded sampling, and derive approximate iris ratios plus head rotation. This is not a calibrated eye tracker or identity verifier.
- [Official model URL usage](https://github.com/google-ai-edge/mediapipe-samples-web/blob/main/src/tasks/face-landmarker.ts): use Google's versioned float16/1 task asset during build, bundle it for offline runtime. Do not use network models during operation.
- [MediaPipe Windows wheels](https://pypi.org/project/mediapipe/0.10.32/): Windows x64 wheel available. Target Python 3.12 and MediaPipe Tasks rather than the removed legacy solutions interface.
- [Qt system tray](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSystemTrayIcon.html): supported Windows tray actions and activation. Qt event-loop UI and worker-thread camera analysis keep independent responsibilities.
- [DwmEnableBlurBehindWindow](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/nf-dwmapi-dwmenableblurbehindwindow): Microsoft documents that the old API no longer yields blur beginning with Windows 8. Aesthetic backdrop APIs do not establish unreadability. Choose opaque covers rather than screenshots or undocumented composition APIs.
- [SetWindowPos](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos): topmost ordinary desktop coverage without activation. No claim of secure-desktop or exclusive-fullscreen coverage.
- [RegisterHotKey](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey): system-wide emergency pause without keyboard hooks; reject a registration conflict before enabling protection.
- [PyInstaller manual](https://pyinstaller.org/en/stable/): build Windows executables on Windows, not Linux. Use a windowed onedir build so loading is predictable and Qt remains dynamically bundled.

Qt is heavier than a hand-written Win32 GUI, but consolidates tray, mixed-DPI screen geometry, settings widgets, signals, and native event handling. This is a reliability tradeoff; memory and CPU must be measured on target hardware. No unsupported low-resource performance claim is made.

Security boundaries: opaque windows conceal local pixels only. They are not a lock screen, capture protection, or owner authentication. Numeric calibration requires explicit consent, with reset support. No application runtime networking or telemetry exists.
