"""Tests for PasteRing cycling, timeout, and reset logic."""

import time
from datetime import datetime

from clipvault.models.entry import ClipboardEntry
from clipvault.paste_ring import PasteRing


def _make_entries(n):
    return [ClipboardEntry(text=f"entry-{i}", timestamp=datetime.now()) for i in range(n)]


class TestPasteRing:
    def test_cycles_through_entries(self):
        entries = _make_entries(5)
        ring = PasteRing(lambda: entries, timeout=60, enabled=True)
        results = [ring.next() for _ in range(5)]
        assert all(r is not None for r in results)
        texts = [r.text for r in results]
        # next() advances index before returning: first call returns entry-1
        assert texts == ["entry-1", "entry-2", "entry-3", "entry-4", "entry-0"]

    def test_wraps_around(self):
        entries = _make_entries(3)
        ring = PasteRing(lambda: entries, timeout=60, enabled=True)
        r1 = ring.next()  # entry-1
        r2 = ring.next()  # entry-2
        r3 = ring.next()  # entry-0
        r4 = ring.next()  # entry-1 (wrapped)
        assert r1.text == "entry-1"
        assert r2.text == "entry-2"
        assert r3.text == "entry-0"
        assert r4.text == "entry-1"

    def test_disabled_returns_none(self):
        entries = _make_entries(3)
        ring = PasteRing(lambda: entries, timeout=60, enabled=False)
        assert ring.next() is None

    def test_empty_entries_returns_none(self):
        ring = PasteRing(lambda: [], timeout=60, enabled=True)
        assert ring.next() is None

    def test_reset_clears_session(self):
        entries = _make_entries(3)
        ring = PasteRing(lambda: entries, timeout=60, enabled=True)
        ring.next()
        ring.reset()
        assert not ring.active()

    def test_timeout_expires_session(self):
        entries = _make_entries(3)
        ring = PasteRing(lambda: entries, timeout=1, enabled=True)
        ring.next()
        time.sleep(1.1)
        assert not ring.active()

    def test_prev_goes_backward(self):
        entries = _make_entries(3)
        ring = PasteRing(lambda: entries, timeout=60, enabled=True)
        ring.next()
        result = ring.prev()
        assert result is not None
        assert result.text == "entry-0"
