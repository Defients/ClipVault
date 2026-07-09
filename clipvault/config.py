"""Constants, paths, color palette, entry types, and sensitive-data patterns."""

import sys
from pathlib import Path

# Application
APP_NAME = "ClipVault"
DATA_DIR = Path.home() / ".clipvault"
DATA_FILE = DATA_DIR / "vault.encrypted"
SALT_FILE = DATA_DIR / "salt"
CONFIG_FILE = DATA_DIR / "config.json"
BOARDS_FILE = DATA_DIR / "boards.json"
LOG_FILE = DATA_DIR / "clipvault.log"
SEARCH_HISTORY_FILE = DATA_DIR / "search_history.json"


def get_icon_path() -> Path:
    """Return the path to the application icon, whether running from source or a PyInstaller bundle."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "assets" / "CLIPVAULT.ico"

# Limits
MAX_PREVIEW_LENGTH = 50
MAX_CLIPBOARD_SIZE = 500000
MONITOR_INTERVAL = 500

# CyberTech Color Palette
CYBER_BG = "#070b15"
CYBER_BG_LIGHT = "#0d1220"
CYBER_PANEL = "#0a1018"
CYBER_NEON_BLUE = "#00ffff"
CYBER_NEON_PURPLE = "#ff00ff"
CYBER_NEON_GREEN = "#00ff9f"
CYBER_ELECTRIC_BLUE = "#0099ff"
CYBER_HOT_PINK = "#ff0066"
CYBER_YELLOW = "#ffff33"
CYBER_ORANGE = "#ff9500"
CYBER_GRID = "#142038"
CYBER_TEXT = "#f0ffff"
CYBER_TEXT_DIM = "#99aacc"

# ── Design Tokens ──────────────────────────────────────────────
# Spacing scale
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_2XL = 32

# Radius scale
RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 12
RADIUS_XL = 16
RADIUS_PILL = 999

# Typography
FONT_FAMILY = "'Consolas', 'Cascadia Code', 'SF Mono', monospace"
FONT_FAMILY_UI = "'Segoe UI', 'Inter', sans-serif"
FONT_SIZE_XS = 10
FONT_SIZE_SM = 11
FONT_SIZE_BASE = 13
FONT_SIZE_LG = 16
FONT_SIZE_XL = 20
FONT_SIZE_HERO = 24

# Motion
MOTION_FAST = 120
MOTION_NORMAL = 200
MOTION_SLOW = 350

# Border alpha helpers
BORDER_ALPHA_SUBTLE = "22"
BORDER_ALPHA_DEFAULT = "44"
BORDER_ALPHA_HOVER = "66"
BORDER_ALPHA_FOCUS = "88"


class EntryType:
    TEXT = "text"
    URL = "url"
    EMAIL = "email"
    CODE = "code"
    NUMBER = "number"
    PATH = "path"
    IMAGE = "image"
    SENSITIVE = "sensitive"


SENSITIVE_PATTERNS = {
    'credit_card': r'\b(?:\d[ -]*?){13,16}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'otp': r'\b\d{6}\b',
    'api_key': r'[A-Za-z0-9]{32,}',
}

DEFAULT_CONFIG = {
    "autostart": False,
    "start_minimized": False,
    "cyber_intensity": 0.3,
    "reduce_motion": False,
    "disable_bg": False,
    "font_size": 12,
    "pause_capture": False,
    "incognito_mode": False,
    "exclude_apps": "",
    "block_patterns": "",
    "auto_lock": False,
    "lock_time": 10,
    "block_sensitive": True,
    "ephemeral_otp": True,
    "enable_retention": False,
    "retention_days": 30,
    "max_entries": 1000,
    "auto_backup": False,
    "backup_path": "",
    "last_backup": None,
    "smart_dedupe": True,
    "confirm_delete": True,
    "hotkey_command_palette": "Ctrl+Shift+P",
    "hotkey_paste_ring": "Ctrl+Shift+V",
    "hotkey_quick_search": "Ctrl+Shift+F",
    "hotkey_toggle_pin": "Ctrl+Shift+L",
    "hotkey_pause_capture_key": "Ctrl+Shift+Q",
    "paste_ring_enabled": True,
    "paste_ring_timeout": 10,
    "enable_ocr": False,
    "enable_search_history": True,
}
