"""Utility helpers: logging, ID generation, preview truncation."""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from clipvault.config import LOG_FILE, MAX_PREVIEW_LENGTH


def setup_logger(name: str = "clipvault") -> logging.Logger:
    """Configure and return a logger that writes to the log file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except Exception:
        pass
    return logger


def generate_id(text: str, timestamp: Optional[datetime] = None) -> str:
    """Generate a deterministic 12-char hex ID from text + timestamp."""
    ts = timestamp or datetime.now()
    content = f"{text[:100]}{ts.isoformat()}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def make_preview(text: str, length: int = MAX_PREVIEW_LENGTH) -> str:
    """Return a single-line preview of *text*, truncated to *length*."""
    cleaned = text.replace("\n", " ").strip()
    if len(cleaned) > length:
        return cleaned[:length] + "..."
    return cleaned
