"""Security utilities for JWT token handling and encryption."""

import base64
import hashlib
import logging
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


def _get_encryption_key() -> bytes:
    """Derive a Fernet-compatible encryption key from the secret key.

    Fernet requires a 32-byte base64-encoded key. We derive it from
    the application's secret key using SHA-256.
    """
    # Use SHA-256 to get a consistent 32-byte key from the secret
    key_bytes = hashlib.sha256(settings.secret_key.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_token(token: str) -> str:
    """Encrypt a token (e.g., GitHub deploy token) using Fernet.

    Args:
        token: The plaintext token to encrypt.

    Returns:
        The encrypted token as a base64 string.
    """
    if not token:
        return ""
    fernet = Fernet(_get_encryption_key())
    encrypted = fernet.encrypt(token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str | None:
    """Decrypt a previously encrypted token.

    Args:
        encrypted_token: The encrypted token string.

    Returns:
        The decrypted plaintext token, or None if decryption fails.
    """
    if not encrypted_token:
        return None
    try:
        fernet = Fernet(_get_encryption_key())
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except InvalidToken:
        logger.warning("Failed to decrypt token - invalid or corrupted")
        return None
    except Exception as e:
        logger.error(f"Token decryption error: {e}")
        return None


class TokenData(BaseModel):
    """Data stored in JWT token."""

    authenticated: bool = True
    exp: datetime | None = None


def create_access_token(expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {"authenticated": True, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData | None:
    """Verify a JWT token and return the token data."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return TokenData(**payload)
    except jwt.PyJWTError:
        return None


def verify_password(password: str) -> bool:
    """Verify if the provided password matches the app password."""
    return password == settings.app_password

