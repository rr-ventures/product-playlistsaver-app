import logging

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

logger = logging.getLogger("playlist_saver.encryption")
settings = get_settings()

_PLACEHOLDER_PREFIX = "replace-with"


def _get_cipher() -> Fernet | None:
    if settings.encryption_key.startswith(_PLACEHOLDER_PREFIX):
        return None
    return Fernet(settings.encryption_key.encode())


def encrypt_value(value: str | None) -> str | None:
    if not value:
        return None
    cipher = _get_cipher()
    if cipher is None:
        logger.warning("Encryption key not configured — storing value in plaintext")
        return value
    return cipher.encrypt(value.encode()).decode()


def decrypt_value(value: str | None) -> str | None:
    if not value:
        return None
    cipher = _get_cipher()
    if cipher is None:
        return value
    try:
        return cipher.decrypt(value.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt value — token is invalid or key has changed")
        return None
