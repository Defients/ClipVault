"""Stylized PIN dialog used for initial unlock and changing PIN."""

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QApplication,
)
from PyQt6.QtCore import Qt
from clipvault.config import CYBER_ELECTRIC_BLUE

from clipvault.config import (
    CYBER_BG, CYBER_BG_LIGHT, CYBER_TEXT, CYBER_TEXT_DIM,
    CYBER_ELECTRIC_BLUE, FONT_FAMILY,
)
from clipvault.ui.theme import get_input_style, get_button_style


class PinDialog(QDialog):
    """Stylized PIN dialog used for initial unlock and changing PIN"""
    def __init__(self, hint: str = '', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Security PIN")
        self.setFixedSize(360, 200)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)

        self.setStyleSheet(f"""
            PinDialog {{
                background: {CYBER_BG_LIGHT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background: {CYBER_BG_LIGHT};
                border: 2px solid {CYBER_ELECTRIC_BLUE}66;
                border-radius: 10px;
            }}
        """)
        clayout = QVBoxLayout(container)
        clayout.setContentsMargins(16, 12, 16, 12)

        lbl = QLabel("Enter current PIN and new PIN (for change) or just PIN to unlock")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {CYBER_TEXT_DIM};")
        clayout.addWidget(lbl)

        self.old_pin = QLineEdit()
        self.old_pin.setPlaceholderText("Current PIN")
        self.old_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_pin.setStyleSheet(get_input_style())
        self.old_pin.setAccessibleName("Current PIN input")
        self.old_pin.returnPressed.connect(self.accept)
        clayout.addWidget(self.old_pin)

        self.new_pin = QLineEdit()
        self.new_pin.setPlaceholderText("New PIN (leave blank to just unlock)")
        self.new_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pin.setStyleSheet(get_input_style())
        self.new_pin.setAccessibleName("New PIN input")
        self.new_pin.returnPressed.connect(self.accept)
        clayout.addWidget(self.new_pin)

        btns = QHBoxLayout()
        ok = QPushButton("OK")
        ok.setStyleSheet(get_button_style())
        ok.setAccessibleName("Confirm PIN button")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(get_button_style())
        cancel.setAccessibleName("Cancel PIN button")
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok)
        btns.addWidget(cancel)
        clayout.addLayout(btns)

        layout.addWidget(container)

        self.old_pin.setFocus()

        self._center_on_screen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def _center_on_screen(self):
        """Center the dialog on the primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

    def get_pins(self):
        return self.old_pin.text(), self.new_pin.text()
