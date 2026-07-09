"""Statistics dashboard dialog."""

import json
from datetime import datetime, timedelta
from collections import Counter
from typing import List

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QScrollArea, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt

from clipvault.config import (
    CYBER_BG, CYBER_BG_LIGHT, CYBER_PANEL, CYBER_TEXT, CYBER_TEXT_DIM,
    CYBER_NEON_BLUE, CYBER_NEON_GREEN, CYBER_ELECTRIC_BLUE, DATA_FILE,
    FONT_FAMILY, FONT_SIZE_LG, SPACING_LG,
)
from clipvault.models.entry import ClipboardEntry
from clipvault.ui.glow_button import GlowButton
from clipvault.ui.theme import get_group_style, get_scroll_area_style


class StatsDialog(QDialog):
    """Statistics dashboard"""

    def __init__(self, entries: List[ClipboardEntry], parent=None):
        super().__init__(parent)
        self.entries = entries
        self.setWindowTitle("ClipVault Statistics")
        self.setFixedSize(800, 600)
        self.setStyleSheet(f"""
            QDialog {{
                background: {CYBER_BG};
            }}
        """)

        self.init_ui()
        self.load_stats()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("📊 ANALYTICS DASHBOARD")
        header.setStyleSheet(f"""
            QLabel {{
                color: {CYBER_NEON_GREEN};
                font-size: {FONT_SIZE_LG}px;
                font-weight: bold;
                font-family: {FONT_FAMILY};
                padding: {SPACING_LG}px;
                background: {CYBER_BG_LIGHT};
                border-bottom: 2px solid {CYBER_NEON_GREEN};
            }}
        """)
        header.setAccessibleName("Statistics dashboard header")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(get_scroll_area_style())
        scroll.setAccessibleName("Statistics scroll area")

        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(20)

        self.overview_group = self.create_stat_group("Overview")
        stats_layout.addWidget(self.overview_group)

        self.activity_group = self.create_stat_group("Activity")
        stats_layout.addWidget(self.activity_group)

        self.types_group = self.create_stat_group("Content Types")
        stats_layout.addWidget(self.types_group)

        self.storage_group = self.create_stat_group("Storage")
        stats_layout.addWidget(self.storage_group)

        stats_layout.addStretch()
        scroll.setWidget(stats_widget)
        layout.addWidget(scroll)

        export_btn = GlowButton("EXPORT STATS", CYBER_ELECTRIC_BLUE, glow_intensity=0.5,
                                tooltip="Export statistics to JSON file",
                                accessible_name="Export statistics button")
        export_btn.clicked.connect(self.export_stats)
        layout.addWidget(export_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def create_stat_group(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setStyleSheet(get_group_style())
        group.setAccessibleName(f"{title} statistics group")
        return group

    def load_stats(self):
        if not self.entries:
            empty = QLabel("No entries yet — start copying to see statistics.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {CYBER_TEXT_DIM}; font-size: {FONT_SIZE_LG}px; padding: 40px;")
            layout = self.layout()
            layout.insertWidget(1, empty)
            return

        overview_layout = QGridLayout()
        overview_stats = [
            ("Total Entries:", str(len(self.entries))),
            ("Pinned Entries:", str(sum(1 for e in self.entries if e.pinned))),
            ("Unique Entries:", str(len(set(e.text for e in self.entries)))),
            ("Total Size:", f"{sum(len(e.text) for e in self.entries) / 1024:.1f} KB"),
        ]

        for i, (label, value) in enumerate(overview_stats):
            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"color: {CYBER_TEXT_DIM};")
            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"color: {CYBER_NEON_GREEN}; font-weight: bold;")
            overview_layout.addWidget(label_widget, i // 2, (i % 2) * 2)
            overview_layout.addWidget(value_widget, i // 2, (i % 2) * 2 + 1)

        self.overview_group.setLayout(overview_layout)

        activity_layout = QVBoxLayout()

        today = datetime.now().date()
        today_count = sum(1 for e in self.entries if e.timestamp.date() == today)
        activity_layout.addWidget(self.create_stat_row("Today's Captures:", str(today_count)))

        week_start = today - timedelta(days=today.weekday())
        week_count = sum(1 for e in self.entries if e.timestamp.date() >= week_start)
        activity_layout.addWidget(self.create_stat_row("This Week:", str(week_count)))

        if self.entries:
            days = (self.entries[0].timestamp.date() - self.entries[-1].timestamp.date()).days + 1
            avg = len(self.entries) / max(days, 1)
            activity_layout.addWidget(self.create_stat_row("Average/Day:", f"{avg:.1f}"))

        self.activity_group.setLayout(activity_layout)

        types_layout = QVBoxLayout()
        type_counts = Counter(e.entry_type for e in self.entries)

        for entry_type, count in type_counts.most_common():
            percentage = (count / len(self.entries)) * 100
            types_layout.addWidget(
                self.create_stat_row(f"{entry_type.title()}:",
                                    f"{count} ({percentage:.1f}%)")
            )

        self.types_group.setLayout(types_layout)

        storage_layout = QVBoxLayout()

        vault_size = DATA_FILE.stat().st_size if DATA_FILE.exists() else 0
        storage_layout.addWidget(
            self.create_stat_row("Vault Size:", f"{vault_size / 1024:.1f} KB")
        )

        if self.entries:
            oldest = min(e.timestamp for e in self.entries)
            storage_layout.addWidget(
                self.create_stat_row("Oldest Entry:", oldest.strftime("%Y-%m-%d"))
            )

        self.storage_group.setLayout(storage_layout)

    def create_stat_row(self, label: str, value: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"color: {CYBER_TEXT_DIM};")

        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"color: {CYBER_TEXT}; font-weight: bold;")

        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(value_widget)

        return widget

    def export_stats(self):
        stats = {
            'generated': datetime.now().isoformat(),
            'total_entries': len(self.entries),
            'pinned_entries': sum(1 for e in self.entries if e.pinned),
            'type_distribution': dict(Counter(e.entry_type for e in self.entries)),
            'total_size_kb': sum(len(e.text) for e in self.entries) / 1024,
        }

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Statistics", "clipvault_stats.json", "JSON Files (*.json)")

        if file_path:
            with open(file_path, 'w') as f:
                json.dump(stats, f, indent=2)
            QMessageBox.information(self, "Success", "Statistics exported successfully!")
