"""Tests for bulk actions logic."""

from datetime import datetime

from clipvault.models.entry import ClipboardEntry


def _make_entries(n):
    return [ClipboardEntry(text=f"entry-{i}", timestamp=datetime.now()) for i in range(n)]


class TestBulkActions:
    def test_bulk_copy_joins_text(self):
        entries = _make_entries(3)
        texts = [e.text for e in entries if not e.image_data]
        joined = "\n\n".join(texts)
        assert joined == "entry-0\n\nentry-1\n\nentry-2"

    def test_bulk_copy_skips_images(self):
        text_entry = ClipboardEntry(text="hello", timestamp=datetime.now())
        image_entry = ClipboardEntry(text="[Image]", timestamp=datetime.now(), image_data="abc")
        texts = [e.text for e in [text_entry, image_entry] if not e.image_data]
        joined = "\n\n".join(texts)
        assert joined == "hello"

    def test_bulk_pin_majority_unpinned(self):
        entries = _make_entries(5)
        entries[0].pinned = True
        entries[1].pinned = True
        entries[2].pinned = True
        majority_pinned = sum(1 for e in entries if e.pinned) > len(entries) // 2
        assert majority_pinned is True

    def test_bulk_pin_majority_pinned(self):
        entries = _make_entries(4)
        entries[0].pinned = True
        majority_pinned = sum(1 for e in entries if e.pinned) > len(entries) // 2
        assert majority_pinned is False

    def test_bulk_delete_filter(self):
        entries = _make_entries(5)
        to_delete = entries[:3]
        ids = {e.id for e in to_delete}
        remaining = [e for e in entries if e.id not in ids]
        assert len(remaining) == 2
        assert remaining[0].text == "entry-3"
        assert remaining[1].text == "entry-4"
