"""Global hotkey manager using pynput for system-wide shortcuts."""

from typing import Dict, Callable, Optional

from clipvault.utils import setup_logger

_log = setup_logger("clipvault.hotkeys")

_PYNPUT_AVAILABLE = False
try:
    from pynput import keyboard as _pkb
    _PYNPUT_AVAILABLE = True
except ImportError:
    _log.warning("pynput not installed — global hotkeys disabled (in-app shortcuts still work)")


_QT_TO_PYNPUT = {
    "Ctrl": "<ctrl>",
    "Shift": "<shift>",
    "Alt": "<alt>",
    "Meta": "<cmd>",
    "Win": "<cmd>",
    "Super": "<cmd>",
}


def parse_hotkey(qt_notation: str) -> str:
    """Convert Qt-style hotkey notation to pynput format.

    Examples:
        "Ctrl+Shift+V" -> "<ctrl>+<shift>+v"
        "Alt+F1"       -> "<alt>+f1"
    """
    parts = [p.strip() for p in qt_notation.split("+")]
    converted = []
    for part in parts:
        if part in _QT_TO_PYNPUT:
            converted.append(_QT_TO_PYNPUT[part])
        else:
            key_lower = part.lower()
            if len(key_lower) == 1:
                converted.append(key_lower)
            elif key_lower.startswith("f") and key_lower[1:].isdigit():
                converted.append(f"<{key_lower}>")
            else:
                converted.append(key_lower)
    return "+".join(converted)


class GlobalHotkeyManager:
    """Manage system-wide hotkeys via pynput with graceful fallback."""

    def __init__(self, config: dict, callbacks: Dict[str, Callable]):
        self.config = config
        self.callbacks = callbacks
        self._listener = None

    def start(self):
        if not _PYNPUT_AVAILABLE:
            return
        try:
            self._register()
        except Exception as e:
            _log.error("Failed to start global hotkeys: %s", e)

    def stop(self):
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def update_hotkeys(self, config: dict):
        self.config = config
        if not _PYNPUT_AVAILABLE:
            return
        self.stop()
        try:
            self._register()
        except Exception as e:
            _log.error("Failed to update global hotkeys: %s", e)

    def _register(self):
        if not _PYNPUT_AVAILABLE:
            return

        hotkey_map = {}
        key_map = {
            "command_palette": "hotkey_command_palette",
            "paste_ring": "hotkey_paste_ring",
            "quick_search": "hotkey_quick_search",
            "toggle_pin": "hotkey_toggle_pin",
            "pause_capture": "hotkey_pause_capture_key",
        }

        for action, config_key in key_map.items():
            if action not in self.callbacks:
                continue
            qt_seq = self.config.get(config_key, "")
            if not qt_seq:
                continue
            try:
                pynput_seq = parse_hotkey(qt_seq)
                hotkey_map[pynput_seq] = self.callbacks[action]
            except Exception as e:
                _log.warning("Failed to parse hotkey %s=%r: %s", config_key, qt_seq, e)

        if not hotkey_map:
            return

        self._listener = _pkb.GlobalHotKeysListener(hotkey_map)
        self._listener.start()
        _log.info("Global hotkeys registered: %s", list(hotkey_map.keys()))
