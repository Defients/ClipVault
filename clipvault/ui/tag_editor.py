"""Inline tag editor popup for adding/removing tags on entries."""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QWidget, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal

from clipvault.config import (
    CYBER_BG, CYBER_BG_LIGHT, CYBER_NEON_BLUE, CYBER_NEON_GREEN,
    CYBER_TEXT, CYBER_TEXT_DIM, FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_XS,
    SPACING_XS, SPACING_SM, SPACING_MD,
)
from clipvault.ui.theme import get_input_style, get_button_style, get_checkbox_style


_TAG_COLORS = [
    CYBER_NEON_BLUE, CYBER_NEON_GREEN, "#ff6ec7", "#ffd700",
    "#ff8c00", "#00ffaa", "#aa00ff", "#00aaff",
]


def get_tag_color(tag: str) -> str:
    """Deterministically assign a color to a tag name."""
    h = hash(tag) % len(_TAG_COLORS)
    return _TAG_COLORS[h]


class TagEditorPopup(QFrame):
    """Popup frame for editing tags on an entry."""

    tags_changed = pyqtSignal(str, list)  # (entry_id, tags)

    def __init__(self, entry, all_tags: list, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._all_tags = all_tags

        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(260)

        container = QWidget(self)
        container.setStyleSheet(f"""
            QWidget {{
                background: {CYBER_BG_LIGHT};
                border: 1px solid {CYBER_NEON_BLUE}66;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        inner = QVBoxLayout(container)
        inner.setContentsMargins(SPACING_MD, SPACING_SM, SPACING_MD, SPACING_SM)
        inner.setSpacing(SPACING_SM)

        title = QLabel("🏷 Tags")
        title.setStyleSheet(
            f"color: {CYBER_NEON_BLUE}; font-family: {FONT_FAMILY}; "
            f"font-size: {FONT_SIZE_SM}px; font-weight: bold;"
        )
        inner.addWidget(title)

        self._input = QLineEdit()
        self._input.setPlaceholderText("New tag…")
        self._input.setStyleSheet(get_input_style())
        self._input.returnPressed.connect(self._add_tag)
        inner.addWidget(self._input)

        add_btn = QPushButton("Add")
        add_btn.setStyleSheet(get_button_style(CYBER_NEON_GREEN))
        add_btn.clicked.connect(self._add_tag)
        inner.addWidget(add_btn)

        existing = [t for t in all_tags if t not in entry.tags]
        current = entry.tags

        if current:
            current_label = QLabel("Current:")
            current_label.setStyleSheet(
                f"color: {CYBER_TEXT_DIM}; font-size: {FONT_SIZE_XS}px;"
            )
            inner.addWidget(current_label)
            for tag in current:
                cb = QCheckBox(tag)
                cb.setChecked(True)
                cb.setStyleSheet(get_checkbox_style())
                cb.toggled.connect(lambda checked, t=tag: self._toggle_tag(t, checked))
                inner.addWidget(cb)

        if existing:
            avail_label = QLabel("Available:")
            avail_label.setStyleSheet(
                f"color: {CYBER_TEXT_DIM}; font-size: {FONT_SIZE_XS}px;"
            )
            inner.addWidget(avail_label)
            for tag in existing:
                cb = QCheckBox(tag)
                cb.setChecked(False)
                cb.setStyleSheet(get_checkbox_style())
                cb.toggled.connect(lambda checked, t=tag: self._toggle_tag(t, checked))
                inner.addWidget(cb)

    def _add_tag(self):
        tag = self._input.text().strip()
        if not tag:
            return
        if tag not in self._entry.tags:
            self._entry.tags.append(tag)
            self.tags_changed.emit(self._entry.id, self._entry.tags)
        self._input.clear()
        self.close()

    def _toggle_tag(self, tag: str, checked: bool):
        if checked:
            if tag not in self._entry.tags:
                self._entry.tags.append(tag)
        else:
            if tag in self._entry.tags:
                self._entry.tags.remove(tag)
        self.tags_changed.emit(self._entry.id, self._entry.tags)
