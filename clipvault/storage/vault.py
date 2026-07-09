"""Encrypted vault storage for clipboard entries."""

import json
import base64
import os
from typing import Optional, List

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from clipvault.config import DATA_FILE, SALT_FILE
from clipvault.models.entry import ClipboardEntry
from clipvault.utils import setup_logger, generate_id

_log = setup_logger("clipvault.storage")

PBKDF2_ITERATIONS = 600_000
_PBKDF2_LEGACY_ITERATIONS = 100_000


class StorageManager:
    """Enhanced storage manager with encryption support"""

    def __init__(self):
        self.fernet: Optional[Fernet] = None
        self._ensure_dirs()

    def _ensure_dirs(self):
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    def set_pin(self, pin: str, iterations: int = PBKDF2_ITERATIONS) -> bool:
        """Set up encryption with the given PIN.

        *iterations* defaults to 600 000 (OWASP 2023). When loading an existing
        vault created with the legacy 100 000-iteration count, call
        ``set_pin`` with ``iterations=_PBKDF2_LEGACY_ITERATIONS`` first, then
        re-save with the new default.
        """
        try:
            salt = self._get_or_create_salt()
            key = self._derive_key(pin, salt, iterations)
            self.fernet = Fernet(key)
            self._iterations = iterations
            self._last_pin = pin
            return True
        except Exception as e:
            _log.error("set_pin failed: %s", e)
            return False

    def _get_or_create_salt(self) -> bytes:
        if SALT_FILE.exists():
            return SALT_FILE.read_bytes()
        else:
            salt = os.urandom(16)
            SALT_FILE.write_bytes(salt)
            return salt

    def _derive_key(self, pin: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        key = base64.urlsafe_b64encode(kdf.derive(pin.encode()))
        return key

    def save_entries(self, entries: List[ClipboardEntry]) -> bool:
        """Save entries to encrypted file"""
        if not self.fernet:
            return False

        try:
            data = json.dumps([e.to_dict() for e in entries])
            encrypted = self.fernet.encrypt(data.encode())
            DATA_FILE.write_bytes(encrypted)
            return True
        except Exception as e:
            _log.error("Save error: %s", e)
            return False

    def load_entries(self) -> List[ClipboardEntry]:
        """Load entries from encrypted file.

        If decryption fails with the current iteration count, retry with the
        legacy 100 000-iteration count for backward compatibility.
        """
        if not self.fernet or not DATA_FILE.exists():
            return []

        try:
            encrypted = DATA_FILE.read_bytes()
            decrypted = self.fernet.decrypt(encrypted)
            data = json.loads(decrypted)
            return [ClipboardEntry.from_dict(d) for d in data]
        except Exception:
            # Retry with legacy iterations if we haven't already
            current_iters = getattr(self, '_iterations', PBKDF2_ITERATIONS)
            if current_iters != _PBKDF2_LEGACY_ITERATIONS:
                _log.info("Retrying decryption with legacy iterations")
                try:
                    salt = self._get_or_create_salt()
                    key = self._derive_key(
                        self._last_pin, salt, _PBKDF2_LEGACY_ITERATIONS
                    )
                    legacy_fernet = Fernet(key)
                    encrypted = DATA_FILE.read_bytes()
                    decrypted = legacy_fernet.decrypt(encrypted)
                    data = json.loads(decrypted)
                    _log.info("Legacy decryption succeeded")
                    return [ClipboardEntry.from_dict(d) for d in data]
                except Exception as e2:
                    _log.error("Legacy load also failed: %s", e2)
            else:
                _log.error("Load error: decryption failed")
            return []
