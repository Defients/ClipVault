"""Global command palette overlay."""

from typing import List

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLineEdit,
    QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent

from clipvault.config import (
    CYBER_BG, CYBER_BG_LIGHT, CYBER_PANEL, CYBER_TEXT, CYBER_TEXT_DIM,
    CYBER_NEON_PURPLE, CYBER_ELECTRIC_BLUE, FONT_FAMILY,
)
from clipvault.models.entry import ClipboardEntry
from clipvault.ui.theme import ENTRY_TYPE_ICONS


class CommandPalette(QDialog):
    """Global command palette overlay"""

    action_triggered = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries = []
        self.commands = []

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(600)

        self.init_ui()

    def init_ui(self):
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background: {CYBER_BG}dd;
                border: 2px solid {CYBER_NEON_PURPLE}66;
                border-radius: 20px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        palette_layout = QVBoxLayout(container)
        palette_layout.setContentsMargins(20, 20, 20, 20)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Type command or search…  (↑↓ to navigate, Enter to execute)")
        self.command_input.textChanged.connect(self.filter_commands)
        self.command_input.returnPressed.connect(self.execute_first)
        self.command_input.setAccessibleName("Command palette search input")
        self.command_input.setStyleSheet(f"""
            QLineEdit {{
                background: {CYBER_BG_LIGHT};
                color: {CYBER_TEXT};
                border: 2px solid {CYBER_NEON_PURPLE}44;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border: 2px solid {CYBER_NEON_PURPLE};
            }}
        """)
        palette_layout.addWidget(self.command_input)

        self.results_list = QListWidget()
        self.results_list.setMaximumHeight(400)
        self.results_list.setAccessibleName("Command palette results list")
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                padding: 10px 0;
            }}
            QListWidget::item {{
                background: {CYBER_PANEL}66;
                color: {CYBER_TEXT};
                padding: 10px;
                margin: 2px;
                border-radius: 8px;
                border: 1px solid {CYBER_ELECTRIC_BLUE}22;
            }}
            QListWidget::item:selected {{
                background: {CYBER_ELECTRIC_BLUE}44;
                border: 1px solid {CYBER_NEON_PURPLE};
            }}
            QListWidget::item:hover {{
                background: {CYBER_ELECTRIC_BLUE}22;
            }}
        """)
        self.results_list.itemActivated.connect(self.execute_item)
        palette_layout.addWidget(self.results_list)

        self.installEventFilter(self)

    def set_data(self, entries: List[ClipboardEntry]):
        self.entries = entries
        self.build_commands()

    def build_commands(self):
        self.commands = []

        for entry in self.entries[:20]:
            icon = ENTRY_TYPE_ICONS.get(entry.entry_type, '📋')
            self.commands.append({
                'text': f"Copy: {entry.preview(40)}",
                'action': 'copy',
                'data': entry,
                'icon': icon
            })

        system_commands = [
            {'text': 'Open Settings', 'action': 'settings', 'icon': '⚙️'},
            {'text': 'Clear All Entries', 'action': 'clear', 'icon': '🗑️'},
            {'text': 'Export Data', 'action': 'export', 'icon': '💾'},
            {'text': 'Import Data', 'action': 'import', 'icon': '📥'},
            {'text': 'Show Stats', 'action': 'stats', 'icon': '📊'},
            {'text': 'Timeline View', 'action': 'timeline', 'icon': '📅'},
            {'text': 'Toggle Pin Mode', 'action': 'pin_mode', 'icon': '📌'},
            {'text': 'Pause Capture', 'action': 'pause', 'icon': '⏸️'},
        ]
        self.commands.extend(system_commands)

    def filter_commands(self, text: str):
        self.results_list.clear()

        if not text:
            filtered = self.commands[:10]
        else:
            filtered = [c for c in self.commands
                       if text.lower() in c['text'].lower()][:10]

        if not filtered:
            item = QListWidgetItem("No results found")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.results_list.addItem(item)
            return

        for cmd in filtered:
            item = QListWidgetItem(f"{cmd.get('icon', '')} {cmd['text']}")
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.results_list.addItem(item)

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def execute_first(self):
        if self.results_list.count() > 0:
            item = self.results_list.item(0)
            if item.data(Qt.ItemDataRole.UserRole) is not None:
                self.execute_item(item)

    def execute_item(self, item: QListWidgetItem):
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if cmd is None:
            return
        self.action_triggered.emit(cmd['action'], cmd.get('data'))
        self.close()

    def show_centered(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())
        self.show()
        self.command_input.clear()
        self.command_input.setFocus()
        self.filter_commands("")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.close()
            elif event.key() == Qt.Key.Key_Down:
                self.results_list.setFocus()
                if self.results_list.count() > 0:
                    row = min(self.results_list.currentRow() + 1, self.results_list.count() - 1)
                    self.results_list.setCurrentRow(row)
            elif event.key() == Qt.Key.Key_Up:
                self.results_list.setFocus()
                if self.results_list.count() > 0:
                    row = max(self.results_list.currentRow() - 1, 0)
                    self.results_list.setCurrentRow(row)
        elif event.type() == QEvent.Type.WindowDeactivate:
            self.close()
        return super().eventFilter(obj, event)
