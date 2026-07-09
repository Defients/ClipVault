"""Tests for OCR module — availability and graceful fallback."""

from clipvault.ocr import is_available, extract_text


class TestOCR:
    def test_is_available_returns_bool(self):
        assert isinstance(is_available(), bool)

    def test_extract_text_invalid_input_returns_none(self):
        result = extract_text("not-valid-base64!!!")
        assert result is None

    def test_extract_text_empty_string_returns_none(self):
        result = extract_text("")
        assert result is None

    def test_extract_text_none_returns_none(self):
        result = extract_text(None)
        assert result is None
