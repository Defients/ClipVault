"""Shared stylesheet helpers, design tokens, and reusable UI primitives."""

from clipvault.config import (
    CYBER_BG, CYBER_BG_LIGHT, CYBER_PANEL,
    CYBER_NEON_BLUE, CYBER_NEON_PURPLE, CYBER_NEON_GREEN,
    CYBER_ELECTRIC_BLUE, CYBER_HOT_PINK, CYBER_YELLOW,
    CYBER_ORANGE, CYBER_GRID, CYBER_TEXT, CYBER_TEXT_DIM,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
    FONT_FAMILY, FONT_FAMILY_UI,
    FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_LG, FONT_SIZE_XL,
    BORDER_ALPHA_SUBTLE, BORDER_ALPHA_DEFAULT, BORDER_ALPHA_HOVER, BORDER_ALPHA_FOCUS,
)


# ── Entry-type visual mapping ──────────────────────────────────

ENTRY_TYPE_ICONS = {
    'text': '📝',
    'url': '🔗',
    'email': '✉',
    'code': '💻',
    'number': '🔢',
    'path': '📁',
    'image': '🖼',
    'sensitive': '🔒',
}

ENTRY_TYPE_COLORS = {
    'text': CYBER_TEXT_DIM,
    'url': CYBER_ELECTRIC_BLUE,
    'email': CYBER_NEON_BLUE,
    'code': CYBER_NEON_PURPLE,
    'number': CYBER_YELLOW,
    'path': CYBER_ORANGE,
    'image': CYBER_NEON_GREEN,
    'sensitive': CYBER_HOT_PINK,
}


# ── Shared stylesheet functions ────────────────────────────────

def get_mini_button_style(color: str) -> str:
    """Return small inline button stylesheet (shared with mini panel)."""
    return f"""
        QToolButton {{
            background: transparent;
            color: {color};
            border: 1px solid {color}{BORDER_ALPHA_DEFAULT};
            border-radius: {RADIUS_SM}px;
            padding: {SPACING_XS}px {SPACING_SM}px;
            font-size: 14px;
        }}
        QToolButton:hover {{
            background: {color}22;
            border: 1px solid {color};
        }}
        QToolButton:pressed {{
            background: {color}44;
        }}
        QToolButton:disabled {{
            color: {CYBER_TEXT_DIM}66;
            border-color: {CYBER_TEXT_DIM}33;
        }}
    """


def get_list_style() -> str:
    """Return stylesheet for mini-panel QListWidget."""
    return f"""
        QListWidget {{
            background: transparent;
            border: none;
            padding: {SPACING_SM}px;
        }}
        QListWidget::item {{
            background: {CYBER_PANEL}88;
            margin: 2px;
            padding: {SPACING_SM}px;
            border-radius: {RADIUS_SM}px;
            border: 1px solid {CYBER_ELECTRIC_BLUE}{BORDER_ALPHA_SUBTLE};
        }}
        QListWidget::item:hover {{
            background: {CYBER_PANEL};
            border: 1px solid {CYBER_ELECTRIC_BLUE}{BORDER_ALPHA_HOVER};
        }}
    """


def get_input_style(focus_color: str = CYBER_NEON_BLUE) -> str:
    """Return shared QLineEdit/QTextEdit stylesheet."""
    return f"""
        QLineEdit, QTextEdit {{
            background: {CYBER_BG};
            color: {CYBER_TEXT};
            border: 1px solid {CYBER_ELECTRIC_BLUE}{BORDER_ALPHA_DEFAULT};
            border-radius: {RADIUS_SM}px;
            padding: {SPACING_SM}px;
            font-size: {FONT_SIZE_BASE}px;
            font-family: {FONT_FAMILY};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 1px solid {focus_color};
        }}
        QLineEdit:disabled, QTextEdit:disabled {{
            color: {CYBER_TEXT_DIM}66;
            border-color: {CYBER_TEXT_DIM}33;
        }}
    """


def get_button_style(color: str = CYBER_ELECTRIC_BLUE) -> str:
    """Return shared QPushButton stylesheet."""
    return f"""
        QPushButton {{
            background: {color}44;
            color: {CYBER_TEXT};
            border: 1px solid {color};
            border-radius: {RADIUS_SM}px;
            padding: {SPACING_SM}px {SPACING_LG}px;
            font-size: {FONT_SIZE_BASE}px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: {color}66;
        }}
        QPushButton:pressed {{
            background: {color}88;
        }}
        QPushButton:disabled {{
            background: {CYBER_BG_LIGHT};
            color: {CYBER_TEXT_DIM}66;
            border-color: {CYBER_TEXT_DIM}33;
        }}
    """


def get_checkbox_style() -> str:
    """Return shared QCheckBox stylesheet."""
    return f"""
        QCheckBox {{
            color: {CYBER_TEXT};
            spacing: {SPACING_MD}px;
            font-size: {FONT_SIZE_BASE}px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {CYBER_ELECTRIC_BLUE};
            border-radius: {RADIUS_SM}px;
            background: {CYBER_BG};
        }}
        QCheckBox::indicator:checked {{
            background: {CYBER_NEON_BLUE};
            border-color: {CYBER_NEON_BLUE};
        }}
        QCheckBox::indicator:hover {{
            border-color: {CYBER_NEON_BLUE};
        }}
    """


def get_group_style() -> str:
    """Return shared QGroupBox stylesheet."""
    return f"""
        QGroupBox {{
            color: {CYBER_NEON_BLUE};
            font-weight: bold;
            font-size: {FONT_SIZE_BASE}px;
            border: 1px solid {CYBER_ELECTRIC_BLUE}{BORDER_ALPHA_DEFAULT};
            border-radius: {RADIUS_LG}px;
            margin-top: {SPACING_LG}px;
            padding-top: {SPACING_LG}px;
            background: {CYBER_BG_LIGHT}44;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {SPACING_MD}px;
            padding: 0 {SPACING_SM}px;
        }}
    """


def get_spinbox_style() -> str:
    """Return shared QSpinBox stylesheet."""
    return f"""
        QSpinBox {{
            background: {CYBER_BG};
            color: {CYBER_TEXT};
            border: 1px solid {CYBER_ELECTRIC_BLUE}{BORDER_ALPHA_DEFAULT};
            border-radius: {RADIUS_SM}px;
            padding: {SPACING_SM}px;
            font-size: {FONT_SIZE_BASE}px;
        }}
        QSpinBox:focus {{
            border: 1px solid {CYBER_NEON_BLUE};
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            background: {CYBER_ELECTRIC_BLUE}33;
            border: none;
            border-radius: {RADIUS_SM - 2}px;
            width: 18px;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background: {CYBER_ELECTRIC_BLUE}66;
        }}
    """


def get_tab_style(accent: str = CYBER_NEON_BLUE) -> str:
    """Return shared QTabWidget stylesheet."""
    return f"""
        QTabWidget::pane {{
            border: 1px solid {CYBER_ELECTRIC_BLUE}{BORDER_ALPHA_SUBTLE};
            background: transparent;
        }}
        QTabBar::tab {{
            background: {CYBER_BG};
            color: {CYBER_TEXT_DIM};
            padding: {SPACING_SM}px {SPACING_LG}px;
            margin: 2px;
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_SM}px;
            border-radius: {RADIUS_SM}px;
        }}
        QTabBar::tab:selected {{
            background: {CYBER_ELECTRIC_BLUE}44;
            color: {accent};
            border-bottom: 2px solid {accent};
        }}
        QTabBar::tab:hover:!selected {{
            background: {CYBER_ELECTRIC_BLUE}22;
            color: {CYBER_TEXT};
        }}
    """


def get_scroll_area_style() -> str:
    """Return shared QScrollArea + QScrollBar stylesheet."""
    return f"""
        QScrollArea {{
            border: none;
            background: {CYBER_BG_LIGHT};
        }}
        QScrollBar:vertical {{
            background: {CYBER_BG};
            width: 10px;
            margin: 0;
            border-radius: {RADIUS_SM}px;
        }}
        QScrollBar::handle:vertical {{
            background: {CYBER_ELECTRIC_BLUE}66;
            min-height: 30px;
            border-radius: {RADIUS_SM}px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {CYBER_ELECTRIC_BLUE}aa;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: {CYBER_BG};
            height: 10px;
            margin: 0;
            border-radius: {RADIUS_SM}px;
        }}
        QScrollBar::handle:horizontal {{
            background: {CYBER_ELECTRIC_BLUE}66;
            min-width: 30px;
            border-radius: {RADIUS_SM}px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {CYBER_ELECTRIC_BLUE}aa;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
    """


def get_list_widget_style() -> str:
    """Return styled QListWidget for main window entry lists."""
    return f"""
        QListWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {CYBER_BG}cc,
                stop:1 {CYBER_BG_LIGHT}cc);
            border: 1px solid {CYBER_ELECTRIC_BLUE}{BORDER_ALPHA_SUBTLE};
            border-radius: {RADIUS_MD}px;
            padding: {SPACING_SM}px;
            outline: none;
        }}
        QListWidget::item {{
            background: transparent;
            padding: {SPACING_XS}px {SPACING_SM}px;
            margin: {SPACING_XS}px 0;
            border: none;
        }}
        QListWidget::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {CYBER_ELECTRIC_BLUE}22, stop:1 {CYBER_ELECTRIC_BLUE}11);
            border: 1px solid {CYBER_NEON_BLUE}66;
            border-left: 4px solid {CYBER_NEON_BLUE};
            border-radius: {RADIUS_MD}px;
            padding: {SPACING_XS}px {SPACING_SM}px;
        }}
        QListWidget::item:hover:!selected {{
            background: {CYBER_ELECTRIC_BLUE}11;
            border-radius: {RADIUS_MD}px;
        }}
    """


def get_empty_state_style() -> str:
    """Return stylesheet for empty state placeholder widgets."""
    return f"""
        QWidget {{
            background: transparent;
        }}
        QLabel {{
            color: {CYBER_TEXT_DIM};
            font-size: {FONT_SIZE_LG}px;
            font-family: {FONT_FAMILY};
            padding: {SPACING_2XL}px;
        }}
    """


def get_status_label_style(color: str = CYBER_NEON_GREEN) -> str:
    """Return shared status pill/badge stylesheet."""
    return f"""
        QLabel {{
            color: {color};
            font-size: {FONT_SIZE_SM}px;
            font-weight: bold;
            font-family: {FONT_FAMILY};
            padding: {SPACING_XS}px {SPACING_SM}px;
            background: {color}22;
            border: 1px solid {color};
            border-radius: {RADIUS_MD}px;
        }}
    """


def get_splitter_style() -> str:
    """Return shared QSplitter handle stylesheet."""
    return f"""
        QSplitter::handle {{
            background: {CYBER_GRID};
        }}
        QSplitter::handle:vertical {{
            height: 6px;
            margin: 0 {SPACING_SM}px;
        }}
        QSplitter::handle:horizontal {{
            width: 6px;
            margin: 0;
        }}
        QSplitter::handle:hover {{
            background: {CYBER_NEON_BLUE};
        }}
    """


def get_tooltip_style() -> str:
    """Return shared QToolTip stylesheet."""
    return f"""
        QToolTip {{
            background: {CYBER_BG_LIGHT};
            color: {CYBER_TEXT};
            border: 1px solid {CYBER_ELECTRIC_BLUE}{BORDER_ALPHA_HOVER};
            border-radius: {RADIUS_SM}px;
            padding: {SPACING_XS}px {SPACING_SM}px;
            font-size: {FONT_SIZE_SM}px;
        }}
    """


def get_label_style(color: str = CYBER_TEXT, size: int = FONT_SIZE_BASE,
                    bold: bool = False) -> str:
    """Return shared QLabel stylesheet for settings and dialogs."""
    weight = "bold" if bold else "normal"
    return f"""
        QLabel {{
            color: {color};
            font-size: {size}px;
            font-weight: {weight};
            font-family: {FONT_FAMILY};
        }}
    """


def get_slider_style(accent: str = CYBER_NEON_BLUE) -> str:
    """Return shared QSlider stylesheet."""
    return f"""
        QSlider::groove:horizontal {{
            background: {CYBER_BG};
            height: 6px;
            border-radius: {RADIUS_SM}px;
            border: 1px solid {CYBER_ELECTRIC_BLUE}{BORDER_ALPHA_SUBTLE};
        }}
        QSlider::handle:horizontal {{
            background: {accent};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
            border: 2px solid {CYBER_BG};
        }}
        QSlider::handle:horizontal:hover {{
            background: {accent};
            border: 2px solid {CYBER_TEXT};
        }}
        QSlider::sub-page:horizontal {{
            background: {accent}66;
            border-radius: {RADIUS_SM}px;
        }}
    """
