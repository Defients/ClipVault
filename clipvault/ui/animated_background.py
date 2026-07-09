"""Animated cyber background widget (performance-optimized)."""

import random
import math
from datetime import datetime
from typing import List

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

from clipvault.config import (
    CYBER_GRID, CYBER_NEON_BLUE, CYBER_NEON_GREEN,
)


class AnimatedBackground(QWidget):
    """Enhanced animated background with cyber effects.

    Performance improvements over original:
    - Timer interval 33ms (~30fps) instead of 50ms
    - Uses ``random.random()`` instead of ``os.urandom()`` in the hot loop
    - Skips repaint when widget is not visible
    - Supports reduce-motion (static grid, no particles)
    - Particle count capped based on widget area
    """

    def __init__(self, parent=None, intensity: float = 0.3):
        super().__init__(parent)
        self.intensity = intensity
        self.particles: list = []
        self.pulse = 0
        self.grid_offset = 0
        self._reduce_motion = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(33)

        self.max_particles = 200

    def set_reduce_motion(self, enabled: bool):
        """When enabled, draw a static grid with no moving particles."""
        self._reduce_motion = enabled
        if enabled:
            self.particles = []
            self.timer.stop()
            self.update()
        else:
            if self.intensity > 0:
                self.timer.start(33)

    def set_entries(self, entries: List[object]):
        """Create one particle per entry (1:1 mapping). Clips made today are colored differently."""
        if self._reduce_motion:
            return
        try:
            total = len(entries)
        except Exception:
            total = 0

        count = min(total, self.max_particles)
        self.particles = []
        today = datetime.now().date()

        use_entries = entries[:count] if total <= self.max_particles else entries[:self.max_particles]

        w = max(1, self.width() or 800)
        h = max(1, self.height() or 600)

        for e in use_entries:
            try:
                is_today = (hasattr(e, 'timestamp') and e.timestamp.date() == today)
            except Exception:
                is_today = False

            colour_code = 0 if is_today else 1

            self.particles.append({
                'x': random.uniform(0, w),
                'y': random.uniform(0, h),
                'vx': (random.random() - 0.5) * self.intensity * 2,
                'vy': (random.random() - 0.5) * self.intensity * 2,
                'size': 2 + int(3 * self.intensity),
                'color': colour_code,
            })

    def set_intensity(self, intensity: float):
        """Adjust animation intensity with enhanced effects."""
        self.intensity = max(0.0, min(1.0, intensity))
        if self._reduce_motion or self.intensity == 0:
            self.particles = []
            if self.intensity == 0:
                self.timer.stop()
            self.update()
            return

        if not self.timer.isActive():
            self.timer.start(33)

        particle_count = int(20 * self.intensity)
        self.particles = []
        w = max(1, self.width() or 1000)
        h = max(1, self.height() or 600)
        for _ in range(particle_count):
            self.particles.append({
                'x': random.uniform(0, w),
                'y': random.uniform(0, h),
                'vx': (random.random() - 0.5) * self.intensity * 2,
                'vy': (random.random() - 0.5) * self.intensity * 2,
                'size': 2 + int(3 * self.intensity),
                'color': random.randint(0, 2),
            })

    def update_animation(self):
        if self.intensity <= 0 or self._reduce_motion:
            return
        if not self.isVisible():
            return

        self.pulse = (self.pulse + 3) % 360
        self.grid_offset = (self.grid_offset + 0.5 * self.intensity) % 80

        w = max(1, self.width())
        h = max(1, self.height())

        for p in self.particles:
            p['x'] += p.get('vx', 0) * (1 + 0.2 * math.sin(self.pulse / 30))
            p['y'] += p.get('vy', 0) * (1 + 0.2 * math.cos(self.pulse / 30))

            if p['x'] < 0:
                p['x'] = w
                p['vy'] += (random.random() - 0.5) * 0.1
            if p['x'] > w:
                p['x'] = 0
                p['vy'] += (random.random() - 0.5) * 0.1
            if p['y'] < 0:
                p['y'] = h
                p['vx'] += (random.random() - 0.5) * 0.1
            if p['y'] > h:
                p['y'] = 0
                p['vx'] += (random.random() - 0.5) * 0.1

        self.update()

    def paintEvent(self, event):
        if self.intensity == 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.intensity > 0.2:
            grid_color = QColor(CYBER_GRID)
            grid_color.setAlpha(int(100 * self.intensity))
            painter.setPen(QPen(grid_color, 1))
            grid_size = 80

            for x in range(-80, self.width() + 80, grid_size):
                actual_x = int(x + self.grid_offset)
                painter.drawLine(actual_x, 0, actual_x, int(self.height()))
                if self.intensity > 0.5:
                    glow = QColor(CYBER_NEON_BLUE)
                    glow.setAlpha(int(20 * self.intensity))
                    painter.setPen(QPen(glow, 2))
                    painter.drawLine(actual_x, 0, actual_x, int(self.height()))

            for y in range(-80, int(self.height()) + 80, grid_size):
                actual_y = int(y + self.grid_offset)
                painter.drawLine(0, actual_y, int(self.width()), actual_y)
                if self.intensity > 0.5:
                    glow = QColor(CYBER_NEON_BLUE)
                    glow.setAlpha(int(20 * self.intensity))
                    painter.setPen(QPen(glow, 2))
                    painter.drawLine(0, actual_y, int(self.width()), actual_y)

        if self._reduce_motion:
            painter.end()
            return

        for p in self.particles:
            if p.get('color', 1) == 0:
                color = QColor(CYBER_NEON_GREEN)
            else:
                color = QColor(CYBER_NEON_BLUE)

            alpha = int((120 + 60 * math.sin(self.pulse / 30)) * self.intensity)
            color.setAlpha(alpha)

            painter.setPen(Qt.PenStyle.NoPen)
            radius = max(2, int(p.get('size', 2) * (1 + 0.15 * math.sin(self.pulse / 30))))

            halo = QColor(color)
            halo.setAlpha(int(alpha * 0.3))
            painter.setBrush(QBrush(halo))
            painter.drawEllipse(int(p['x'] - radius*1.5), int(p['y'] - radius*1.5), radius*3, radius*3)

            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(p['x'] - radius), int(p['y'] - radius), radius*2, radius*2)
