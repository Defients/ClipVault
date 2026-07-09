"""Compact tray panel for quick access."""

from typing import List

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QLineEdit, QPushButton, QToolButton, QTabWidget,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QTimer
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtWidgets import QApplication

from clipvault.config import (
    CYBER_BG, CYBER_BG_LIGHT, CYBER_PANEL, CYBER_TEXT, CYBER_TEXT_DIM,
    CYBER_NEON_BLUE, CYBER_NEON_GREEN, CYBER_ELECTRIC_BLUE, CYBER_HOT_PINK,
    CYBER_ORANGE, CYBER_YELLOW,
    FONT_FAMILY, FONT_SIZE_SM, EntryType,
)
from clipvault.models.entry import ClipboardEntry
from clipvault.ui.theme import get_list_style, get_mini_button_style, get_tab_style

_ENTRY_ICONS = {
    EntryType.TEXT: "📋",
    EntryType.URL: "🔗",
    EntryType.EMAIL: "📧",
    EntryType.CODE: "💻",
    EntryType.NUMBER: "🔢",
    EntryType.PATH: "📁",
    EntryType.IMAGE: "🖼️",
    EntryType.SENSITIVE: "🔑",
}


def _relative_time(ts) -> str:
    """Return a short relative-time string like '2m', '1h', '3d'."""
    from datetime import datetime
    delta = datetime.now() - ts
    secs = int(delta.total_seconds())
    if secs < 60:
        return f"{secs}s"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m"
    hrs = mins // 60
    if hrs < 24:
        return f"{hrs}h"
    days = hrs // 24
    return f"{days}d"


class MiniTrayPanel(QDialog):
    """Compact tray panel for quick access"""

    copy_requested = pyqtSignal(object)
    pin_requested = pyqtSignal(object)
    delete_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries = []
        self.filtered_entries = []
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool)
        self.setFixedWidth(380)
        self.setMaximumHeight(600)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"background: transparent;")

        self.init_ui()

    def init_ui(self):
        container = QWidget()
        container.setObjectName("miniPanel")
        container.setStyleSheet(f"""
            #miniPanel {{
                background: {CYBER_BG}ab;
                border: 2px solid {CYBER_ELECTRIC_BLUE}66;
                border-radius: 15px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        panel_layout = QVBoxLayout(container)
        panel_layout.setContentsMargins(15, 15, 15, 15)
        panel_layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(4)

        header = QLabel("CLIPVAULT // QUICK ACCESS")
        header.setStyleSheet(f"""
            QLabel {{
                color: {CYBER_NEON_BLUE};
                font-size: {FONT_SIZE_SM}px;
                font-weight: bold;
                font-family: {FONT_FAMILY};
                padding: 5px;
            }}
        """)
        header.setAccessibleName("Quick access panel header")
        try:
            f = header.font()
            f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
            header.setFont(f)
        except Exception:
            pass
        header_row.addWidget(header, 1)

        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.setToolTip("Close")
        close_btn.setAccessibleName("Close quick access panel")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {CYBER_TEXT_DIM};
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background: {CYBER_HOT_PINK}33;
                color: {CYBER_HOT_PINK};
            }}
        """)
        close_btn.clicked.connect(self.close)
        header_row.addWidget(close_btn)

        panel_layout.addLayout(header_row)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter entries…")
        self.search_input.textChanged.connect(self.filter_entries)
        self.search_input.returnPressed.connect(self.copy_first)
        self.search_input.setAccessibleName("Quick access search input")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: {CYBER_TEXT};
                border: 1px solid {CYBER_ELECTRIC_BLUE}44;
                border-radius: 8px;
                padding: 8px;
                font-size: {FONT_SIZE_SM}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {CYBER_NEON_BLUE};
            }}
        """)
        panel_layout.addWidget(self.search_input)

        self.entry_count_label = QLabel("")
        self.entry_count_label.setStyleSheet(f"color: {CYBER_TEXT_DIM}; font-size: 10px; font-family: {FONT_FAMILY};")
        panel_layout.addWidget(self.entry_count_label)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {CYBER_ELECTRIC_BLUE}22;
                background: transparent;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {CYBER_TEXT_DIM};
                padding: 6px 16px;
                margin: 2px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_SM}px;
                border-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background: {CYBER_ELECTRIC_BLUE}33;
                color: {CYBER_NEON_BLUE};
                border-bottom: 2px solid {CYBER_NEON_BLUE};
            }}
            QTabBar::tab:hover:!selected {{
                background: {CYBER_ELECTRIC_BLUE}22;
                color: {CYBER_TEXT};
            }}
        """)
        self.tabs.setAccessibleName("Quick access tabs")

        list_bg = f"""
            QListWidget {{
                background: transparent;
                border: none;
                padding: 4px;
            }}
            QListWidget::item {{
                background: {CYBER_PANEL}55;
                margin: 2px;
                padding: 4px;
                border-radius: 4px;
                border: 1px solid {CYBER_ELECTRIC_BLUE}22;
            }}
            QListWidget::item:hover {{
                background: {CYBER_PANEL}88;
                border: 1px solid {CYBER_ELECTRIC_BLUE}66;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {CYBER_ELECTRIC_BLUE}66;
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {CYBER_ELECTRIC_BLUE}aa;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """

        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet(list_bg)
        self.recent_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.recent_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.recent_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.recent_list.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.recent_list.itemClicked.connect(self._on_item_clicked)
        self.recent_list.itemDoubleClicked.connect(self._on_item_clicked)
        self.tabs.addTab(self.recent_list, "Recent")

        self.pinned_list = QListWidget()
        self.pinned_list.setStyleSheet(list_bg)
        self.pinned_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pinned_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.pinned_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.pinned_list.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.pinned_list.itemClicked.connect(self._on_item_clicked)
        self.pinned_list.itemDoubleClicked.connect(self._on_item_clicked)
        self.tabs.addTab(self.pinned_list, "Pinned")

        panel_layout.addWidget(self.tabs)

        # ── Copied feedback overlay ──
        self._copied_label = QLabel("✓ Copied to clipboard!")
        self._copied_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._copied_label.setStyleSheet(f"""
            QLabel {{
                background: {CYBER_NEON_GREEN}33;
                color: {CYBER_NEON_GREEN};
                border: 1px solid {CYBER_NEON_GREEN}66;
                border-radius: 6px;
                padding: 6px;
                font-size: {FONT_SIZE_SM}px;
                font-weight: bold;
                font-family: {FONT_FAMILY};
            }}
        """)
        self._copied_label.hide()
        panel_layout.addWidget(self._copied_label)

        open_btn = QPushButton("Open Full App")
        open_btn.setAccessibleName("Open full application button")
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_ELECTRIC_BLUE}33;
                color: {CYBER_TEXT};
                border: 1px solid {CYBER_ELECTRIC_BLUE}66;
                border-radius: 8px;
                padding: 8px;
                font-size: {FONT_SIZE_SM}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {CYBER_ELECTRIC_BLUE}55;
            }}
        """)
        open_btn.clicked.connect(self.open_full_app)
        panel_layout.addWidget(open_btn)

        self.installEventFilter(self)

    def set_entries(self, entries: List[ClipboardEntry]):
        self.entries = entries
        self.filtered_entries = entries
        self.update_lists()

    def update_lists(self):
        self.recent_list.clear()
        recent = [e for e in self.filtered_entries if not e.pinned][:12]
        for entry in recent:
            self.add_entry_widget(self.recent_list, entry)

        self.pinned_list.clear()
        pinned = [e for e in self.filtered_entries if e.pinned]
        for entry in pinned:
            self.add_entry_widget(self.pinned_list, entry)

        total = len(self.filtered_entries)
        self.entry_count_label.setText(f"{total} entries")

    def add_entry_widget(self, list_widget: QListWidget, entry: ClipboardEntry):
        item = QListWidgetItem()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(4)

        type_icon = QLabel(_ENTRY_ICONS.get(entry.entry_type, "📋"))
        type_icon.setFixedWidth(18)
        type_icon.setStyleSheet(f"font-size: 12px; background: transparent;")
        layout.addWidget(type_icon)

        preview = QLabel(entry.preview(30))
        preview.setStyleSheet(f"color: {CYBER_TEXT}; font-size: 11px; background: transparent;")
        preview.setAccessibleName(f"Entry: {entry.preview(60)}")
        layout.addWidget(preview, 1)

        time_lbl = QLabel(_relative_time(entry.timestamp))
        time_lbl.setFixedWidth(28)
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_lbl.setStyleSheet(f"color: {CYBER_TEXT_DIM}; font-size: 9px; background: transparent;")
        layout.addWidget(time_lbl)

        pin_btn = QToolButton()
        pin_btn.setText("📌" if entry.pinned else "📍")
        pin_btn.setToolTip("Unpin" if entry.pinned else "Pin")
        pin_btn.setAccessibleName("Pin or unpin this entry")
        pin_btn.setStyleSheet(get_mini_button_style(CYBER_NEON_GREEN))
        pin_btn.clicked.connect(lambda: self.pin_requested.emit(entry))

        del_btn = QToolButton()
        del_btn.setText("🗑️")
        del_btn.setToolTip("Delete")
        del_btn.setAccessibleName("Delete this entry")
        del_btn.setStyleSheet(get_mini_button_style(CYBER_HOT_PINK))
        del_btn.clicked.connect(lambda: self.delete_requested.emit(entry))

        layout.addWidget(pin_btn)
        layout.addWidget(del_btn)

        widget.setLayout(layout)
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.ItemDataRole.UserRole, entry)

        list_widget.addItem(item)
        list_widget.setItemWidget(item, widget)

    def filter_entries(self, text: str):
        if not text:
            self.filtered_entries = self.entries
        else:
            self.filtered_entries = [e for e in self.entries
                                    if text.lower() in e.text.lower()]
        self.update_lists()

    def _on_item_clicked(self, item: QListWidgetItem):
        """Copy the clicked entry and show feedback before closing."""
        entry = item.data(Qt.ItemDataRole.UserRole)
        if entry:
            self.copy_requested.emit(entry)
            self._show_copied_feedback()

    def _show_copied_feedback(self):
        """Show the '✓ Copied' overlay briefly, then close the panel."""
        self._copied_label.show()
        QTimer.singleShot(800, self.close)

    def copy_first(self):
        if self.filtered_entries:
            self.copy_requested.emit(self.filtered_entries[0])
            self._show_copied_feedback()

    def open_full_app(self):
        self.parent().show()
        self.parent().raise_()
        self.parent().activateWindow()
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            lst = self.tabs.currentWidget()
            if lst:
                items = lst.selectedItems()
                if items:
                    self._on_item_clicked(items[0])
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.WindowDeactivate:
            self.close()
        return super().eventFilter(obj, event)

    def show_at_cursor(self):
        self.adjustSize()
        cursor_pos = QCursor.pos()
        screen = QApplication.primaryScreen().availableGeometry()
        h = self.height() or self.sizeHint().height()
        x = min(cursor_pos.x() - 100, screen.width() - self.width() - 20)
        y = min(cursor_pos.y() + 20, screen.height() - h - 10)
        x = max(x, 10)
        y = max(y, 10)
        self.move(x, y)
        self.show()
        self.search_input.setFocus()
