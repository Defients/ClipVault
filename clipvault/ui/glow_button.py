"""Glow button widget with hover-only glow effects (performance-optimized)."""

from PyQt6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor, QFont

from clipvault.config import CYBER_NEON_BLUE, FONT_FAMILY, FONT_SIZE_BASE


class GlowButton(QPushButton):
    """Enhanced button with static glow that intensifies on hover.

    The continuous pulse timer from the original implementation has been
    removed — it rebuilt the entire QSS string and recreated the shadow
    effect every 50ms even when the button was idle.  Glow is now a
    static effect that animates only on hover enter/leave.
    """

    def __init__(self, text, color=CYBER_NEON_BLUE, parent=None,
                 glow_intensity=1.0, tooltip='', accessible_name=''):
        super().__init__(text, parent)
        self.glow_color = color
        self.glow_intensity = glow_intensity
        self._reduce_motion = False

        try:
            self.setText(text.upper())
        except Exception:
            self.setText(text)

        if tooltip:
            self.setToolTip(tooltip)
        if accessible_name:
            self.setAccessibleName(accessible_name)

        self._setup_style()
        if glow_intensity > 0:
            self._setup_glow()

        self._glow_anim = QPropertyAnimation(self, b"glowBlur")
        self._glow_anim.setDuration(180)
        self._glow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.enterEvent = self._on_enter
        self.leaveEvent = self._on_leave

    def _setup_style(self):
        base_alpha = int(40 * self.glow_intensity)

        light_color = QColor(self.glow_color)
        light_color.setAlpha(255)
        h, s, l, _ = light_color.getHslF()
        light_color.setHslF(h, s * 0.8, min(1.0, l * 1.5), 1.0)
        light_hex = light_color.name()

        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.glow_color}{base_alpha:02x},
                    stop:0.4 {self.glow_color}{int(base_alpha/1.5):02x},
                    stop:1 {self.glow_color}{int(base_alpha/2):02x});
                color: {light_hex};
                border: 2px solid {self.glow_color};
                border-radius: 12px;
                padding: 10px 20px;
                font-size: {FONT_SIZE_BASE}px;
                font-weight: bold;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:pressed {{
                background: {self.glow_color}{int(base_alpha*2.5):02x};
            }}
            QPushButton:disabled {{
                color: {CYBER_NEON_BLUE}66;
                border-color: {CYBER_NEON_BLUE}33;
                background: {CYBER_NEON_BLUE}11;
            }}
        """)

        font = self.font()
        try:
            font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        except Exception:
            pass
        self.setFont(font)

    def _setup_glow(self):
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(self.glow_color))
        base_blur = max(1, int(20 * self.glow_intensity))
        glow.setBlurRadius(base_blur)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
        self._glow_blur = base_blur

    def getGlowBlur(self) -> int:
        eff = self.graphicsEffect()
        try:
            return int(eff.blurRadius()) if eff is not None else 0
        except Exception:
            return getattr(self, '_glow_blur', 0)

    def setGlowBlur(self, value: int):
        eff = self.graphicsEffect()
        try:
            if eff is not None:
                eff.setBlurRadius(int(value))
                self._glow_blur = int(value)
        except Exception:
            self._glow_blur = int(value)

    glowBlur = pyqtProperty(int, fget=getGlowBlur, fset=setGlowBlur)

    def set_glow_intensity(self, intensity: float):
        self.glow_intensity = intensity
        self._setup_style()
        if intensity > 0:
            self._setup_glow()
        else:
            self.setGraphicsEffect(None)

    def set_reduce_motion(self, enabled: bool):
        self._reduce_motion = enabled
        if enabled:
            self._glow_anim.setDuration(0)
            if self.glow_intensity > 0:
                eff = self.graphicsEffect()
                if eff:
                    eff.setBlurRadius(max(1, int(10 * self.glow_intensity)))
        else:
            self._glow_anim.setDuration(180)

    def _on_enter(self, event):
        if self.glow_intensity > 0 and not self._reduce_motion:
            glow = self.graphicsEffect()
            if glow:
                start = glow.blurRadius()
                end = int(30 * self.glow_intensity)
                self._glow_anim.stop()
                self._glow_anim.setStartValue(start)
                self._glow_anim.setEndValue(end)
                self._glow_anim.start()

    def _on_leave(self, event):
        if self.glow_intensity > 0 and not self._reduce_motion:
            glow = self.graphicsEffect()
            if glow:
                start = glow.blurRadius()
                end = max(1, int(20 * self.glow_intensity))
                self._glow_anim.stop()
                self._glow_anim.setStartValue(start)
                self._glow_anim.setEndValue(end)
                self._glow_anim.start()
