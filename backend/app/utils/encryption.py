"""Credential encryption utilities using Fernet (AES-128-CBC + HMAC)"""
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings


def _get_fernet() -> Fernet:
    """Return a Fernet instance using the app encryption key"""
    key = settings.credential_encryption_key.encode()
    return Fernet(key)


def encrypt_credential(plain_value: str) -> str:
    """Encrypt a credential value. Returns a URL-safe base64 string."""
    f = _get_fernet()
    return f.encrypt(plain_value.encode()).decode()


def decrypt_credential(encrypted_value: str) -> str:
    """Decrypt a credential value. Raises ValueError if tampered or wrong key."""
    f = _get_fernet()
    try:
        return f.decrypt(encrypted_value.encode()).decode()
    except InvalidToken:
        raise ValueError("Credential decryption failed: invalid token or wrong key")
