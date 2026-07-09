"""Paste ring — cycle through recent clipboard entries via repeated hotkey presses."""

import time
from typing import Callable, List, Optional

from PyQt6.QtWidgets import QLabel, QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont

from clipvault.config import (
    CYBER_BG_LIGHT, CYBER_NEON_BLUE, CYBER_TEXT, CYBER_TEXT_DIM,
    FONT_FAMILY, FONT_SIZE_SM,
)
from clipvault.models.entry import ClipboardEntry


class PasteRingOSD(QWidget):
    """On-screen display overlay showing current paste ring position."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(400)
        self.setFixedHeight(50)

        self._container = QWidget(self)
        self._container.setStyleSheet(f"""
            QWidget {{
                background: {CYBER_BG_LIGHT}ee;
                border: 2px solid {CYBER_NEON_BLUE}66;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._container)

        inner = QVBoxLayout(self._container)
        inner.setContentsMargins(16, 8, 16, 8)

        self._label = QLabel("")
        self._label.setStyleSheet(
            f"color: {CYBER_TEXT}; font-family: {FONT_FAMILY}; font-size: {FONT_SIZE_SM}px;"
        )
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(self._label)

        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(200)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._hide_fade)

    def show_message(self, text: str):
        self._label.setText(text)
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 60
        self.move(x, y)
        self.setWindowOpacity(0)
        self.show()
        self._fade_anim.stop()
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()
        self._hide_timer.start(2000)

    def _hide_fade(self):
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self.hide)
        self._fade_anim.start()


class PasteRing:
    """Cycle through clipboard entries by repeatedly calling next().

    Each call to ``next()`` advances the index and returns the current entry.
    The session auto-expires after ``timeout`` seconds of inactivity.
    """

    def __init__(self, entries_provider: Callable[[], List[ClipboardEntry]],
                 timeout: int = 10, enabled: bool = True):
        self._provider = entries_provider
        self._timeout = timeout
        self._enabled = enabled
        self._index = 0
        self._snapshot: List[ClipboardEntry] = []
        self._last_call_time: float = 0
        self._osd = None

    def set_timeout(self, timeout: int):
        self._timeout = timeout

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    def active(self) -> bool:
        return len(self._snapshot) > 0 and self._is_valid()

    def _is_valid(self) -> bool:
        if not self._snapshot:
            return False
        if self._timeout > 0:
            elapsed = time.monotonic() - self._last_call_time
            if elapsed > self._timeout:
                return False
        return True

    def start_cycle(self):
        self._snapshot = [e for e in self._provider() if not e.image_data]
        self._index = 0
        self._last_call_time = time.monotonic()

    def next(self) -> Optional[ClipboardEntry]:
        if not self._enabled:
            return None

        if not self._is_valid():
            self.start_cycle()
            if not self._snapshot:
                return None

        self._index = (self._index + 1) % len(self._snapshot)
        self._last_call_time = time.monotonic()

        entry = self._snapshot[self._index]
        self._show_osd(entry)
        return entry

    def prev(self) -> Optional[ClipboardEntry]:
        if not self._enabled:
            return None

        if not self._is_valid():
            self.start_cycle()
            if not self._snapshot:
                return None

        self._index = (self._index - 1) % len(self._snapshot)
        self._last_call_time = time.monotonic()

        entry = self._snapshot[self._index]
        self._show_osd(entry)
        return entry

    def reset(self):
        self._snapshot = []
        self._index = 0
        if self._osd is not None:
            self._osd.hide()

    def _show_osd(self, entry: ClipboardEntry):
        if self._osd is None:
            try:
                from PyQt6.QtWidgets import QApplication
                if QApplication.instance() is None:
                    return
                self._osd = PasteRingOSD()
            except Exception:
                return
        pos = self._index + 1
        total = len(self._snapshot)
        preview = entry.preview(40)
        self._osd.show_message(f"[{pos}/{total}]  {preview}")
