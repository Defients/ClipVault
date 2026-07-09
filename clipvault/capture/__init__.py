"""Capture package."""

from clipvault.capture.monitor import ClipboardMonitor
from clipvault.capture.filters import should_capture

__all__ = ["ClipboardMonitor", "should_capture"]
