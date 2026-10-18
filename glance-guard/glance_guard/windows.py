"""Documented Windows APIs; no key hooks or administrator rights."""
import ctypes
from ctypes import wintypes
import subprocess
import sys
from PySide6.QtCore import QAbstractNativeEventFilter

HOTKEY_ID = 0x4747
class EmergencyHotkey(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.registered = False
        if sys.platform == "win32":
            self.registered = bool(ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, 0x4000 | 0x2 | 0x4, 0x47))

    def nativeEventFilter(self, event_type, message):
        if sys.platform == "win32":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                self.callback()
                return True, 0
        return False, 0

    def close(self):
        if self.registered:
            ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
            self.registered = False

def set_topmost(widget):
    if sys.platform == "win32":
        user32 = ctypes.windll.user32
        user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.SetWindowPos(int(widget.winId()), -1, 0, 0, 0, 0, 0x1 | 0x2 | 0x10 | 0x40)

def set_startup(enabled):
    if sys.platform != "win32":
        if enabled:
            raise RuntimeError("Startup integration is available on Windows only")
        return
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        if enabled:
            if getattr(sys, "frozen", False):
                args = [sys.executable, "--tray"]
            else:
                from pathlib import Path
                pythonw = Path(sys.executable).with_name("pythonw.exe")
                args = [str(pythonw), str(Path(__file__).resolve().parent.parent / "main.py"), "--tray"]
            winreg.SetValueEx(key, "GlanceGuard", 0, winreg.REG_SZ, subprocess.list2cmdline(args))
        else:
            try:
                winreg.DeleteValue(key, "GlanceGuard")
            except FileNotFoundError:
                pass
