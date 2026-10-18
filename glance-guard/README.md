# Glance Guard

A Python Windows desktop utility that conceals your displays when local webcam analysis indicates you have looked away. This first implementation uses head orientation **and iris position**, not face presence alone. Webcam gaze is approximate; calibrate and test it on your own camera before relying on it.

## Download / build

The Windows build runs in the repository's **Actions → Build Glance Guard** workflow when these files change, or manually through **Run workflow**. After a successful run, download **GlanceGuard-Windows**, extract it completely, then double-click `GlanceGuard/GlanceGuard.exe`. Keep the `_internal` folder alongside the EXE. Python is not required on the destination PC. Artifacts require a GitHub login to download and expire after 30 days. The application is portable, unsigned, and requires no administrator rights.

An EXE has **not** been generated or verified in the Linux development environment. A workflow configuration is not evidence of a successful Windows build; check its actual result. Windows webcam and desktop behavior require the manual acceptance checks below.

To build yourself on Windows 10/11 x64, install CPython 3.12 x64, open PowerShell in this folder, and run:

```powershell
powershell -ExecutionPolicy Bypass -File tools/build.ps1
```

The build downloads dependencies and Google's versioned face-landmarker model once, generates the icon, runs automated tests, and packages `dist/GlanceGuard/GlanceGuard.exe`. The entire output folder works offline. `assets/face_landmarker.sha256` records the downloaded model digest; it is an audit record, not an independently pinned authenticity check. Assets come over verified HTTPS from Google's official model URL. Do not replace models from untrusted sources.

## Run from Python

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python tools/prepare_assets.py
.venv\Scripts\python main.py
```

Use `.venv\Scripts\pythonw.exe main.py` to run without a terminal. No Node.js or cloud service is used. Dependency ranges target current MediaPipe Tasks and Qt APIs; the build workflow records exact installed versions in the artifact. Upgrades still require validation.

## Use

1. Allow desktop applications to access your camera in Windows Settings → Privacy & security → Camera. Close apps holding the webcam exclusively.
2. Protection starts automatically. Close the dashboard to keep it in the system tray; double-click the tray icon to reopen it.
3. Look away for the confirmation delay to conceal the screen; look back to reveal it. Default delays are 0.8 seconds away and 0.3 seconds returning, plus sampling and inference latency.
4. **Ctrl+Shift+G immediately pauses protection.** The cover also has a pause button. Resume from the tray or dashboard. If the shortcut cannot be registered, Windows protection stays paused until you resolve the conflict and restart.
5. Calibration is optional and explicitly asks permission to save four numeric offsets locally. Look at screen center for five seconds; an unstable sample is rejected. No face images are stored. Reset calibration from the dashboard.
6. Select a different webcam using its OpenCV index (0 normally means the built-in camera). Camera ordering can change after reconnecting. Apply settings to reconnect.
7. Enable Windows startup in settings to create a per-user Run entry, with a tray-only launch. Source launches reference your current virtual environment and project path, so do not move them after enabling startup.

All monitors are covered by default. The primary-only option deliberately leaves other monitors visible. Appearance choices are fully opaque colors; there is no insecure translucent mode. Closing your eyes longer than a brief blink also conceals the screen. Face loss, uncertain analysis, and camera failure each have configurable conceal policies. A disconnected camera is retried every three seconds. Initialization/model errors stay visible until Pause/Resume retries.

## Privacy and limits

Frames stay in memory for local processing; no recording, image saving, account, telemetry, screen capture, keyboard hook, or runtime network request is implemented. The Windows shortcut uses `RegisterHotKey`, not keyboard monitoring. Settings, four optional calibration offsets, and rotating diagnostic error logs live in `%LOCALAPPDATA%/GlanceGuard`. Error logs do not contain frames or facial landmarks.

This is visual privacy against casual observation. It does not lock Windows, authenticate a face, distinguish an owner from another person, prevent screenshots or remote capture, cover the UAC secure desktop, or guarantee coverage of exclusive fullscreen applications or other topmost windows. Another visible face may be treated as attentive. Use Windows lock for access control. Ordinary desktop windows are covered with opaque topmost windows; monitor layout changes rebuild the covers, and topmost positioning is refreshed while active.

Qt was chosen for reliable per-screen geometry, tray support, native events, and UI threading. It has a larger baseline footprint than native Win32; modest resource use on 4 GB PCs is a target, not a measured claim. OpenCV handles a single 640×480 camera stream with a default 10 analyses/second, one processing thread, and no queued frame history. MediaPipe VIDEO mode provides tracking. EMA smoothing, spatial hysteresis, separate confirmation delays, and a 450 ms blink grace period reduce flicker. Low mean brightness is treated as uncertain. Thresholds are heuristic; glasses, glare, camera angle, eyelid shape, multi-monitor viewing, and lighting can reduce accuracy.

See [RESEARCH.md](RESEARCH.md) for the implementation sources and tradeoffs.

## Automated verification

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python -m compileall -q glance_guard main.py tools tests
```

Pure tests cover head/eye directions, calibration offsets, delays, interrupted transitions, blink handling, fail-safe choices, and settings validation/persistence. They do not establish actual vision accuracy. The Windows CI also loads the actual bundled model against a blank image and starts a Qt offscreen smoke test.

## Windows acceptance checklist (not yet verified on hardware)

Use a nonsensitive test document on each display. Keep the emergency shortcut available. Record hardware, Windows version, camera model, dependency versions, delays, and outcomes.

| Check | Expected result |
|---|---|
| Look at center, read naturally, brief blinks | Clear screen; no repeated flicker |
| Look left/right/up/down with head still | Conceal after delay; adjust sensitivity/calibrate if inaccurate |
| Turn head left/right, look at phone or desk | Conceal after delay |
| Close eyes for >1.3 seconds | Conceal; brief blinks remain clear |
| Walk out of camera view, then return | Conceal on face loss, reveal on stable attention |
| Dim lighting / covered lens | Follow uncertain/no-face policy |
| Disconnect/reconnect webcam | Follow camera failure policy; reconnect automatically |
| Change webcam index | Release old device and open selected device |
| Add/remove monitor, negative coordinates, mixed DPI | Cover every selected display after geometry change |
| Alt-Tab, desktop fullscreen, exclusive fullscreen | Verify coverage; record exclusive fullscreen exceptions |
| Pause/resume, emergency shortcut, exit under cover | Remove all covers; release camera; resume detection |
| Enable startup, sign out/in, disable startup | Tray launch on next login only while enabled |
| Turn network off after installation | Fully operational without downloads |
| Force camera read to stall | Failure cover after stale signal; emergency pause stays responsive |

Measure idle, looking, concealed, paused, and reconnect states for 60 seconds each on the target low-end PC:

```powershell
.venv\Scripts\python tools/profile_runtime.py <PID> --seconds 60
```

The tool reports process CPU (100% = one logical core) and peak resident memory. No Windows CPU/RAM measurements are available yet. Native camera driver calls can block; pause removes covers immediately but device release waits for the current read, and exit waits for the worker rather than killing it unsafely. Test your driver specifically.

## Troubleshooting / uninstall

- Missing model: run `tools/prepare_assets.py` at build time. Source runtime never silently downloads it.
- Wrong conceal behavior: improve lighting, calibrate with your usual posture, reduce sensitivity, or increase away delay. Test across your actual monitor viewing angles.
- Camera busy/unavailable: check privacy permission, close conferencing apps, try another index, and Pause/Resume.
- Cover stuck: Ctrl+Shift+G or its pause button. The tray also provides Pause and Exit. Do not enable startup until acceptance checks pass.
- No tray on an unusual desktop: the dashboard is shown at launch. Windows Explorer tray support is the intended target.
- To uninstall: disable startup, Exit from tray, delete the portable app folder, and optionally delete `%LOCALAPPDATA%/GlanceGuard`. If the app was already deleted, remove `GlanceGuard` from `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.

## Third-party notices

MediaPipe and its model are Google components; Qt/PySide6, OpenCV, NumPy, Pillow, PyInstaller, and psutil retain their respective licenses. The workflow includes installed distribution license metadata with the portable build. PySide6 is dynamically bundled; retain the Qt libraries and notices when distributing, and review the applicable LGPL/commercial terms. See [Qt licensing](https://doc.qt.io/qtforpython-6/licenses.html) and [MediaPipe repository](https://github.com/google-ai-edge/mediapipe).
