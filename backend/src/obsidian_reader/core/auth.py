"""Authentication middleware and dependencies."""

from fastapi import Cookie, HTTPException, status

from .security import verify_token


async def get_current_user(access_token: str | None = Cookie(default=None)) -> bool:
    """Dependency to verify user is authenticated via cookie."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token_data = verify_token(access_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return token_data.authenticated


class AuthRequired:
    """Dependency class to require authentication."""

    async def __call__(self, access_token: str | None = Cookie(default=None)) -> bool:
        """Check if user is authenticated."""
        return await get_current_user(access_token)

