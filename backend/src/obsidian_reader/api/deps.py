"""API dependencies for dependency injection."""

from typing import Annotated

from fastapi import Depends

from ..core.auth import AuthRequired

# Authenticated user dependency
RequireAuth = Annotated[bool, Depends(AuthRequired())]

