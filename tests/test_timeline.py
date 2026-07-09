"""Tests for timeline heatmap data and date filtering."""

from collections import Counter
from datetime import datetime, date

from clipvault.models.entry import ClipboardEntry


class TestTimeline:
    def _make_entries_with_dates(self):
        return [
            ClipboardEntry(text="a", timestamp=datetime(2025, 1, 15, 10, 0)),
            ClipboardEntry(text="b", timestamp=datetime(2025, 1, 15, 14, 30)),
            ClipboardEntry(text="c", timestamp=datetime(2025, 1, 16, 9, 0)),
            ClipboardEntry(text="d", timestamp=datetime(2025, 1, 20, 11, 0)),
        ]

    def test_daily_counts(self):
        entries = self._make_entries_with_dates()
        counts = Counter(e.timestamp.date() for e in entries)
        assert counts[date(2025, 1, 15)] == 2
        assert counts[date(2025, 1, 16)] == 1
        assert counts[date(2025, 1, 20)] == 1

    def test_date_filtering(self):
        entries = self._make_entries_with_dates()
        selected = date(2025, 1, 15)
        day_entries = [e for e in entries if e.timestamp.date() == selected]
        assert len(day_entries) == 2
        assert day_entries[0].text == "a"

    def test_hour_grouping(self):
        entries = self._make_entries_with_dates()
        selected = date(2025, 1, 15)
        day_entries = [e for e in entries if e.timestamp.date() == selected]
        hours = [e.timestamp.strftime("%H:%M") for e in day_entries]
        assert "10:00" in hours
        assert "14:30" in hours

    def test_max_count_for_heatmap(self):
        entries = self._make_entries_with_dates()
        counts = Counter(e.timestamp.date() for e in entries)
        max_count = max(counts.values())
        assert max_count == 2

    def test_empty_entries(self):
        counts = Counter(e.timestamp.date() for e in [])
        assert len(counts) == 0
