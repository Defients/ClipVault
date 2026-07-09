"""ClipboardEntry model with auto-detection, serialization, and similarity."""

import hashlib
import re
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any
from difflib import SequenceMatcher

from clipvault.config import EntryType, SENSITIVE_PATTERNS, MAX_PREVIEW_LENGTH
from clipvault.utils import generate_id, make_preview


class ClipboardEntry:
    """Enhanced clipboard entry with metadata"""

    def __init__(self, text: str, timestamp: Optional[datetime] = None,
                 entry_id: Optional[str] = None, pinned: bool = False,
                 entry_type: str = None, tags: List[str] = None,
                 board: str = None, color: str = None, note: str = None,
                 ephemeral_ttl: int = None, source_app: str = None,
                 image_data: str = None, ocr_text: str = None):
        self.id = entry_id or generate_id(text, timestamp)
        self.text = text
        self.timestamp = timestamp or datetime.now()
        self.pinned = pinned
        self.entry_type = entry_type or self._detect_type(text)
        self.tags = tags or []
        self.board = board
        self.color = color
        self.note = note
        self.ephemeral_ttl = ephemeral_ttl
        self.source_app = source_app
        self.image_data = image_data
        self.ocr_text = ocr_text
        self.duplicate_count = 1
        self.last_used = timestamp or datetime.now()

    @staticmethod
    def _generate_id(text: str, timestamp: Optional[datetime]) -> str:
        return generate_id(text, timestamp)

    def _detect_type(self, text: str) -> str:
        """Auto-detect entry type"""
        if re.match(r'^https?://', text):
            return EntryType.URL
        elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', text):
            return EntryType.EMAIL
        elif re.match(r'^[A-Za-z]:[\\\/]|^[\/~]', text):
            return EntryType.PATH
        elif any(re.search(pattern, text) for pattern in SENSITIVE_PATTERNS.values()):
            return EntryType.SENSITIVE
        elif re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', text):
            return EntryType.NUMBER
        elif any(kw in text.lower() for kw in ['def ', 'function', 'class ', 'import ', 'var ', 'const ']):
            return EntryType.CODE
        return EntryType.TEXT

    def to_dict(self) -> Dict[str, Any]:
        d = {
            'id': self.id,
            'text': self.text,
            'timestamp': self.timestamp.isoformat(),
            'pinned': self.pinned,
            'entry_type': self.entry_type,
            'tags': self.tags,
            'board': self.board,
            'color': self.color,
            'note': self.note,
            'ephemeral_ttl': self.ephemeral_ttl,
            'source_app': self.source_app,
            'duplicate_count': self.duplicate_count,
            'last_used': self.last_used.isoformat()
        }
        if self.image_data:
            d['image_data'] = self.image_data
        if self.ocr_text:
            d['ocr_text'] = self.ocr_text
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClipboardEntry':
        entry = cls(
            text=data['text'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            entry_id=data['id'],
            pinned=data.get('pinned', False),
            entry_type=data.get('entry_type', EntryType.TEXT),
            tags=data.get('tags', []),
            board=data.get('board'),
            color=data.get('color'),
            note=data.get('note'),
            ephemeral_ttl=data.get('ephemeral_ttl'),
            source_app=data.get('source_app'),
            image_data=data.get('image_data'),
            ocr_text=data.get('ocr_text'),
        )
        entry.duplicate_count = data.get('duplicate_count', 1)
        if 'last_used' in data:
            entry.last_used = datetime.fromisoformat(data['last_used'])
        return entry

    def preview(self, length: int = MAX_PREVIEW_LENGTH) -> str:
        if self.image_data:
            if self.ocr_text:
                snippet = make_preview(self.ocr_text, length)
                return f"[Image: {snippet}]"
            return "[Image]"
        return make_preview(self.text, length)

    def is_similar_to(self, other: 'ClipboardEntry', threshold: float = 0.85) -> bool:
        """Check if entries are similar"""
        if self.image_data and other.image_data:
            return self.image_data == other.image_data
        if self.image_data or other.image_data:
            return False
        return SequenceMatcher(None, self.text, other.text).ratio() >= threshold
