"""Field-level encryption for sensitive data.

Encrypts sensitive fields (patient names, ID numbers) at rest using AES-256-GCM.
Encryption key is loaded from environment variable ENCRYPTION_KEY.
"""

import base64
import os
import secrets
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Encryption key from environment (32 bytes = 256 bits)
_ENCRYPTION_KEY: Optional[bytes] = None


def _get_key() -> bytes:
    """Get or initialize encryption key."""
    global _ENCRYPTION_KEY
    if _ENCRYPTION_KEY is None:
        key_hex = os.environ.get("ENCRYPTION_KEY")
        if not key_hex:
            raise RuntimeError(
                "ENCRYPTION_KEY environment variable not set. "
                "Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        _ENCRYPTION_KEY = bytes.fromhex(key_hex)
    return _ENCRYPTION_KEY


def encrypt_field(plaintext: str) -> str:
    """Encrypt a string field using AES-256-GCM.

    Returns base64-encoded ciphertext with nonce prepended.
    Format: base64(nonce + ciphertext)
    """
    if not plaintext:
        return plaintext

    key = _get_key()
    nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    # Prepend nonce to ciphertext
    encrypted = nonce + ciphertext
    return base64.b64encode(encrypted).decode("ascii")


def decrypt_field(encrypted_value: str) -> str:
    """Decrypt a field encrypted with encrypt_field.

    Returns the original plaintext string.
    """
    if not encrypted_value:
        return encrypted_value

    key = _get_key()
    raw = base64.b64decode(encrypted_value)

    # Extract nonce (first 12 bytes) and ciphertext
    nonce = raw[:12]
    ciphertext = raw[12:]

    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def generate_encryption_key() -> str:
    """Generate a new 256-bit encryption key.

    Returns hex-encoded key suitable for ENCRYPTION_KEY env var.
    """
    return secrets.token_hex(32)
