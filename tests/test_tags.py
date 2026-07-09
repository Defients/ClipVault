"""Tests for tag system — add/remove, serialization, color assignment."""

from datetime import datetime

from clipvault.models.entry import ClipboardEntry
from clipvault.ui.tag_editor import get_tag_color


class TestTags:
    def test_add_tag(self):
        entry = ClipboardEntry(text="hello", timestamp=datetime.now())
        entry.tags.append("important")
        assert "important" in entry.tags

    def test_remove_tag(self):
        entry = ClipboardEntry(text="hello", timestamp=datetime.now(), tags=["a", "b"])
        entry.tags.remove("a")
        assert "a" not in entry.tags
        assert entry.tags == ["b"]

    def test_serialization_round_trip(self):
        entry = ClipboardEntry(text="hello", timestamp=datetime.now(), tags=["work", "urgent"])
        d = entry.to_dict()
        assert d["tags"] == ["work", "urgent"]
        restored = ClipboardEntry.from_dict(d)
        assert restored.tags == ["work", "urgent"]

    def test_empty_tags_default(self):
        entry = ClipboardEntry(text="hello", timestamp=datetime.now())
        assert entry.tags == []

    def test_tag_color_deterministic(self):
        c1 = get_tag_color("work")
        c2 = get_tag_color("work")
        assert c1 == c2

    def test_tag_color_different_tags(self):
        tags = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        colors = [get_tag_color(t) for t in tags]
        assert len(set(colors)) > 1

    def test_filter_by_tag(self):
        entries = [
            ClipboardEntry(text="a", timestamp=datetime.now(), tags=["work"]),
            ClipboardEntry(text="b", timestamp=datetime.now(), tags=["personal"]),
            ClipboardEntry(text="c", timestamp=datetime.now(), tags=["work", "urgent"]),
        ]
        tagged = [e for e in entries if "work" in e.tags]
        assert len(tagged) == 2
        assert tagged[0].text == "a"
        assert tagged[1].text == "c"
