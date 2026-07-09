"""Tests for retention policy and capture filters."""

from datetime import datetime, timedelta

from clipvault.models.entry import ClipboardEntry
from clipvault.capture.filters import should_capture


class TestRetentionPolicy:
    def _apply_retention(self, entries, config):
        """Replicate ClipVaultMain.apply_retention_policy logic."""
        if not config.get('enable_retention', False):
            return entries

        retention_days = config.get('retention_days', 30)
        max_entries = config.get('max_entries', 1000)

        cutoff = datetime.now() - timedelta(days=retention_days)
        entries = [e for e in entries if e.timestamp > cutoff or e.pinned]

        if len(entries) > max_entries:
            pinned = [e for e in entries if e.pinned]
            unpinned = [e for e in entries if not e.pinned]
            unpinned.sort(key=lambda e: e.timestamp, reverse=True)
            entries = pinned + unpinned[:max_entries - len(pinned)]

        return entries

    def test_no_retention_when_disabled(self):
        entries = [ClipboardEntry("old", timestamp=datetime(2020, 1, 1))]
        result = self._apply_retention(entries, {"enable_retention": False})
        assert len(result) == 1

    def test_old_entries_removed(self):
        entries = [
            ClipboardEntry("old", timestamp=datetime(2020, 1, 1)),
            ClipboardEntry("new", timestamp=datetime.now()),
        ]
        result = self._apply_retention(entries, {
            "enable_retention": True,
            "retention_days": 30,
            "max_entries": 1000,
        })
        assert len(result) == 1
        assert result[0].text == "new"

    def test_pinned_entries_kept(self):
        entries = [
            ClipboardEntry("old pinned", timestamp=datetime(2020, 1, 1), pinned=True),
            ClipboardEntry("new", timestamp=datetime.now()),
        ]
        result = self._apply_retention(entries, {
            "enable_retention": True,
            "retention_days": 30,
            "max_entries": 1000,
        })
        assert len(result) == 2

    def test_max_entries_limit(self):
        entries = []
        for i in range(10):
            entries.append(ClipboardEntry(f"entry{i}", timestamp=datetime.now() - timedelta(seconds=i)))

        result = self._apply_retention(entries, {
            "enable_retention": True,
            "retention_days": 365,
            "max_entries": 5,
        })
        assert len(result) <= 5


class TestShouldCapture:
    def test_normal_text(self):
        assert should_capture("hello world", {}) is True

    def test_block_sensitive_credit_card(self):
        assert should_capture("4539-1488-0343-6462", {"block_sensitive": True}) is False

    def test_allow_sensitive_when_disabled(self):
        assert should_capture("4539-1488-0343-6462", {"block_sensitive": False}) is True

    def test_block_pattern(self):
        config = {"block_patterns": "password"}
        assert should_capture("my password is x", config) is False
        assert should_capture("no match here", config) is True

    def test_invalid_regex_ignored(self):
        config = {"block_patterns": "[invalid("}
        assert should_capture("test", config) is True

    def test_exclude_apps_blocks_matching(self):
        config = {"exclude_apps": "KeePass, 1Password"}
        assert should_capture("hello", config, source_app="KeePass") is False
        assert should_capture("hello", config, source_app="1Password") is False

    def test_exclude_apps_allows_non_matching(self):
        config = {"exclude_apps": "KeePass"}
        assert should_capture("hello", config, source_app="Notepad") is True

    def test_exclude_apps_empty_allows_all(self):
        config = {"exclude_apps": ""}
        assert should_capture("hello", config, source_app="Anything") is True
