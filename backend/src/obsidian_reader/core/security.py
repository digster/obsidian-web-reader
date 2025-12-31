"""Security utilities for JWT token handling."""

from datetime import datetime, timedelta, timezone

import jwt
from pydantic import BaseModel

from .config import settings

ALGORITHM = "HS256"


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

