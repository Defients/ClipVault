"""Tests for global hotkey manager and hotkey string parsing."""

from clipvault.hotkeys import parse_hotkey, GlobalHotkeyManager


class TestParseHotkey:
    def test_ctrl_shift_v(self):
        assert parse_hotkey("Ctrl+Shift+V") == "<ctrl>+<shift>+v"

    def test_alt_f1(self):
        assert parse_hotkey("Alt+F1") == "<alt>+<f1>"

    def test_ctrl_only(self):
        assert parse_hotkey("Ctrl+C") == "<ctrl>+c"

    def test_win_key(self):
        assert parse_hotkey("Win+V") == "<cmd>+v"

    def test_meta_key(self):
        assert parse_hotkey("Meta+S") == "<cmd>+s"


class TestGlobalHotkeyManager:
    def test_start_without_pynput(self):
        mgr = GlobalHotkeyManager({}, {})
        mgr.start()
        mgr.stop()

    def test_update_hotkeys(self):
        mgr = GlobalHotkeyManager({}, {})
        mgr.update_hotkeys({"hotkey_command_palette": "Ctrl+Shift+P"})
        mgr.stop()

    def test_callbacks_not_required_for_start(self):
        mgr = GlobalHotkeyManager({}, {})
        mgr.start()
        mgr.stop()
