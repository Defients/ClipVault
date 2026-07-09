"""Filter logic for clipboard capture decisions."""

import re
from typing import Dict, Any

from clipvault.config import SENSITIVE_PATTERNS
from clipvault.utils import setup_logger

_log = setup_logger("clipvault.capture")


def should_capture(text: str, config: Dict[str, Any], source_app: str = '') -> bool:
    """Check if text should be captured based on filters.

    Returns True if the text passes all block-pattern, sensitive-data, and
    source-app exclusion filters.
    """
    exclude_apps = config.get('exclude_apps', '')
    if exclude_apps and source_app:
        excluded = [a.strip().lower() for a in exclude_apps.split(',') if a.strip()]
        for app in excluded:
            if app in source_app.lower():
                return False

    patterns = config.get('block_patterns', '').split('\n')
    for pattern in patterns:
        if pattern.strip():
            try:
                if re.search(pattern.strip(), text):
                    return False
            except re.error as e:
                _log.warning("Invalid block pattern %r: %s", pattern, e)

    if config.get('block_sensitive', True):
        for pattern in SENSITIVE_PATTERNS.values():
            if re.search(pattern, text):
                return False

    return True
