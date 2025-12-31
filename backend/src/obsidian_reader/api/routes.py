"""API routes for the Obsidian Web Reader."""

import logging
import secrets
from datetime import timedelta
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse

from ..core.config import settings
from ..core.security import create_access_token, verify_password, verify_token
from ..models.schemas import (
    AuthStatus,
    FileTreeResponse,
    LoginRequest,
    MessageResponse,
    NoteResponse,
    SearchResponse,
    TokenResponse,
    VaultListResponse,
    VaultSelectRequest,
)
from ..services.markdown import render_markdown
from ..services.search import search_service
from ..services.vault_manager import vault_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Authentication helpers
# ============================================================================


def get_session_id(access_token: str | None = Cookie(default=None)) -> str:
    """Get or generate a session ID from the access token."""
    if access_token:
        token_data = verify_token(access_token)
        if token_data:
            # Use token as session identifier
            return access_token[:32]
    return secrets.token_hex(16)


def require_auth(access_token: str | None = Cookie(default=None)) -> str:
    """Dependency that requires authentication and returns session ID."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token_data = verify_token(access_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return access_token[:32]  # Return session ID


# Type alias for authenticated endpoints
AuthSession = Annotated[str, Depends(require_auth)]


# ============================================================================
# Auth Routes
# ============================================================================


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, response: Response) -> TokenResponse:
    """Login with password and receive access token."""
    if not verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    # Create access token
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(expires_delta=expires)

    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.is_development,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    return TokenResponse(access_token=access_token)


@router.post("/auth/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    """Logout and clear the access token cookie."""
    response.delete_cookie(key="access_token")
    return MessageResponse(message="Logged out successfully")


@router.get("/auth/me", response_model=AuthStatus)
async def get_auth_status(
    access_token: str | None = Cookie(default=None),
) -> AuthStatus:
    """Check current authentication status."""
    if not access_token:
        return AuthStatus(authenticated=False)

    token_data = verify_token(access_token)
    if not token_data:
        return AuthStatus(authenticated=False)

    session_id = access_token[:32]
    active_vault = vault_manager.get_active_vault_id(session_id)

    return AuthStatus(authenticated=True, active_vault=active_vault)


# ============================================================================
# Vault Routes
# ============================================================================


@router.get("/vaults", response_model=VaultListResponse)
async def list_vaults(session_id: AuthSession) -> VaultListResponse:
    """List all available vaults."""
    vaults = vault_manager.list_vaults()
    active_vault = vault_manager.get_active_vault_id(session_id)
    default_vault = vault_manager.get_default_vault()

    return VaultListResponse(
        vaults=vaults,
        active_vault=active_vault,
        default_vault=default_vault,
    )


@router.post("/vaults/select", response_model=MessageResponse)
async def select_vault(
    request: VaultSelectRequest,
    session_id: AuthSession,
) -> MessageResponse:
    """Set the active vault for the current session."""
    success = vault_manager.set_active_vault(session_id, request.vault_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault '{request.vault_id}' not found",
        )

    # Build search index for the vault if not already done
    vault = vault_manager.get_vault(request.vault_id)
    if vault:
        try:
            search_service.build_index(request.vault_id, vault.vault_path)
        except Exception as e:
            logger.warning(f"Failed to build search index: {e}")

    return MessageResponse(message=f"Switched to vault: {request.vault_id}")


@router.get("/vault/tree", response_model=FileTreeResponse)
async def get_file_tree(session_id: AuthSession) -> FileTreeResponse:
    """Get the file tree for the active vault."""
    vault_id = vault_manager.get_active_vault_id(session_id)

    if not vault_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active vault selected",
        )

    tree = vault_manager.get_file_tree(session_id)

    return FileTreeResponse(vault_id=vault_id, tree=tree)


@router.get("/vault/note/{note_path:path}", response_model=NoteResponse)
async def get_note(note_path: str, session_id: AuthSession) -> NoteResponse:
    """Get a note by path with rendered HTML content."""
    note = vault_manager.get_note(session_id, note_path)

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note not found: {note_path}",
        )

    # Render markdown to HTML
    note.content_html = render_markdown(note.content_html)

    return note


@router.get("/vault/attachment/{attachment_path:path}")
async def get_attachment(attachment_path: str, session_id: AuthSession) -> FileResponse:
    """Serve an attachment file from the vault."""
    file_path = vault_manager.get_attachment_path(session_id, attachment_path)

    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment not found: {attachment_path}",
        )

    # Determine media type
    suffix = file_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".pdf": "application/pdf",
        ".mp3": "audio/mpeg",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name,
    )


# ============================================================================
# Search Routes
# ============================================================================


@router.get("/search", response_model=SearchResponse)
async def search_notes(q: str, session_id: AuthSession) -> SearchResponse:
    """Search notes in the active vault."""
    if not q.strip():
        return SearchResponse(query=q, results=[], total=0)

    vault = vault_manager.get_active_vault(session_id)

    if not vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active vault selected",
        )

    results = search_service.search(vault.vault_id, vault.vault_path, q)

    return SearchResponse(query=q, results=results, total=len(results))


@router.post("/search/reindex", response_model=MessageResponse)
async def reindex_search(session_id: AuthSession) -> MessageResponse:
    """Rebuild the search index for the active vault."""
    vault = vault_manager.get_active_vault(session_id)

    if not vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active vault selected",
        )

    try:
        count = search_service.build_index(vault.vault_id, vault.vault_path)
        return MessageResponse(message=f"Indexed {count} notes")
    except Exception as e:
        logger.error(f"Failed to reindex: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rebuild search index",
        )


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
    }
