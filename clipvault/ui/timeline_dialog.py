"""Timeline / calendar view dialog showing entries grouped by day with heatmap."""

from collections import Counter
from datetime import datetime, date
from typing import List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCalendarWidget,
    QListWidget, QListWidgetItem, QPushButton, QSplitter, QWidget,
)
from PyQt6.QtCore import Qt, QDate

from clipvault.config import (
    APP_NAME, CYBER_BG, CYBER_BG_LIGHT, CYBER_NEON_BLUE, CYBER_NEON_GREEN,
    CYBER_TEXT, CYBER_TEXT_DIM, FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_XS,
    SPACING_SM, SPACING_MD,
)
from clipvault.models.entry import ClipboardEntry
from clipvault.ui.entry_widget import _relative_time


class TimelineDialog(QDialog):
    """Calendar view with capture-frequency heatmap and per-day entry list."""

    def __init__(self, entries: List[ClipboardEntry], parent=None):
        super().__init__(parent)
        self._entries = entries
        self.setWindowTitle(f"{APP_NAME} — Timeline")
        self.setMinimumSize(700, 500)
        self.setStyleSheet(f"""
            QDialog {{
                background: {CYBER_BG};
            }}
            QLabel {{
                color: {CYBER_TEXT};
                font-family: {FONT_FAMILY};
            }}
            QCalendarWidget {{
                background: {CYBER_BG_LIGHT};
                color: {CYBER_TEXT};
                border: 1px solid {CYBER_NEON_BLUE}44;
                border-radius: 8px;
            }}
            QCalendarWidget QAbstractItemView {{
                background: {CYBER_BG_LIGHT};
                color: {CYBER_TEXT};
                selection-background-color: {CYBER_NEON_BLUE}66;
                selection-color: {CYBER_TEXT};
            }}
            QCalendarWidget QToolButton {{
                color: {CYBER_NEON_BLUE};
                background: transparent;
                border: none;
                font-size: {FONT_SIZE_SM}px;
            }}
            QCalendarWidget QMenu {{
                background: {CYBER_BG_LIGHT};
                color: {CYBER_TEXT};
            }}
            QListWidget {{
                background: {CYBER_BG_LIGHT};
                color: {CYBER_TEXT};
                border: 1px solid {CYBER_NEON_BLUE}33;
                border-radius: 8px;
                padding: {SPACING_SM}px;
            }}
            QPushButton {{
                background: {CYBER_NEON_BLUE}22;
                color: {CYBER_NEON_BLUE};
                border: 1px solid {CYBER_NEON_BLUE}44;
                border-radius: 6px;
                padding: {SPACING_SM}px {SPACING_MD}px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_SM}px;
            }}
            QPushButton:hover {{
                background: {CYBER_NEON_BLUE}44;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_SM)

        title = QLabel("📅 Timeline View")
        title.setStyleSheet(
            f"color: {CYBER_NEON_BLUE}; font-size: {FONT_SIZE_SM}px; font-weight: bold;"
        )
        layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self._calendar = QCalendarWidget()
        self._calendar.setGridVisible(True)
        self._calendar.clicked.connect(self._on_date_clicked)
        splitter.addWidget(self._calendar)

        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self._day_label = QLabel("Select a day to view entries")
        self._day_label.setStyleSheet(
            f"color: {CYBER_TEXT_DIM}; font-size: {FONT_SIZE_SM}px;"
        )
        bottom_layout.addWidget(self._day_label)

        self._entry_list = QListWidget()
        bottom_layout.addWidget(self._entry_list)

        splitter.addWidget(bottom)
        splitter.setSizes([250, 250])
        layout.addWidget(splitter)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._apply_heatmap()

    def _compute_daily_counts(self) -> Counter:
        return Counter(e.timestamp.date() for e in self._entries)

    def _apply_heatmap(self):
        counts = self._compute_daily_counts()
        if not counts:
            return
        max_count = max(counts.values()) if counts else 1
        text_format = self._calendar.dateTextFormat()
        for day, count in counts.items():
            qdate = QDate(day.year, day.month, day.day)
            intensity = min(count / max_count, 1.0)
            alpha = int(40 + 180 * intensity)
            color = f"rgba(0, 255, 170, {alpha})"
            from PyQt6.QtGui import QTextCharFormat, QColor, QBrush
            fmt = QTextCharFormat()
            fmt.setBackground(QBrush(QColor(color)))
            fmt.setForeground(QBrush(QColor(CYBER_TEXT)))
            self._calendar.setDateTextFormat(qdate, fmt)

    def _on_date_clicked(self, qdate: QDate):
        selected = date(qdate.year(), qdate.month(), qdate.day())
        day_entries = [e for e in self._entries if e.timestamp.date() == selected]
        day_entries.sort(key=lambda e: e.timestamp, reverse=True)

        self._day_label.setText(
            f"{selected.strftime('%B %d, %Y')} — {len(day_entries)} entries"
        )

        self._entry_list.clear()
        for entry in day_entries:
            time_str = entry.timestamp.strftime("%H:%M")
            preview = entry.preview(50)
            item = QListWidgetItem(f"[{time_str}] {preview}")
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self._entry_list.addItem(item)
