from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

settings = get_settings()


def _get_cipher() -> Fernet | None:
    if settings.encryption_key.startswith("replace-with"):
        return None
    return Fernet(settings.encryption_key.encode())


def encrypt_value(value: str | None) -> str | None:
    if not value:
        return None
    cipher = _get_cipher()
    if cipher is None:
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
        return None
