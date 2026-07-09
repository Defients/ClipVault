"""Entry widget factory and selection-style helpers for the main list."""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QToolButton, QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import Qt, QByteArray, QMimeData
from PyQt6.QtGui import QPixmap, QImage, QDrag, QMouseEvent

from clipvault.config import (
    CYBER_BG, CYBER_PANEL, CYBER_TEXT, CYBER_TEXT_DIM,
    CYBER_NEON_BLUE, CYBER_NEON_GREEN, CYBER_NEON_PURPLE,
    CYBER_ELECTRIC_BLUE, CYBER_HOT_PINK, EntryType,
    SPACING_XS, SPACING_SM, FONT_SIZE_SM, FONT_SIZE_XS,
)
from clipvault.models.entry import ClipboardEntry
from clipvault.ui.theme import get_mini_button_style, ENTRY_TYPE_ICONS, ENTRY_TYPE_COLORS


def _relative_time(timestamp: datetime) -> str:
    """Return a human-friendly relative time string."""
    now = datetime.now()
    diff = now - timestamp
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days}d ago"
    return timestamp.strftime("%b %d")


class DraggableEntryWidget(QWidget):
    """Entry widget with drag-and-drop support for exporting entries."""

    def __init__(self, entry: ClipboardEntry, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._drag_start = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start is None or self._entry is None:
            return super().mouseMoveEvent(event)
        if (event.position().toPoint() - self._drag_start).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime = QMimeData()

        if self._entry.image_data:
            raw = QByteArray.fromBase64(self._entry.image_data.encode("ascii"))
            mime.setData("image/png", bytes(raw))
            mime.setText(self._entry.ocr_text or self._entry.text or "[Image]")
        else:
            mime.setText(self._entry.text)

        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)
        self._drag_start = None


def create_entry_widget(entry: ClipboardEntry, config: dict, main_window) -> QWidget:
    """Create entry widget with type icon, badges, and inline action buttons.

    *main_window* must expose ``copy_entry``, ``toggle_pin_entry``, and
    ``delete_entry`` methods (the ClipVaultMain instance does).
    """
    widget = DraggableEntryWidget(entry)
    widget.setFixedHeight(60)
    intensity = config.get('cyber_intensity', 0.3)

    type_color = ENTRY_TYPE_COLORS.get(entry.entry_type, CYBER_TEXT_DIM)
    bg_color = CYBER_PANEL
    border_color = f"{CYBER_ELECTRIC_BLUE}{int(68*intensity):02x}"
    left_border = f"border-left: 3px solid {type_color}88;"

    if entry.pinned:
        bg_color = f"{CYBER_BG}00"
        border_color = f"{CYBER_NEON_GREEN}22"
        left_border = f"border-left: 3px solid {CYBER_NEON_GREEN};"
    elif entry.entry_type == EntryType.SENSITIVE:
        border_color = CYBER_HOT_PINK
        left_border = f"border-left: 3px solid {CYBER_HOT_PINK};"

    base_style = f"""
        QWidget {{
            background: {bg_color};
            border: 1px solid {border_color};
            {left_border}
            border-radius: 8px;
        }}
    """

    widget.setStyleSheet(base_style)
    widget._base_style = base_style

    layout = QHBoxLayout(widget)
    layout.setContentsMargins(SPACING_SM, SPACING_XS, SPACING_SM, SPACING_XS)
    layout.setSpacing(SPACING_SM)

    if entry.pinned:
        pin_label = QLabel("📌")
        pin_label.setFixedWidth(24)
        pin_label.setStyleSheet(f"color: {CYBER_NEON_GREEN}; font-size: 16px;")
        pin_label.setAccessibleName("Pinned entry indicator")
        layout.addWidget(pin_label)

    type_icon = ENTRY_TYPE_ICONS.get(entry.entry_type, "📝")
    icon_label = QLabel(type_icon)
    icon_label.setFixedSize(28, 28)
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_label.setStyleSheet(f"font-size: 18px;")
    icon_label.setAccessibleName(f"Entry type: {entry.entry_type}")
    layout.addWidget(icon_label)

    if entry.image_data:
        img_bytes = QByteArray.fromBase64(entry.image_data.encode("ascii"))
        img = QImage()
        img.loadFromData(img_bytes, "PNG")
        if not img.isNull():
            thumb_label = QLabel()
            pixmap = QPixmap.fromImage(img)
            thumb_label.setPixmap(pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            thumb_label.setFixedSize(44, 44)
            thumb_label.setAccessibleName("Image thumbnail preview")
            layout.addWidget(thumb_label)

        preview = QLabel(entry.preview(80))
        preview.setWordWrap(True)
        preview.setStyleSheet(f"color: {CYBER_TEXT}; font-family: 'Consolas'; font-size: {FONT_SIZE_SM}px;")
        layout.addWidget(preview, 1)
    else:
        preview = QLabel(entry.preview(80))
        preview.setWordWrap(True)
        preview.setStyleSheet(f"color: {CYBER_TEXT}; font-family: 'Consolas'; font-size: {FONT_SIZE_SM}px;")
        layout.addWidget(preview, 1)

    meta_container = QWidget()
    meta_layout = QVBoxLayout(meta_container)
    meta_layout.setContentsMargins(0, 0, 0, 0)
    meta_layout.setSpacing(2)

    top_row = QWidget()
    top_layout = QHBoxLayout(top_row)
    top_layout.setContentsMargins(0, 0, 0, 0)

    type_badge = QLabel(entry.entry_type.upper())
    type_badge.setStyleSheet(f"color: {type_color}; font-size: {FONT_SIZE_XS}px; font-weight: bold;")
    top_layout.addWidget(type_badge)

    if entry.duplicate_count > 1:
        dup_badge = QLabel(f"×{entry.duplicate_count}")
        dup_badge.setStyleSheet(f"color: {CYBER_NEON_PURPLE}; font-weight:bold; font-size:{FONT_SIZE_SM}px;")
        top_layout.addWidget(dup_badge)

    if entry.ocr_text:
        ocr_badge = QLabel("📝OCR")
        ocr_badge.setStyleSheet(f"color: {CYBER_NEON_GREEN}; font-weight:bold; font-size:{FONT_SIZE_XS}px;")
        top_layout.addWidget(ocr_badge)

    top_layout.addStretch()
    meta_layout.addWidget(top_row)

    bottom_row = QWidget()
    bottom_layout = QHBoxLayout(bottom_row)
    bottom_layout.setContentsMargins(0, 0, 0, 0)

    time_label = QLabel(_relative_time(entry.timestamp))
    time_label.setStyleSheet(f"color: {CYBER_TEXT_DIM}; font-size: {FONT_SIZE_XS}px;")
    bottom_layout.addWidget(time_label)

    bottom_layout.addStretch()
    meta_layout.addWidget(bottom_row)

    layout.addWidget(meta_container)

    btn_container = QWidget()
    btn_layout = QHBoxLayout(btn_container)
    btn_layout.setContentsMargins(0, 0, 0, 0)
    btn_layout.setSpacing(2)

    copy_btn = QToolButton()
    copy_btn.setText("📋")
    copy_btn.setToolTip("Copy to clipboard")
    copy_btn.setAccessibleName("Copy this entry")
    copy_btn.setStyleSheet(get_mini_button_style(CYBER_NEON_BLUE))
    copy_btn.clicked.connect(lambda _, e=entry: main_window.copy_entry(e))

    pin_btn = QToolButton()
    pin_btn.setText("📌" if entry.pinned else "📍")
    pin_btn.setToolTip("Unpin" if entry.pinned else "Pin")
    pin_btn.setAccessibleName("Pin or unpin this entry")
    pin_btn.setStyleSheet(get_mini_button_style(CYBER_NEON_GREEN))
    pin_btn.clicked.connect(lambda _, e=entry: main_window.toggle_pin_entry(e))

    del_btn = QToolButton()
    del_btn.setText("🗑️")
    del_btn.setToolTip("Delete")
    del_btn.setAccessibleName("Delete this entry")
    del_btn.setStyleSheet(get_mini_button_style(CYBER_HOT_PINK))
    del_btn.clicked.connect(lambda _, e=entry: main_window.delete_entry(e))

    tag_btn = QToolButton()
    tag_btn.setText("🏷")
    tag_btn.setToolTip("Tags")
    tag_btn.setAccessibleName("Edit tags for this entry")
    tag_btn.setStyleSheet(get_mini_button_style(CYBER_NEON_PURPLE))
    tag_btn.clicked.connect(lambda _, e=entry: main_window.show_tag_editor(e, tag_btn))

    btn_layout.addWidget(copy_btn)
    btn_layout.addWidget(pin_btn)
    btn_layout.addWidget(del_btn)
    btn_layout.addWidget(tag_btn)

    layout.addWidget(btn_container)

    if not hasattr(widget, '_base_style'):
        widget._base_style = widget.styleSheet()

    return widget


def add_entry_to_list(list_widget: QListWidget, entry: ClipboardEntry, config: dict, main_window):
    """Add entry widget to list."""
    item = QListWidgetItem()
    widget = create_entry_widget(entry, config, main_window)
    item.setSizeHint(widget.sizeHint())
    item.setData(Qt.ItemDataRole.UserRole, entry)
    list_widget.addItem(item)
    list_widget.setItemWidget(item, widget)


def update_selection_styles(main_window):
    """Apply a polished selected look to the currently selected item widget(s)."""
    selected_overlay = f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {CYBER_ELECTRIC_BLUE}22, stop:1 {CYBER_ELECTRIC_BLUE}11);
            border: 1px solid {CYBER_NEON_BLUE}88;
            border-left: 4px solid {CYBER_NEON_BLUE};
            border-radius: 8px;
        }}
    """

    for name in ('recent_list', 'pinned_list', 'all_list'):
        lst = getattr(main_window, name, None)
        if not lst:
            continue
        for i in range(lst.count()):
            item = lst.item(i)
            widget = lst.itemWidget(item)
            if widget is None:
                continue
            try:
                if item.isSelected():
                    widget.setStyleSheet(widget._base_style + selected_overlay)
                else:
                    widget.setStyleSheet(widget._base_style)
            except Exception:
                pass
