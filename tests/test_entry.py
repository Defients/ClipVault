"""Tests for ClipboardEntry model."""

from datetime import datetime

from clipvault.models.entry import ClipboardEntry, EntryType


class TestEntryType:
    def test_text_detection(self):
        e = ClipboardEntry("Hello world")
        assert e.entry_type == EntryType.TEXT

    def test_url_detection(self):
        e = ClipboardEntry("https://example.com")
        assert e.entry_type == EntryType.URL

    def test_email_detection(self):
        e = ClipboardEntry("user@example.com")
        assert e.entry_type == EntryType.EMAIL

    def test_path_detection(self):
        e = ClipboardEntry("C:\\Users\\test")
        assert e.entry_type == EntryType.PATH

    def test_number_detection(self):
        e = ClipboardEntry("42 + 3 * 7")
        assert e.entry_type == EntryType.NUMBER

    def test_code_detection(self):
        e = ClipboardEntry("def hello():")
        assert e.entry_type == EntryType.CODE

    def test_sensitive_detection(self):
        e = ClipboardEntry("4539-1488-0343-6462")
        assert e.entry_type == EntryType.SENSITIVE


class TestSerialization:
    def test_round_trip(self):
        e = ClipboardEntry(
            "test text",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            pinned=True,
            tags=["work", "important"],
            board="default",
            color="#00ffff",
            note="a note",
        )
        d = e.to_dict()
        assert d['text'] == "test text"
        assert d['pinned'] is True
        assert d['tags'] == ["work", "important"]

        restored = ClipboardEntry.from_dict(d)
        assert restored.text == e.text
        assert restored.pinned == e.pinned
        assert restored.tags == e.tags
        assert restored.board == e.board
        assert restored.color == e.color
        assert restored.note == e.note
        assert restored.id == e.id

    def test_from_dict_defaults(self):
        d = {
            'id': 'abc123',
            'text': 'hello',
            'timestamp': datetime(2025, 1, 1).isoformat(),
        }
        e = ClipboardEntry.from_dict(d)
        assert e.pinned is False
        assert e.tags == []
        assert e.duplicate_count == 1

    def test_ocr_text_serialization(self):
        e = ClipboardEntry(
            "[Image]",
            timestamp=datetime(2025, 1, 1),
            image_data="abc123",
            ocr_text="Hello World",
        )
        d = e.to_dict()
        assert d['ocr_text'] == "Hello World"
        restored = ClipboardEntry.from_dict(d)
        assert restored.ocr_text == "Hello World"

    def test_image_preview_with_ocr(self):
        e = ClipboardEntry(
            "[Image]",
            timestamp=datetime(2025, 1, 1),
            image_data="abc",
            ocr_text="Extracted text here",
        )
        preview = e.preview(20)
        assert "Extracted" in preview
        assert "[Image:" in preview

    def test_image_preview_without_ocr(self):
        e = ClipboardEntry(
            "[Image]",
            timestamp=datetime(2025, 1, 1),
            image_data="abc",
        )
        preview = e.preview()
        assert preview == "[Image]"


class TestPreview:
    def test_short_text(self):
        e = ClipboardEntry("Hello")
        assert e.preview() == "Hello"

    def test_long_text(self):
        e = ClipboardEntry("A" * 100)
        preview = e.preview(50)
        assert len(preview) == 53  # 50 + "..."
        assert preview.endswith("...")

    def test_multiline(self):
        e = ClipboardEntry("line1\nline2\nline3")
        assert "\n" not in e.preview()


class TestSimilarity:
    def test_identical(self):
        e1 = ClipboardEntry("hello world")
        e2 = ClipboardEntry("hello world")
        assert e1.is_similar_to(e2)

    def test_different(self):
        e1 = ClipboardEntry("hello world")
        e2 = ClipboardEntry("completely different text about cats")
        assert not e1.is_similar_to(e2)

    def test_threshold(self):
        e1 = ClipboardEntry("hello world this is a test")
        e2 = ClipboardEntry("hello world this is a pest")
        assert e1.is_similar_to(e2, threshold=0.8)
