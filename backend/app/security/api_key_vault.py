import os

from cryptography.fernet import Fernet

from app.config import settings

_DEV_FERNET_KEY = Fernet.generate_key()


def _fernet() -> Fernet:
    key = settings.NIM_API_KEY_ENCRYPTION_KEY
    if not key:
        return Fernet(_DEV_FERNET_KEY)
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_key(raw: str) -> str:
    return _fernet().encrypt(raw.encode()).decode()


def decrypt_key(encrypted: str) -> str:
    return _fernet().decrypt(encrypted.encode()).decode()


def get_nim_api_key() -> str:
    encrypted = os.getenv("NIM_API_KEY_ENCRYPTED")
    if encrypted:
        return decrypt_key(encrypted)
    raw = os.getenv("NIM_API_KEY", "")
    if not raw:
        raise OSError("NIM_API_KEY or NIM_API_KEY_ENCRYPTED must be set")
    return raw
