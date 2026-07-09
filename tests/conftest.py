"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path

@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect all ClipVault data paths to a temp directory."""
    from clipvault import config as cfg

    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cfg, "DATA_FILE", tmp_path / "vault.encrypted")
    monkeypatch.setattr(cfg, "SALT_FILE", tmp_path / "salt")
    monkeypatch.setattr(cfg, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(cfg, "BOARDS_FILE", tmp_path / "boards.json")
    monkeypatch.setattr(cfg, "LOG_FILE", tmp_path / "clipvault.log")
    monkeypatch.setattr(cfg, "SEARCH_HISTORY_FILE", tmp_path / "search_history.json")

    # Also patch the names imported into storage modules
    from clipvault.storage import vault as vault_mod
    monkeypatch.setattr(vault_mod, "DATA_FILE", tmp_path / "vault.encrypted")
    monkeypatch.setattr(vault_mod, "SALT_FILE", tmp_path / "salt")

    from clipvault.storage import config_store as cs_mod
    monkeypatch.setattr(cs_mod, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(cs_mod, "BOARDS_FILE", tmp_path / "boards.json")
    monkeypatch.setattr(cs_mod, "SEARCH_HISTORY_FILE", tmp_path / "search_history.json")

    return tmp_path
