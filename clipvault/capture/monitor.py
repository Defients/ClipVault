"""Clipboard monitor thread — text + image support."""

import time
import base64
import hashlib
import platform
from typing import Dict, Any

import pyperclip
from PyQt6.QtCore import QThread, pyqtSignal, QBuffer, QIODevice
from PyQt6.QtGui import QImage

from clipvault.config import MAX_CLIPBOARD_SIZE, MONITOR_INTERVAL
from clipvault.capture.filters import should_capture
from clipvault.utils import setup_logger

_log = setup_logger("clipvault.monitor")

MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB encoded


def _get_active_window_title() -> str:
    """Return the title of the currently focused window (best-effort)."""
    system = platform.system()
    try:
        if system == "Windows":
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                return buf.value
        elif system == "Darwin":
            try:
                from AppKit import NSWorkspace
                app = NSWorkspace.sharedWorkspace().frontmostApplication()
                return app.localizedName() or ""
            except ImportError:
                pass
        elif system == "Linux":
            try:
                import subprocess
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True, text=True, timeout=1,
                )
                return result.stdout.strip()
            except Exception:
                pass
    except Exception:
        pass
    return ""


class ClipboardMonitor(QThread):
    """Enhanced clipboard monitor with filtering and image support."""

    new_entry = pyqtSignal(str)
    new_image_entry = pyqtSignal(str, str)  # (placeholder_text, base64_png)

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.running = True
        self.last_text = ""
        self.last_image_hash = ""
        self.paused = False

    def run(self):
        while self.running:
            if not self.paused and not self.config.get('pause_capture', False):
                try:
                    self._poll_clipboard()
                except Exception as e:
                    _log.debug("Monitor poll error: %s", e)
            time.sleep(MONITOR_INTERVAL / 1000)

    def _poll_clipboard(self):
        from PyQt6.QtWidgets import QApplication
        clip = QApplication.clipboard()
        if clip is None:
            return

        # Check for image first
        image = clip.image()
        if not image.isNull():
            self._handle_image(image)
            return

        # Fall back to text
        current = pyperclip.paste()
        if current and current != self.last_text and len(current) < MAX_CLIPBOARD_SIZE:
            source_app = _get_active_window_title()
            if should_capture(current, self.config, source_app):
                self.last_text = current
                self.new_entry.emit(current)

    def _handle_image(self, image: QImage):
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buf, "PNG")
        raw = bytes(buf.data())
        buf.close()

        img_hash = hashlib.md5(raw).hexdigest()
        if img_hash == self.last_image_hash:
            return
        self.last_image_hash = img_hash

        if len(raw) > MAX_IMAGE_SIZE:
            _log.info("Image too large (%d bytes), skipping", len(raw))
            return

        b64 = base64.b64encode(raw).decode("ascii")
        timestamp = time.strftime("%H:%M:%S")
        placeholder = f"[Image captured at {timestamp}]"
        self.new_image_entry.emit(placeholder, b64)

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False
