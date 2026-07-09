"""Main window UI construction helpers for ClipVaultMain.

These functions are called by ``clipvault.app.ClipVaultMain`` to build the
header, search bar, left panel, right panel, and entry lists.  They are kept
here so ``app.py`` stays a slim orchestration layer.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QListWidget, QSplitter, QTabWidget, QSystemTrayIcon,
    QMenu, QFrame, QAbstractItemView, QApplication,
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QRadialGradient, QColor, QPen, QBrush, QFont,
    QAction,
)

from clipvault.config import (
    APP_NAME, get_icon_path, CYBER_BG, CYBER_BG_LIGHT, CYBER_PANEL, CYBER_TEXT, CYBER_TEXT_DIM,
    CYBER_NEON_BLUE, CYBER_NEON_GREEN, CYBER_NEON_PURPLE,
    CYBER_ELECTRIC_BLUE, CYBER_HOT_PINK, CYBER_YELLOW,
    CYBER_ORANGE, CYBER_GRID,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    FONT_FAMILY, FONT_SIZE_BASE, FONT_SIZE_SM, FONT_SIZE_LG, FONT_SIZE_XL, FONT_SIZE_HERO,
)
from clipvault.ui.glow_button import GlowButton
from clipvault.ui.animated_background import AnimatedBackground
from clipvault.ui.theme import (
    get_list_widget_style, get_tab_style, get_splitter_style,
    get_status_label_style, get_input_style, get_scroll_area_style,
    get_tooltip_style, get_empty_state_style,
)


def apply_font_size(main_window, size: int):
    """Apply the configured font size to the application and key widgets."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    app = QApplication.instance()
    if app:
        app.setFont(QFont("Consolas", size))
    detail = getattr(main_window, 'detail_text', None)
    if detail:
        detail.setFont(QFont("Consolas", size))


def _create_empty_state(message: str, hint: str = '') -> QWidget:
    """Create a centered empty-state placeholder for a list."""
    widget = QWidget()
    widget.setStyleSheet(get_empty_state_style())
    layout = QVBoxLayout(widget)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    msg = QLabel(message)
    msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
    msg.setStyleSheet(f"color: {CYBER_TEXT_DIM}; font-size: {FONT_SIZE_LG}px; font-family: {FONT_FAMILY};")
    layout.addWidget(msg)

    if hint:
        h = QLabel(hint)
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.setStyleSheet(f"color: {CYBER_TEXT_DIM}aa; font-size: {FONT_SIZE_SM}px; font-family: {FONT_FAMILY};")
        layout.addWidget(h)

    return widget


def create_header(main_window) -> QWidget:
    """Create enhanced header with tooltips and accessible names."""
    header = QWidget()
    header.setFixedHeight(56)
    intensity = main_window.config.get('cyber_intensity', 0.3)

    header.setStyleSheet(f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {CYBER_BG_LIGHT},
                stop:0.5 {CYBER_ELECTRIC_BLUE}{int(34*intensity):02x},
                stop:1 {CYBER_BG_LIGHT});
            border-bottom: 2px solid {CYBER_ELECTRIC_BLUE}{int(102*intensity):02x};
        }}
    """)

    layout = QHBoxLayout(header)
    layout.setContentsMargins(SPACING_XL, 0, SPACING_XL, 0)
    layout.setSpacing(SPACING_SM)

    title = QLabel(f"◢ {APP_NAME.upper()} ◣")
    title.setStyleSheet(f"""
        QLabel {{
            color: {CYBER_NEON_BLUE};
            font-size: {FONT_SIZE_HERO}px;
            font-weight: bold;
            font-family: {FONT_FAMILY};
        }}
    """)
    try:
        tf = title.font()
        tf.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.5)
        title.setFont(tf)
    except Exception:
        pass
    title.setAccessibleName(f"{APP_NAME} application title")
    layout.addWidget(title)

    main_window.status_label = QLabel("● MONITORING")
    main_window.status_label.setStyleSheet(get_status_label_style(CYBER_NEON_GREEN))
    main_window.status_label.setAccessibleName("Capture status: monitoring")
    layout.addWidget(main_window.status_label)

    layout.addStretch()

    button_intensity = min(intensity * 2, 1.0)

    settings_btn = GlowButton("⚙", CYBER_YELLOW, glow_intensity=button_intensity,
                              tooltip="Settings (configure capture, privacy, appearance)",
                              accessible_name="Settings button")
    settings_btn.clicked.connect(main_window.show_settings)

    stats_btn = GlowButton("📊", CYBER_NEON_PURPLE, glow_intensity=button_intensity,
                           tooltip="View statistics dashboard",
                           accessible_name="Statistics button")
    stats_btn.clicked.connect(main_window.show_stats)

    timeline_btn = GlowButton("📅", CYBER_NEON_GREEN, glow_intensity=button_intensity,
                              tooltip="Timeline / calendar view",
                              accessible_name="Timeline button")
    timeline_btn.clicked.connect(main_window.show_timeline)

    import_btn = GlowButton("↓", CYBER_ELECTRIC_BLUE, glow_intensity=button_intensity,
                            tooltip="Import entries from JSON file",
                            accessible_name="Import button")
    import_btn.clicked.connect(main_window.import_entries)

    export_btn = GlowButton("↑", CYBER_NEON_GREEN, glow_intensity=button_intensity,
                            tooltip="Export all entries to JSON file",
                            accessible_name="Export button")
    export_btn.clicked.connect(main_window.export_all)

    layout.addWidget(settings_btn)
    layout.addWidget(stats_btn)
    layout.addWidget(timeline_btn)
    layout.addWidget(import_btn)
    layout.addWidget(export_btn)

    return header


def create_search_bar(main_window) -> QWidget:
    """Create search bar with clear button and Ctrl+F hint."""
    container = QWidget()
    container.setStyleSheet(f"""
        QWidget {{
            background: {CYBER_BG_LIGHT}88;
            border-bottom: 1px solid {CYBER_ELECTRIC_BLUE}44;
        }}
    """)

    layout = QHBoxLayout(container)
    layout.setContentsMargins(SPACING_XL, SPACING_SM, SPACING_XL, SPACING_SM)
    layout.setSpacing(SPACING_SM)

    search_icon = QLabel("🔍")
    search_icon.setStyleSheet(f"color: {CYBER_ELECTRIC_BLUE};")
    search_icon.setAccessibleName("Search icon")
    layout.addWidget(search_icon)

    main_window.search_input = QLineEdit()
    main_window.search_input.setPlaceholderText("Search clipboard entries…  (Ctrl+F)")
    main_window.search_input.textChanged.connect(main_window.filter_entries)
    main_window.search_input.textChanged.connect(lambda text: _toggle_clear_btn(main_window, text))
    main_window.search_input.setAccessibleName("Search input field")
    main_window.search_input.setMinimumWidth(200)
    main_window.search_input.setStyleSheet(f"""
        QLineEdit {{
            background: {CYBER_BG};
            color: {CYBER_TEXT};
            border: 1px solid {CYBER_ELECTRIC_BLUE}44;
            border-radius: {RADIUS_SM}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            font-size: {FONT_SIZE_BASE}px;
            font-family: {FONT_FAMILY};
        }}
        QLineEdit:focus {{
            border: 1px solid {CYBER_NEON_BLUE};
        }}
    """)
    layout.addWidget(main_window.search_input, 1)

    _orig_focus_in = main_window.search_input.focusInEvent
    def _on_focus_in(event):
        _orig_focus_in(event)
        if hasattr(main_window, '_show_search_suggestions'):
            main_window._show_search_suggestions()
    main_window.search_input.focusInEvent = _on_focus_in

    main_window._search_clear_btn = GlowButton("✕", CYBER_HOT_PINK, glow_intensity=0.3,
                                               tooltip="Clear search",
                                               accessible_name="Clear search button")
    main_window._search_clear_btn.setFixedWidth(36)
    main_window._search_clear_btn.setVisible(False)
    main_window._search_clear_btn.clicked.connect(lambda: main_window.search_input.clear())
    layout.addWidget(main_window._search_clear_btn)

    return container


def _toggle_clear_btn(main_window, text: str):
    """Show/hide the search clear button based on input text."""
    btn = getattr(main_window, '_search_clear_btn', None)
    if btn:
        btn.setVisible(bool(text))


def create_entry_list(main_window) -> QListWidget:
    """Create styled entry list using shared theme."""
    list_widget = QListWidget()
    list_widget.setStyleSheet(get_list_widget_style())
    list_widget.setSpacing(2)
    list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    list_widget.itemSelectionChanged.connect(main_window.on_selection_changed)
    list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    list_widget.customContextMenuRequested.connect(main_window.show_context_menu)
    list_widget.setAccessibleName("Clipboard entries list")
    return list_widget


def create_left_panel(main_window) -> QWidget:
    """Create left panel with tabs and empty-state support."""
    panel = QWidget()
    panel.setStyleSheet(f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {CYBER_BG_LIGHT}cc,
                stop:1 {CYBER_BG}aa);
            border: 1px solid {CYBER_ELECTRIC_BLUE}44;
            border-radius: {RADIUS_LG}px;
        }}
    """)

    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING_SM, SPACING_SM, SPACING_SM, SPACING_SM)
    layout.setSpacing(SPACING_XS)

    main_window.tabs = QTabWidget()
    main_window.tabs.currentChanged.connect(main_window.on_tab_changed)
    main_window.tabs.setStyleSheet(get_tab_style())

    main_window.recent_list = create_entry_list(main_window)
    main_window.tabs.addTab(main_window.recent_list, "RECENT")

    main_window.pinned_list = create_entry_list(main_window)
    main_window.tabs.addTab(main_window.pinned_list, "PINNED")

    main_window.all_list = create_entry_list(main_window)
    main_window.tabs.addTab(main_window.all_list, "ALL")

    main_window.tagged_list = create_entry_list(main_window)
    main_window.tabs.addTab(main_window.tagged_list, "🏷 TAGS")

    layout.addWidget(main_window.tabs)

    return panel


def create_right_panel(main_window) -> QWidget:
    """Create right panel with detail header, metadata, and action buttons."""
    panel = QWidget()
    panel.setStyleSheet(f"""
        QWidget {{
            background: {CYBER_BG_LIGHT}44;
            border: 1px solid {CYBER_ELECTRIC_BLUE}44;
            border-radius: {RADIUS_LG}px;
        }}
    """)

    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
    layout.setSpacing(SPACING_SM)

    detail_header = QLabel("▸ DETAILS")
    detail_header.setStyleSheet(f"""
        QLabel {{
            color: {CYBER_NEON_BLUE};
            font-size: {FONT_SIZE_SM}px;
            font-weight: bold;
            font-family: {FONT_FAMILY};
            padding: {SPACING_XS}px 0;
        }}
    """)
    detail_header.setAccessibleName("Details section header")
    layout.addWidget(detail_header)

    main_window.detail_text = QTextEdit()
    main_window.detail_text.setReadOnly(True)
    main_window.detail_text.setFont(QFont("Consolas", 11))
    main_window.detail_text.setMinimumHeight(100)
    main_window.detail_text.setPlaceholderText("Select an entry to view its full content…")
    main_window.detail_text.setAccessibleName("Entry detail view")
    main_window.detail_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
    main_window.detail_text.setStyleSheet(f"""
        QTextEdit {{
            background: {CYBER_BG};
            color: {CYBER_TEXT};
            border: 1px solid {CYBER_ELECTRIC_BLUE}22;
            border-radius: {RADIUS_MD}px;
            padding: {SPACING_MD}px;
        }}
    """)
    layout.addWidget(main_window.detail_text, 1)

    meta_frame = QFrame()
    meta_frame.setStyleSheet(f"""
        QFrame {{
            background: {CYBER_BG}66;
            border: 1px solid {CYBER_ELECTRIC_BLUE}22;
            border-radius: {RADIUS_SM}px;
        }}
    """)
    meta_layout = QHBoxLayout(meta_frame)
    meta_layout.setContentsMargins(SPACING_SM, SPACING_XS, SPACING_SM, SPACING_XS)
    meta_layout.setSpacing(SPACING_MD)

    main_window.meta_type_label = QLabel("")
    main_window.meta_type_label.setStyleSheet(f"color: {CYBER_TEXT_DIM}; font-size: {FONT_SIZE_SM}px; font-family: {FONT_FAMILY};")
    meta_layout.addWidget(main_window.meta_type_label)

    main_window.meta_time_label = QLabel("")
    main_window.meta_time_label.setStyleSheet(f"color: {CYBER_TEXT_DIM}; font-size: {FONT_SIZE_SM}px; font-family: {FONT_FAMILY};")
    meta_layout.addWidget(main_window.meta_time_label)

    meta_layout.addStretch()

    main_window.meta_count_label = QLabel("")
    main_window.meta_count_label.setStyleSheet(f"color: {CYBER_NEON_PURPLE}; font-size: {FONT_SIZE_SM}px; font-family: {FONT_FAMILY};")
    meta_layout.addWidget(main_window.meta_count_label)

    layout.addWidget(meta_frame)

    button_container = QWidget()
    button_layout = QHBoxLayout(button_container)
    button_layout.setSpacing(SPACING_SM)
    button_layout.setContentsMargins(0, SPACING_XS, 0, SPACING_XS)

    intensity = main_window.config.get('cyber_intensity', 0.3)

    main_window.copy_btn = GlowButton("📋 COPY", CYBER_NEON_BLUE, glow_intensity=intensity,
                                      tooltip="Copy selected entry to clipboard (Ctrl+C)",
                                      accessible_name="Copy button")
    main_window.copy_btn.clicked.connect(main_window.copy_selected)
    main_window.copy_btn.setEnabled(False)

    main_window.pin_btn = GlowButton("📌 PIN", CYBER_NEON_GREEN, glow_intensity=intensity,
                                     tooltip="Pin or unpin selected entry",
                                     accessible_name="Pin button")
    main_window.pin_btn.clicked.connect(main_window.toggle_pin_selected)
    main_window.pin_btn.setEnabled(False)

    main_window.delete_btn = GlowButton("🗑 DELETE", CYBER_HOT_PINK, glow_intensity=intensity,
                                        tooltip="Delete selected entry (Delete key)",
                                        accessible_name="Delete button")
    main_window.delete_btn.clicked.connect(main_window.delete_selected)
    main_window.delete_btn.setEnabled(False)

    button_layout.addWidget(main_window.copy_btn)
    button_layout.addWidget(main_window.pin_btn)
    button_layout.addWidget(main_window.delete_btn)

    layout.addWidget(button_container)

    return panel


def create_status_bar(main_window) -> QWidget:
    """Create a thin bottom status bar."""
    bar = QWidget()
    bar.setFixedHeight(28)
    bar.setStyleSheet(f"""
        QWidget {{
            background: {CYBER_BG_LIGHT};
            border-top: 1px solid {CYBER_ELECTRIC_BLUE}33;
        }}
    """)

    layout = QHBoxLayout(bar)
    layout.setContentsMargins(SPACING_XL, 0, SPACING_XL, 0)
    layout.setSpacing(SPACING_MD)

    main_window.status_entry_count = QLabel("0 entries")
    main_window.status_entry_count.setStyleSheet(f"color: {CYBER_TEXT_DIM}; font-size: {FONT_SIZE_SM}px; font-family: {FONT_FAMILY};")
    layout.addWidget(main_window.status_entry_count)

    layout.addStretch()

    main_window.status_last_capture = QLabel("")
    main_window.status_last_capture.setStyleSheet(f"color: {CYBER_TEXT_DIM}; font-size: {FONT_SIZE_SM}px; font-family: {FONT_FAMILY};")
    layout.addWidget(main_window.status_last_capture)

    return bar


def init_ui(main_window):
    """Build the full main-window UI."""
    main_window.setWindowTitle(APP_NAME.upper())
    main_window.setGeometry(100, 100, 1200, 700)
    main_window.setMinimumSize(700, 500)
    main_window.setStyleSheet(f"""
        QMainWindow {{
            background: {CYBER_BG};
        }}
    """)

    central = QWidget()
    main_window.setCentralWidget(central)
    central_layout = QVBoxLayout(central)
    central_layout.setContentsMargins(0, 0, 0, 0)
    central_layout.setSpacing(0)

    main_window.bg = AnimatedBackground(central, main_window.config.get('cyber_intensity', 0.3))
    main_window.bg.setObjectName("animatedBackground")
    main_window.bg.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    try:
        main_window.bg.setSizePolicy(main_window.sizePolicy())
    except Exception:
        pass
    main_window.bg.setAutoFillBackground(False)
    main_window.bg.setParent(central)
    main_window.bg.setGeometry(central.rect())
    central.installEventFilter(main_window)
    main_window.bg.lower()

    container = QWidget()
    container.setStyleSheet(f"""
        QWidget {{
            background: {CYBER_BG}ee;
        }}
    """)
    central_layout.addWidget(container)

    main_layout = QVBoxLayout(container)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    header = create_header(main_window)
    main_layout.addWidget(header)

    search_container = create_search_bar(main_window)
    search_container.setMinimumHeight(48)

    v_splitter = QSplitter(Qt.Orientation.Vertical)
    v_splitter.setHandleWidth(6)
    v_splitter.setStyleSheet(get_splitter_style())

    v_splitter.addWidget(search_container)

    h_splitter = QSplitter(Qt.Orientation.Horizontal)
    h_splitter.setHandleWidth(6)
    h_splitter.setStyleSheet(get_splitter_style())
    left_panel = create_left_panel(main_window)
    h_splitter.addWidget(left_panel)

    right_panel = create_right_panel(main_window)
    h_splitter.addWidget(right_panel)

    h_splitter.setSizes([400, 650])
    h_splitter.setChildrenCollapsible(False)
    left_panel.setMinimumWidth(250)
    right_panel.setMinimumWidth(300)

    v_splitter.addWidget(h_splitter)
    v_splitter.setChildrenCollapsible(False)

    try:
        v_splitter.setSizes([52, 648])
    except Exception:
        pass

    main_layout.addWidget(v_splitter, 1)

    status_bar = create_status_bar(main_window)
    main_layout.addWidget(status_bar)

    main_window.setup_shortcuts()


def _create_tray_icon_pixmap() -> QPixmap:
    """Draw a polished cyber-themed tray icon programmatically.

    64×64 transparent canvas with:
    - Dark rounded-rect background
    - Neon blue/cyan radial glow
    - Bright ring border
    - "CV" monogram in the center
    """
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # ── Dark background circle ──
    bg_gradient = QRadialGradient(size / 2, size / 2, size / 2)
    bg_gradient.setColorAt(0, QColor(CYBER_BG_LIGHT))
    bg_gradient.setColorAt(0.7, QColor(CYBER_BG))
    bg_gradient.setColorAt(1, QColor("#030508"))
    painter.setBrush(QBrush(bg_gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, size - 8, size - 8)

    # ── Neon glow ring ──
    glow_gradient = QRadialGradient(size / 2, size / 2, size / 2 - 2)
    glow_gradient.setColorAt(0.55, QColor(CYBER_NEON_BLUE))
    glow_gradient.setColorAt(0.75, QColor(CYBER_ELECTRIC_BLUE))
    glow_gradient.setColorAt(1.0, QColor(CYBER_ELECTRIC_BLUE + "00"))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QBrush(glow_gradient), 3))
    painter.drawEllipse(6, 6, size - 12, size - 12)

    # ── Inner accent ring ──
    painter.setPen(QPen(QColor(CYBER_NEON_BLUE), 1))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(10, 10, size - 20, size - 20)

    # ── "CV" monogram ──
    font = QFont("Consolas", 18, QFont.Weight.Bold)
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
    painter.setFont(font)
    painter.setPen(QColor(CYBER_NEON_GREEN))
    fm = painter.fontMetrics()
    text = "CV"
    text_width = fm.horizontalAdvance(text)
    text_height = fm.ascent()
    painter.drawText(
        (size - text_width) // 2,
        (size + text_height) // 2 - 2,
        text,
    )

    # ── Subtle bottom highlight ──
    highlight = QRadialGradient(size / 2, size - 12, 20)
    highlight.setColorAt(0, QColor(CYBER_NEON_BLUE + "33"))
    highlight.setColorAt(1, QColor(CYBER_NEON_BLUE + "00"))
    painter.setBrush(QBrush(highlight))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(8, size - 20, size - 16, 16)

    painter.end()
    return pixmap


def setup_tray(main_window):
    """Setup system tray with a beautified icon and a context menu."""
    main_window.tray_icon = QSystemTrayIcon(main_window)

    icon_path = get_icon_path()
    if icon_path.exists():
        icon = QIcon(str(icon_path))
    else:
        pixmap = _create_tray_icon_pixmap()
        icon = QIcon(pixmap)
    main_window.tray_icon.setIcon(icon)
    main_window.tray_icon.setToolTip(APP_NAME)

    # Apply the same icon to the main window so it shows in the taskbar / title bar
    main_window.setWindowIcon(icon)

    # ── Context menu ──
    menu = QMenu()
    menu.setStyleSheet(f"""
        QMenu {{
            background: {CYBER_BG};
            border: 1px solid {CYBER_ELECTRIC_BLUE}66;
            border-radius: 6px;
            padding: 4px;
            color: {CYBER_TEXT};
            font-family: 'Consolas', 'Cascadia Code', monospace;
            font-size: 12px;
        }}
        QMenu::item {{
            padding: 6px 28px 6px 20px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background: {CYBER_ELECTRIC_BLUE}33;
            color: {CYBER_NEON_BLUE};
        }}
        QMenu::separator {{
            height: 1px;
            background: {CYBER_ELECTRIC_BLUE}33;
            margin: 4px 8px;
        }}
    """)

    show_action = QAction("Show / Hide", menu)
    show_action.triggered.connect(lambda: _toggle_main_window(main_window))
    menu.addAction(show_action)

    quick_action = QAction("Quick Access", menu)
    quick_action.triggered.connect(lambda: _tray_quick_access(main_window))
    menu.addAction(quick_action)

    settings_action = QAction("Settings", menu)
    settings_action.triggered.connect(main_window.show_settings)
    menu.addAction(settings_action)

    menu.addSeparator()

    quit_action = QAction("Quit", menu)
    quit_action.triggered.connect(lambda: _quit_app(main_window))
    menu.addAction(quit_action)

    main_window.tray_icon.setContextMenu(menu)

    main_window.tray_icon.activated.connect(main_window.tray_activated)
    main_window.tray_icon.show()


def _toggle_main_window(main_window):
    """Toggle visibility of the main window from the tray menu."""
    if main_window.isVisible():
        main_window.hide()
    else:
        main_window.show()
        main_window.raise_()
        main_window.activateWindow()


def _tray_quick_access(main_window):
    """Open the mini panel at the cursor position."""
    main_window.mini_panel.set_entries(main_window.entries[:20])
    main_window.mini_panel.show_at_cursor()


def _quit_app(main_window):
    """Gracefully quit the application from the tray menu."""
    main_window._force_quit = True
    try:
        main_window.close()
    except Exception:
        pass
    QApplication.instance().quit()
