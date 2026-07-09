"""OCR text extraction from clipboard images using pytesseract + Pillow."""

import base64
import io
from typing import Optional

from clipvault.utils import setup_logger

_log = setup_logger("clipvault.ocr")

_PILLOW_AVAILABLE = False
_PYTESSERACT_AVAILABLE = False

try:
    from PIL import Image as _PILImage
    _PILLOW_AVAILABLE = True
except ImportError:
    pass

try:
    import pytesseract as _pytesseract
    _PYTESSERACT_AVAILABLE = True
except ImportError:
    pass


def is_available() -> bool:
    """Return True if both Pillow and pytesseract are importable."""
    return _PILLOW_AVAILABLE and _PYTESSERACT_AVAILABLE


def extract_text(image_b64: str) -> Optional[str]:
    """Extract text from a base64-encoded PNG image via OCR.

    Returns the extracted text (stripped), or ``None`` if OCR is unavailable,
    the image is invalid, or no text was found.
    """
    if not is_available():
        return None

    try:
        raw = base64.b64decode(image_b64)
        img = _PILImage.open(io.BytesIO(raw))
        text = _pytesseract.image_to_string(img)
        text = text.strip()
        return text if text else None
    except Exception as e:
        _log.debug("OCR extraction failed: %s", e)
        return None
