"""Plain-text config and boards persistence (not encrypted)."""

import json
from typing import Dict, Any, List

from clipvault.config import CONFIG_FILE, BOARDS_FILE, SEARCH_HISTORY_FILE, DEFAULT_CONFIG
from clipvault.utils import setup_logger

_log = setup_logger("clipvault.config_store")


class ConfigStore:
    """Persist application configuration and pin boards."""

    def save_config(self, config: dict):
        """Save app configuration"""
        try:
            CONFIG_FILE.write_text(json.dumps(config, indent=2))
        except Exception as e:
            _log.error("save_config: %s", e)

    def load_config(self) -> dict:
        """Load app configuration"""
        try:
            if CONFIG_FILE.exists():
                return json.loads(CONFIG_FILE.read_text())
        except Exception as e:
            _log.error("load_config: %s", e)
        return dict(DEFAULT_CONFIG)

    def save_boards(self, boards: dict):
        """Save pin boards"""
        try:
            BOARDS_FILE.write_text(json.dumps(boards, indent=2))
        except Exception as e:
            _log.error("save_boards: %s", e)

    def load_boards(self) -> dict:
        """Load pin boards"""
        try:
            if BOARDS_FILE.exists():
                return json.loads(BOARDS_FILE.read_text())
        except Exception as e:
            _log.error("load_boards: %s", e)
        return {"default": []}

    def save_search_history(self, queries: List[str]):
        """Save recent search queries."""
        try:
            SEARCH_HISTORY_FILE.write_text(json.dumps(queries[:50], indent=2))
        except Exception as e:
            _log.error("save_search_history: %s", e)

    def load_search_history(self) -> List[str]:
        """Load recent search queries."""
        try:
            if SEARCH_HISTORY_FILE.exists():
                return json.loads(SEARCH_HISTORY_FILE.read_text())
        except Exception as e:
            _log.error("load_search_history: %s", e)
        return []
