"""Tests for StorageManager (encrypted vault round-trip)."""

from clipvault.models.entry import ClipboardEntry
from clipvault.storage.vault import StorageManager
from clipvault.storage.config_store import ConfigStore


class TestStorageManager:
    def test_set_pin(self, tmp_data_dir):
        sm = StorageManager()
        assert sm.set_pin("1234") is True
        assert sm.fernet is not None

    def test_save_load_round_trip(self, tmp_data_dir):
        sm = StorageManager()
        assert sm.set_pin("mypin") is True

        entries = [
            ClipboardEntry("first entry"),
            ClipboardEntry("second entry", pinned=True),
            ClipboardEntry("https://example.com"),
        ]
        assert sm.save_entries(entries) is True

        loaded = sm.load_entries()
        assert len(loaded) == 3
        assert loaded[0].text == "first entry"
        assert loaded[1].text == "second entry"
        assert loaded[1].pinned is True
        assert loaded[2].text == "https://example.com"

    def test_load_empty(self, tmp_data_dir):
        sm = StorageManager()
        assert sm.set_pin("1234") is True
        loaded = sm.load_entries()
        assert loaded == []

    def test_load_wrong_pin(self, tmp_data_dir):
        sm1 = StorageManager()
        sm1.set_pin("correct")
        sm1.save_entries([ClipboardEntry("secret")])

        sm2 = StorageManager()
        sm2.set_pin("wrong")
        loaded = sm2.load_entries()
        assert loaded == []

    def test_save_without_pin(self, tmp_data_dir):
        sm = StorageManager()
        assert sm.save_entries([ClipboardEntry("test")]) is False


class TestConfigStore:
    def test_config_round_trip(self, tmp_data_dir):
        cs = ConfigStore()
        config = {"cyber_intensity": 0.8, "font_size": 14}
        cs.save_config(config)
        loaded = cs.load_config()
        assert loaded["cyber_intensity"] == 0.8
        assert loaded["font_size"] == 14

    def test_config_defaults(self, tmp_data_dir):
        cs = ConfigStore()
        loaded = cs.load_config()
        assert "cyber_intensity" in loaded
        assert "font_size" in loaded

    def test_boards_round_trip(self, tmp_data_dir):
        cs = ConfigStore()
        boards = {"default": [], "work": ["id1", "id2"]}
        cs.save_boards(boards)
        loaded = cs.load_boards()
        assert "work" in loaded
        assert loaded["work"] == ["id1", "id2"]

    def test_boards_defaults(self, tmp_data_dir):
        cs = ConfigStore()
        loaded = cs.load_boards()
        assert "default" in loaded
