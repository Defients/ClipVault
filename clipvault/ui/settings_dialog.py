"""Comprehensive settings dialog with dirty-state tracking and validation."""

import re
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QSpinBox, QSlider, QCheckBox, QGroupBox,
    QTabWidget, QTextEdit, QPushButton, QFileDialog, QMessageBox,
    QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from clipvault.config import (
    CYBER_BG, CYBER_BG_LIGHT, CYBER_TEXT, CYBER_TEXT_DIM,
    CYBER_NEON_BLUE, CYBER_NEON_GREEN, CYBER_NEON_PURPLE,
    CYBER_ELECTRIC_BLUE, CYBER_HOT_PINK, CYBER_ORANGE, CYBER_YELLOW,
    FONT_FAMILY, FONT_SIZE_BASE, FONT_SIZE_SM, FONT_SIZE_XS, FONT_SIZE_LG,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
)
from clipvault.ui.glow_button import GlowButton
from clipvault.ui.pin_dialog import PinDialog
from clipvault.ui.theme import (
    get_group_style, get_checkbox_style, get_input_style,
    get_spinbox_style, get_button_style, get_tab_style,
    get_label_style, get_slider_style, get_scroll_area_style,
    get_tooltip_style,
)
from clipvault.storage.vault import StorageManager


class SettingsDialog(QDialog):
    """Comprehensive settings dialog with dirty-state tracking and validation."""

    settings_changed = pyqtSignal(dict)
    intensity_preview = pyqtSignal(float)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self._initial_config = config.copy()
        self._dirty = False
        self.setWindowTitle("ClipVault Settings")
        self.setMinimumSize(720, 560)
        self.setStyleSheet(f"""
            QDialog {{
                background: {CYBER_BG};
            }}
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("⚙ SYSTEM CONFIGURATION")
        header.setStyleSheet(f"""
            QLabel {{
                color: {CYBER_NEON_BLUE};
                font-size: {FONT_SIZE_LG}px;
                font-weight: bold;
                font-family: {FONT_FAMILY};
                padding: {SPACING_LG}px {SPACING_XL}px;
                background: {CYBER_BG_LIGHT};
                border-bottom: 2px solid {CYBER_ELECTRIC_BLUE};
            }}
        """)
        header.setAccessibleName("Settings dialog header")
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(get_tab_style())
        self.tabs.setAccessibleName("Settings categories")

        self.create_appearance_tab()
        self.create_capture_tab()
        self.create_privacy_tab()
        self.create_data_tab()
        self.create_hotkeys_tab()

        layout.addWidget(self.tabs, 1)

        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_BG_LIGHT};
                border-top: 2px solid {CYBER_ELECTRIC_BLUE};
            }}
        """)
        button_layout = QHBoxLayout(footer)
        button_layout.setContentsMargins(SPACING_XL, SPACING_MD, SPACING_XL, SPACING_MD)
        button_layout.setSpacing(SPACING_SM)

        cancel_btn = GlowButton("CANCEL", CYBER_ELECTRIC_BLUE, glow_intensity=0.4,
                                tooltip="Discard changes and close",
                                accessible_name="Cancel settings button")
        cancel_btn.clicked.connect(self.reject)

        reset_btn = GlowButton("RESET", CYBER_ORANGE, glow_intensity=0.4,
                               tooltip="Reset all settings to defaults",
                               accessible_name="Reset settings button")
        reset_btn.clicked.connect(self.reset_defaults)

        apply_btn = GlowButton("APPLY", CYBER_NEON_GREEN, glow_intensity=0.4,
                              tooltip="Apply settings without closing",
                              accessible_name="Apply settings button")
        apply_btn.clicked.connect(self.apply_settings)

        save_btn = GlowButton("SAVE", CYBER_NEON_BLUE, glow_intensity=0.5,
                             tooltip="Save settings and close",
                             accessible_name="Save settings button")
        save_btn.clicked.connect(self.save_settings)

        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(save_btn)

        layout.addWidget(footer)

    # ── Helpers ──────────────────────────────────────────────────

    def _wrap_scroll(self, content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        scroll.setStyleSheet(get_scroll_area_style())
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll

    def _set_dirty(self):
        self._dirty = True

    def _help_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(get_label_style(CYBER_TEXT_DIM, FONT_SIZE_XS))
        return lbl

    # ── Tab: Appearance ──────────────────────────────────────────

    def create_appearance_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(SPACING_XL, SPACING_XL, SPACING_XL, SPACING_XL)
        layout.setSpacing(SPACING_LG)

        intensity_group = QGroupBox("Visual Intensity")
        intensity_group.setStyleSheet(get_group_style())
        intensity_layout = QVBoxLayout()
        intensity_layout.setSpacing(SPACING_SM)

        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(int(self.config.get('cyber_intensity', 0.3) * 100))
        self.intensity_slider.setStyleSheet(get_slider_style())
        self.intensity_slider.setAccessibleName("Visual intensity slider")
        self.intensity_slider.setToolTip("Controls the strength of cyber/neon visual effects")
        self.intensity_slider.valueChanged.connect(self._on_intensity_changed)

        self.intensity_label = QLabel(f"Cyber Mode: {self.intensity_slider.value()}%")
        self.intensity_label.setStyleSheet(get_label_style(CYBER_TEXT, FONT_SIZE_SM, bold=True))

        intensity_layout.addWidget(self.intensity_label)
        intensity_layout.addWidget(self.intensity_slider)
        intensity_layout.addWidget(self._help_label("0% = Subtle Mode · 50% = Balanced · 100% = Full Cyber"))

        intensity_group.setLayout(intensity_layout)
        layout.addWidget(intensity_group)

        motion_group = QGroupBox("Animation & Accessibility")
        motion_group.setStyleSheet(get_group_style())
        motion_layout = QVBoxLayout()
        motion_layout.setSpacing(SPACING_SM)

        self.reduce_motion = QCheckBox("Reduce Motion")
        self.reduce_motion.setChecked(self.config.get('reduce_motion', False))
        self.reduce_motion.setStyleSheet(get_checkbox_style())
        self.reduce_motion.setAccessibleName("Reduce motion checkbox")
        self.reduce_motion.setToolTip("Disable animations for accessibility (WCAG 2.2 AA)")
        self.reduce_motion.toggled.connect(self._set_dirty)

        self.disable_bg = QCheckBox("Disable Background Animation")
        self.disable_bg.setChecked(self.config.get('disable_bg', False))
        self.disable_bg.setStyleSheet(get_checkbox_style())
        self.disable_bg.setAccessibleName("Disable background animation checkbox")
        self.disable_bg.setToolTip("Turn off the animated particle background")
        self.disable_bg.toggled.connect(self._set_dirty)

        motion_layout.addWidget(self.reduce_motion)
        motion_layout.addWidget(self.disable_bg)
        motion_layout.addWidget(self._help_label("Reduce Motion disables all animations. Disable Background keeps UI animations but removes the particle field."))
        motion_group.setLayout(motion_layout)
        layout.addWidget(motion_group)

        font_group = QGroupBox("Typography")
        font_group.setStyleSheet(get_group_style())
        font_layout = QHBoxLayout()
        font_layout.setSpacing(SPACING_MD)

        font_label = QLabel("Font Size:")
        font_label.setStyleSheet(get_label_style())

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 20)
        self.font_size.setValue(self.config.get('font_size', 12))
        self.font_size.setStyleSheet(get_spinbox_style())
        self.font_size.setAccessibleName("Font size spinbox")
        self.font_size.setToolTip("Base font size for the application (8–20 px)")
        self.font_size.setSuffix(" px")
        self.font_size.valueChanged.connect(self._set_dirty)

        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_size)
        font_layout.addStretch()
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        layout.addStretch()
        self.tabs.addTab(self._wrap_scroll(widget), "🎨 Appearance")

    # ── Tab: Capture ─────────────────────────────────────────────

    def create_capture_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(SPACING_XL, SPACING_XL, SPACING_XL, SPACING_XL)
        layout.setSpacing(SPACING_LG)

        control_group = QGroupBox("Capture Control")
        control_group.setStyleSheet(get_group_style())
        control_layout = QVBoxLayout()
        control_layout.setSpacing(SPACING_SM)

        self.pause_capture = QCheckBox("Pause Clipboard Capture")
        self.pause_capture.setChecked(self.config.get('pause_capture', False))
        self.pause_capture.setStyleSheet(get_checkbox_style())
        self.pause_capture.setAccessibleName("Pause clipboard capture checkbox")
        self.pause_capture.setToolTip("Stop capturing new clipboard entries")
        self.pause_capture.toggled.connect(self._set_dirty)

        self.incognito_mode = QCheckBox("Incognito Mode (No Disk Storage)")
        self.incognito_mode.setChecked(self.config.get('incognito_mode', False))
        self.incognito_mode.setStyleSheet(get_checkbox_style())
        self.incognito_mode.setAccessibleName("Incognito mode checkbox")
        self.incognito_mode.setToolTip("Capture and display entries without persisting to disk")
        self.incognito_mode.toggled.connect(self._set_dirty)

        control_layout.addWidget(self.pause_capture)
        control_layout.addWidget(self.incognito_mode)
        control_layout.addWidget(self._help_label("Incognito Mode: entries appear in the UI but are never written to the encrypted vault."))

        self.enable_ocr = QCheckBox("Enable OCR for images (requires Tesseract)")
        self.enable_ocr.setChecked(self.config.get('enable_ocr', False))
        self.enable_ocr.setStyleSheet(get_checkbox_style())
        self.enable_ocr.setAccessibleName("Enable OCR checkbox")
        self.enable_ocr.setToolTip("Extract text from copied images using Tesseract OCR")
        self.enable_ocr.toggled.connect(self._set_dirty)
        control_layout.addWidget(self.enable_ocr)
        control_layout.addWidget(self._help_label("Download Tesseract from github.com/UB-Mannheim/tesseract/wiki"))

        self.enable_search_history = QCheckBox("Remember search history")
        self.enable_search_history.setChecked(self.config.get('enable_search_history', True))
        self.enable_search_history.setStyleSheet(get_checkbox_style())
        self.enable_search_history.setAccessibleName("Enable search history checkbox")
        self.enable_search_history.setToolTip("Remember recent search queries and show suggestions")
        self.enable_search_history.toggled.connect(self._set_dirty)
        control_layout.addWidget(self.enable_search_history)

        clear_search_btn = QPushButton("Clear Search History")
        clear_search_btn.setStyleSheet(get_button_style())
        clear_search_btn.setAccessibleName("Clear search history button")
        clear_search_btn.clicked.connect(self._clear_search_history)
        control_layout.addWidget(clear_search_btn)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        filter_group = QGroupBox("Application Filters")
        filter_group.setStyleSheet(get_group_style())
        filter_layout = QVBoxLayout()
        filter_layout.setSpacing(SPACING_SM)

        filter_desc = QLabel("Exclude apps (comma-separated):")
        filter_desc.setStyleSheet(get_label_style())

        self.exclude_apps = QLineEdit()
        self.exclude_apps.setText(self.config.get('exclude_apps', ''))
        self.exclude_apps.setPlaceholderText("e.g., KeePass, 1Password, Bitwarden")
        self.exclude_apps.setStyleSheet(get_input_style())
        self.exclude_apps.setAccessibleName("Excluded applications input")
        self.exclude_apps.setToolTip("Clipboard content from these apps will not be captured")
        self.exclude_apps.textChanged.connect(self._set_dirty)

        filter_layout.addWidget(filter_desc)
        filter_layout.addWidget(self.exclude_apps)
        filter_layout.addWidget(self._help_label("Entries copied from listed applications will be ignored."))
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        regex_group = QGroupBox("Content Filters")
        regex_group.setStyleSheet(get_group_style())
        regex_layout = QVBoxLayout()
        regex_layout.setSpacing(SPACING_SM)

        regex_desc = QLabel("Block patterns (regex, one per line):")
        regex_desc.setStyleSheet(get_label_style())

        self.block_patterns = QTextEdit()
        self.block_patterns.setPlainText(self.config.get('block_patterns', ''))
        self.block_patterns.setMaximumHeight(120)
        self.block_patterns.setStyleSheet(get_input_style())
        self.block_patterns.setAccessibleName("Block patterns input")
        self.block_patterns.setToolTip("Regular expressions, one per line, to block from capture")
        self.block_patterns.textChanged.connect(self._set_dirty)

        self.regex_status = QLabel("")
        self.regex_status.setStyleSheet(get_label_style(CYBER_TEXT_DIM, FONT_SIZE_XS))
        self.regex_status.setAccessibleName("Regex validation status")

        regex_layout.addWidget(regex_desc)
        regex_layout.addWidget(self.block_patterns)
        regex_layout.addWidget(self.regex_status)
        regex_layout.addWidget(self._help_label("Each line is a regex. Invalid patterns are silently ignored at runtime but flagged here."))
        regex_group.setLayout(regex_layout)
        layout.addWidget(regex_group)

        layout.addStretch()
        self.tabs.addTab(self._wrap_scroll(widget), "📡 Capture")

    # ── Tab: Privacy ─────────────────────────────────────────────

    def create_privacy_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(SPACING_XL, SPACING_XL, SPACING_XL, SPACING_XL)
        layout.setSpacing(SPACING_LG)

        security_group = QGroupBox("Security")
        security_group.setStyleSheet(get_group_style())
        security_layout = QVBoxLayout()
        security_layout.setSpacing(SPACING_SM)

        self.auto_lock = QCheckBox("Auto-lock on idle")
        self.auto_lock.setChecked(self.config.get('auto_lock', False))
        self.auto_lock.setStyleSheet(get_checkbox_style())
        self.auto_lock.setAccessibleName("Auto-lock checkbox")
        self.auto_lock.setToolTip("Automatically lock the vault after a period of inactivity")
        self.auto_lock.toggled.connect(self._set_dirty)

        lock_time_layout = QHBoxLayout()
        lock_time_layout.setSpacing(SPACING_MD)
        lock_label = QLabel("Lock after (minutes):")
        lock_label.setStyleSheet(get_label_style())

        self.lock_time = QSpinBox()
        self.lock_time.setRange(1, 120)
        self.lock_time.setValue(self.config.get('lock_time', 10))
        self.lock_time.setStyleSheet(get_spinbox_style())
        self.lock_time.setAccessibleName("Auto-lock timeout spinbox")
        self.lock_time.setSuffix(" min")
        self.lock_time.valueChanged.connect(self._set_dirty)

        lock_time_layout.addWidget(lock_label)
        lock_time_layout.addWidget(self.lock_time)
        lock_time_layout.addStretch()

        security_layout.addWidget(self.auto_lock)
        security_layout.addLayout(lock_time_layout)
        security_layout.addWidget(self._help_label("When enabled, the vault locks after the specified idle time and requires PIN re-entry."))
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)

        self.auto_lock.toggled.connect(
            lambda checked: self.lock_time.setEnabled(checked)
        )
        self.lock_time.setEnabled(self.auto_lock.isChecked())

        sensitive_group = QGroupBox("Sensitive Data Protection")
        sensitive_group.setStyleSheet(get_group_style())
        sensitive_layout = QVBoxLayout()
        sensitive_layout.setSpacing(SPACING_SM)

        self.block_sensitive = QCheckBox("Block credit cards, SSNs, API keys")
        self.block_sensitive.setChecked(self.config.get('block_sensitive', True))
        self.block_sensitive.setStyleSheet(get_checkbox_style())
        self.block_sensitive.setAccessibleName("Block sensitive data checkbox")
        self.block_sensitive.setToolTip("Prevent capturing credit card numbers, SSNs, and API keys")
        self.block_sensitive.toggled.connect(self._set_dirty)

        self.ephemeral_otp = QCheckBox("Auto-expire OTP codes (5 min)")
        self.ephemeral_otp.setChecked(self.config.get('ephemeral_otp', True))
        self.ephemeral_otp.setStyleSheet(get_checkbox_style())
        self.ephemeral_otp.setAccessibleName("Auto-expire OTP checkbox")
        self.ephemeral_otp.setToolTip("Automatically delete OTP codes after 5 minutes")
        self.ephemeral_otp.toggled.connect(self._set_dirty)

        sensitive_layout.addWidget(self.block_sensitive)
        sensitive_layout.addWidget(self.ephemeral_otp)
        sensitive_group.setLayout(sensitive_layout)
        layout.addWidget(sensitive_group)

        pin_group = QGroupBox("PIN Management")
        pin_group.setStyleSheet(get_group_style())
        pin_layout = QHBoxLayout()
        pin_layout.setSpacing(SPACING_MD)

        change_pin_btn = QPushButton("Change PIN")
        change_pin_btn.setStyleSheet(get_button_style(CYBER_NEON_BLUE))
        change_pin_btn.setAccessibleName("Change PIN button")
        change_pin_btn.setToolTip("Change the vault PIN code (requires current PIN)")
        change_pin_btn.clicked.connect(self.change_pin)

        pin_layout.addWidget(change_pin_btn)
        pin_layout.addStretch()
        pin_group.setLayout(pin_layout)
        layout.addWidget(pin_group)

        layout.addStretch()
        self.tabs.addTab(self._wrap_scroll(widget), "🔒 Privacy")

    # ── Tab: Data ────────────────────────────────────────────────

    def create_data_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(SPACING_XL, SPACING_XL, SPACING_XL, SPACING_XL)
        layout.setSpacing(SPACING_LG)

        retention_group = QGroupBox("Data Retention")
        retention_group.setStyleSheet(get_group_style())
        retention_layout = QVBoxLayout()
        retention_layout.setSpacing(SPACING_SM)

        self.enable_retention = QCheckBox("Auto-delete old entries")
        self.enable_retention.setChecked(self.config.get('enable_retention', False))
        self.enable_retention.setStyleSheet(get_checkbox_style())
        self.enable_retention.setAccessibleName("Enable retention checkbox")
        self.enable_retention.setToolTip("Automatically delete entries older than the specified number of days")
        self.enable_retention.toggled.connect(self._set_dirty)

        retention_time_layout = QHBoxLayout()
        retention_time_layout.setSpacing(SPACING_MD)
        retention_label = QLabel("Keep entries for (days):")
        retention_label.setStyleSheet(get_label_style())

        self.retention_days = QSpinBox()
        self.retention_days.setRange(1, 365)
        self.retention_days.setValue(self.config.get('retention_days', 30))
        self.retention_days.setStyleSheet(get_spinbox_style())
        self.retention_days.setAccessibleName("Retention days spinbox")
        self.retention_days.setSuffix(" days")
        self.retention_days.valueChanged.connect(self._set_dirty)

        retention_time_layout.addWidget(retention_label)
        retention_time_layout.addWidget(self.retention_days)
        retention_time_layout.addStretch()

        max_entries_layout = QHBoxLayout()
        max_entries_layout.setSpacing(SPACING_MD)
        max_label = QLabel("Maximum entries:")
        max_label.setStyleSheet(get_label_style())

        self.max_entries = QSpinBox()
        self.max_entries.setRange(100, 10000)
        self.max_entries.setSingleStep(100)
        self.max_entries.setValue(self.config.get('max_entries', 1000))
        self.max_entries.setStyleSheet(get_spinbox_style())
        self.max_entries.setAccessibleName("Max entries spinbox")
        self.max_entries.valueChanged.connect(self._set_dirty)

        max_entries_layout.addWidget(max_label)
        max_entries_layout.addWidget(self.max_entries)
        max_entries_layout.addStretch()

        retention_layout.addWidget(self.enable_retention)
        retention_layout.addLayout(retention_time_layout)
        retention_layout.addLayout(max_entries_layout)
        retention_layout.addWidget(self._help_label("Pinned entries are always kept regardless of retention policy."))
        retention_group.setLayout(retention_layout)
        layout.addWidget(retention_group)

        self.enable_retention.toggled.connect(
            lambda checked: [self.retention_days.setEnabled(checked), self.max_entries.setEnabled(checked)]
        )
        self.retention_days.setEnabled(self.enable_retention.isChecked())
        self.max_entries.setEnabled(self.enable_retention.isChecked())

        backup_group = QGroupBox("Backup & Sync")
        backup_group.setStyleSheet(get_group_style())
        backup_layout = QVBoxLayout()
        backup_layout.setSpacing(SPACING_SM)

        self.auto_backup = QCheckBox("Daily auto-backup")
        self.auto_backup.setChecked(self.config.get('auto_backup', False))
        self.auto_backup.setStyleSheet(get_checkbox_style())
        self.auto_backup.setAccessibleName("Auto-backup checkbox")
        self.auto_backup.setToolTip("Automatically back up the vault daily to the specified folder")
        self.auto_backup.toggled.connect(self._set_dirty)

        backup_path_layout = QHBoxLayout()
        backup_path_layout.setSpacing(SPACING_SM)
        path_label = QLabel("Backup folder:")
        path_label.setStyleSheet(get_label_style())

        self.backup_path = QLineEdit()
        self.backup_path.setText(self.config.get('backup_path', ''))
        self.backup_path.setPlaceholderText("Select a folder…")
        self.backup_path.setStyleSheet(get_input_style())
        self.backup_path.setAccessibleName("Backup folder path input")
        self.backup_path.textChanged.connect(self._set_dirty)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setStyleSheet(get_button_style())
        self.browse_btn.setAccessibleName("Browse backup folder button")
        self.browse_btn.clicked.connect(self.browse_backup_path)

        backup_path_layout.addWidget(path_label)
        backup_path_layout.addWidget(self.backup_path, 1)
        backup_path_layout.addWidget(self.browse_btn)

        backup_layout.addWidget(self.auto_backup)
        backup_layout.addLayout(backup_path_layout)
        backup_layout.addWidget(self._help_label("Vault file and salt are copied to the backup folder daily."))
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)

        self.auto_backup.toggled.connect(
            lambda checked: [self.backup_path.setEnabled(checked), self.browse_btn.setEnabled(checked)]
        )
        self.backup_path.setEnabled(self.auto_backup.isChecked())
        self.browse_btn.setEnabled(self.auto_backup.isChecked())

        layout.addStretch()
        self.tabs.addTab(self._wrap_scroll(widget), "💾 Data")

    # ── Tab: Hotkeys ─────────────────────────────────────────────

    def create_hotkeys_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(SPACING_XL, SPACING_XL, SPACING_XL, SPACING_XL)
        layout.setSpacing(SPACING_LG)

        hotkeys_group = QGroupBox("Global Hotkeys")
        hotkeys_group.setStyleSheet(get_group_style())
        hotkeys_layout = QGridLayout()
        hotkeys_layout.setSpacing(SPACING_SM)

        hotkey_configs = [
            ("Command Palette", "command_palette", "Ctrl+Shift+P"),
            ("Paste Ring", "paste_ring", "Ctrl+Shift+V"),
            ("Quick Search", "quick_search", "Ctrl+Shift+F"),
            ("Toggle Pin", "toggle_pin", "Ctrl+Shift+L"),
            ("Pause Capture", "pause_capture_key", "Ctrl+Shift+Q"),
        ]

        self.hotkey_inputs = {}
        for i, (label_text, key, default) in enumerate(hotkey_configs):
            label_widget = QLabel(label_text + ":")
            label_widget.setStyleSheet(get_label_style())

            input_widget = QLineEdit()
            input_widget.setText(self.config.get(f'hotkey_{key}', default))
            input_widget.setStyleSheet(get_input_style())
            input_widget.setAccessibleName(f"{label_text} hotkey input")
            input_widget.setToolTip(f"Keyboard shortcut for {label_text}")
            input_widget.textChanged.connect(self._set_dirty)
            self.hotkey_inputs[key] = input_widget

            hotkeys_layout.addWidget(label_widget, i, 0)
            hotkeys_layout.addWidget(input_widget, i, 1)

        hotkeys_layout.addWidget(self._help_label("Use standard notation: Ctrl, Shift, Alt, Meta + key."), len(hotkey_configs), 0, 1, 2)
        hotkeys_group.setLayout(hotkeys_layout)
        layout.addWidget(hotkeys_group)

        startup_group = QGroupBox("System")
        startup_group.setStyleSheet(get_group_style())
        startup_layout = QVBoxLayout()
        startup_layout.setSpacing(SPACING_SM)

        self.autostart = QCheckBox("Launch on system startup")
        self.autostart.setChecked(self.config.get('autostart', False))
        self.autostart.setStyleSheet(get_checkbox_style())
        self.autostart.setAccessibleName("Autostart checkbox")
        self.autostart.setToolTip("Start ClipVault automatically when the system boots")
        self.autostart.toggled.connect(self._set_dirty)

        self.start_minimized = QCheckBox("Start minimized to tray")
        self.start_minimized.setChecked(self.config.get('start_minimized', False))
        self.start_minimized.setStyleSheet(get_checkbox_style())
        self.start_minimized.setAccessibleName("Start minimized checkbox")
        self.start_minimized.setToolTip("Start hidden in the system tray")
        self.start_minimized.toggled.connect(self._set_dirty)

        startup_layout.addWidget(self.autostart)
        startup_layout.addWidget(self.start_minimized)
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        layout.addStretch()
        self.tabs.addTab(self._wrap_scroll(widget), "⌨ Hotkeys")

    # ── Actions ──────────────────────────────────────────────────

    def _clear_search_history(self):
        from clipvault.config import SEARCH_HISTORY_FILE
        try:
            if SEARCH_HISTORY_FILE.exists():
                SEARCH_HISTORY_FILE.unlink()
        except Exception:
            pass
        QMessageBox.information(self, "Cleared", "Search history cleared.")

    def _on_intensity_changed(self, value: int):
        self.intensity_label.setText(f"Cyber Mode: {value}%")
        self.intensity_preview.emit(value / 100.0)
        self._set_dirty()

    def _validate_regex(self) -> bool:
        patterns = self.block_patterns.toPlainText().strip()
        if not patterns:
            self.regex_status.setText("")
            self.regex_status.setStyleSheet(get_label_style(CYBER_TEXT_DIM, FONT_SIZE_XS))
            return True

        invalid = []
        for i, line in enumerate(patterns.split('\n'), 1):
            line = line.strip()
            if not line:
                continue
            try:
                re.compile(line)
            except re.error:
                invalid.append(str(i))

        if invalid:
            self.regex_status.setText(f"⚠ Invalid regex on line(s): {', '.join(invalid)}")
            self.regex_status.setStyleSheet(get_label_style(CYBER_HOT_PINK, FONT_SIZE_XS))
            return False
        else:
            self.regex_status.setText("✓ All patterns valid")
            self.regex_status.setStyleSheet(get_label_style(CYBER_NEON_GREEN, FONT_SIZE_XS))
            return True

    def _collect_settings(self) -> dict:
        cfg = {}
        cfg['cyber_intensity'] = self.intensity_slider.value() / 100
        cfg['reduce_motion'] = self.reduce_motion.isChecked()
        cfg['disable_bg'] = self.disable_bg.isChecked()
        cfg['font_size'] = self.font_size.value()
        cfg['pause_capture'] = self.pause_capture.isChecked()
        cfg['incognito_mode'] = self.incognito_mode.isChecked()
        cfg['enable_ocr'] = self.enable_ocr.isChecked()
        cfg['enable_search_history'] = self.enable_search_history.isChecked()
        cfg['exclude_apps'] = self.exclude_apps.text()
        cfg['block_patterns'] = self.block_patterns.toPlainText()
        cfg['auto_lock'] = self.auto_lock.isChecked()
        cfg['lock_time'] = self.lock_time.value()
        cfg['block_sensitive'] = self.block_sensitive.isChecked()
        cfg['ephemeral_otp'] = self.ephemeral_otp.isChecked()
        cfg['enable_retention'] = self.enable_retention.isChecked()
        cfg['retention_days'] = self.retention_days.value()
        cfg['max_entries'] = self.max_entries.value()
        cfg['auto_backup'] = self.auto_backup.isChecked()
        cfg['backup_path'] = self.backup_path.text()
        for key, input_widget in self.hotkey_inputs.items():
            cfg[f'hotkey_{key}'] = input_widget.text()
        cfg['autostart'] = self.autostart.isChecked()
        cfg['start_minimized'] = self.start_minimized.isChecked()
        return cfg

    def _apply_to_ui(self, config: dict):
        self.intensity_slider.setValue(int(config.get('cyber_intensity', 0.3) * 100))
        self.reduce_motion.setChecked(config.get('reduce_motion', False))
        self.disable_bg.setChecked(config.get('disable_bg', False))
        self.font_size.setValue(config.get('font_size', 12))
        self.pause_capture.setChecked(config.get('pause_capture', False))
        self.incognito_mode.setChecked(config.get('incognito_mode', False))
        self.enable_ocr.setChecked(config.get('enable_ocr', False))
        self.enable_search_history.setChecked(config.get('enable_search_history', True))
        self.exclude_apps.setText(config.get('exclude_apps', ''))
        self.block_patterns.setPlainText(config.get('block_patterns', ''))
        self.auto_lock.setChecked(config.get('auto_lock', False))
        self.lock_time.setValue(config.get('lock_time', 10))
        self.block_sensitive.setChecked(config.get('block_sensitive', True))
        self.ephemeral_otp.setChecked(config.get('ephemeral_otp', True))
        self.enable_retention.setChecked(config.get('enable_retention', False))
        self.retention_days.setValue(config.get('retention_days', 30))
        self.max_entries.setValue(config.get('max_entries', 1000))
        self.auto_backup.setChecked(config.get('auto_backup', False))
        self.backup_path.setText(config.get('backup_path', ''))
        for key, input_widget in self.hotkey_inputs.items():
            input_widget.setText(config.get(f'hotkey_{key}', input_widget.text()))
        self.autostart.setChecked(config.get('autostart', False))
        self.start_minimized.setChecked(config.get('start_minimized', False))

    def reset_defaults(self):
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to their default values?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        from clipvault.config import DEFAULT_CONFIG
        self.config = dict(DEFAULT_CONFIG)
        self._apply_to_ui(self.config)
        self._dirty = True

    def browse_backup_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if folder:
            self.backup_path.setText(folder)

    def change_pin(self):
        dlg = PinDialog(self.config.get('pin_hint', ''), self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        old_pin, new_pin = dlg.get_pins()
        if not new_pin:
            QMessageBox.warning(self, "No New PIN", "Please enter a new PIN to change it.")
            return
        if not self.parent() or not hasattr(self.parent(), 'storage'):
            QMessageBox.warning(self, "Error", "Storage not available to change PIN.")
            return
        storage: StorageManager = self.parent().storage
        if not storage.set_pin(old_pin):
            QMessageBox.warning(self, "Invalid PIN", "The current PIN is incorrect.")
            return
        entries = storage.load_entries()
        if storage.set_pin(new_pin):
            storage.save_entries(entries)
            self.parent().storage = storage
            QMessageBox.information(self, "PIN Changed", "PIN changed successfully. The vault has been re-encrypted.")
        else:
            QMessageBox.warning(self, "Error", "Failed to set new PIN.")

    def apply_settings(self):
        if not self._validate_regex():
            QMessageBox.warning(self, "Invalid Patterns", "Please fix invalid regex patterns before applying.")
            return
        self.config = self._collect_settings()
        self.settings_changed.emit(self.config)
        self._dirty = False

    def save_settings(self):
        if not self._validate_regex():
            QMessageBox.warning(self, "Invalid Patterns", "Please fix invalid regex patterns before saving.")
            return
        self.config = self._collect_settings()
        self.settings_changed.emit(self.config)
        self._dirty = False
        self.accept()

    def closeEvent(self, event):
        if self._dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Discard and close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        super().closeEvent(event)
