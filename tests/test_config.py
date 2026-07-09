"""Tests for config constants and bug fixes."""

from clipvault.config import APP_NAME, DEFAULT_CONFIG


class TestConfig:
    def test_app_name_is_clipvault(self):
        assert APP_NAME == "ClipVault"

    def test_default_config_has_new_keys(self):
        assert "paste_ring_enabled" in DEFAULT_CONFIG
        assert "paste_ring_timeout" in DEFAULT_CONFIG
        assert "enable_ocr" in DEFAULT_CONFIG
        assert "enable_search_history" in DEFAULT_CONFIG

    def test_default_config_hotkeys(self):
        assert "hotkey_paste_ring" in DEFAULT_CONFIG
        assert DEFAULT_CONFIG["hotkey_paste_ring"] == "Ctrl+Shift+V"
