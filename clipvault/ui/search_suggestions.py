"""Search suggestion dropdown popup showing recent search queries."""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal

from clipvault.config import (
    CYBER_BG_LIGHT, CYBER_NEON_BLUE, CYBER_TEXT, CYBER_TEXT_DIM,
    FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_XS,
    SPACING_XS, SPACING_SM,
)


class SearchSuggestionPopup(QFrame):
    """Popup showing recent search queries below the search input."""

    query_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(350)

        self._container = QWidget(self)
        self._container.setStyleSheet(f"""
            QWidget {{
                background: {CYBER_BG_LIGHT};
                border: 1px solid {CYBER_NEON_BLUE}44;
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._container)

        self._inner = QVBoxLayout(self._container)
        self._inner.setContentsMargins(SPACING_SM, SPACING_SM, SPACING_SM, SPACING_SM)
        self._inner.setSpacing(SPACING_XS)

        self._buttons = []

    def set_queries(self, queries: list, filter_text: str = ""):
        """Populate the popup with query suggestions."""
        self._clear_buttons()

        if not queries:
            self.hide()
            return

        if filter_text:
            queries = [q for q in queries if filter_text.lower() in q.lower()]

        if not queries:
            self.hide()
            return

        for q in queries[:10]:
            btn = QPushButton(q)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {CYBER_TEXT};
                    border: none;
                    border-radius: 4px;
                    padding: {SPACING_XS}px {SPACING_SM}px;
                    text-align: left;
                    font-family: {FONT_FAMILY};
                    font-size: {FONT_SIZE_SM}px;
                }}
                QPushButton:hover {{
                    background: {CYBER_NEON_BLUE}22;
                }}
            """)
            btn.clicked.connect(lambda _, query=q: self._select(query))
            self._inner.addWidget(btn)
            self._buttons.append(btn)

        self.adjustSize()

    def _select(self, query: str):
        self.query_selected.emit(query)
        self.hide()

    def _clear_buttons(self):
        for btn in self._buttons:
            self._inner.removeWidget(btn)
            btn.deleteLater()
        self._buttons = []

    def show_below(self, widget):
        """Show the popup directly below the given widget."""
        pos = widget.mapToGlobal(widget.rect().bottomLeft())
        self.move(pos)
        self.show()
