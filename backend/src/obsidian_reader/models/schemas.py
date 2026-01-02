"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# Auth schemas
class LoginRequest(BaseModel):
    """Login request body."""

    password: str


class TokenResponse(BaseModel):
    """Token response after successful login."""

    access_token: str
    token_type: str = "bearer"


class AuthStatus(BaseModel):
    """Authentication status response."""

    authenticated: bool
    active_vault: str | None = None


# Vault schemas
class VaultInfo(BaseModel):
    """Information about a vault."""

    id: str
    name: str
    path: str
    note_count: int = 0


class VaultListResponse(BaseModel):
    """Response containing list of vaults."""

    vaults: list[VaultInfo]
    active_vault: str | None = None
    default_vault: str | None = None


class VaultSelectRequest(BaseModel):
    """Request to select active vault."""

    vault_id: str


class VaultCreateRequest(BaseModel):
    """Request to create a new vault from a git repository."""

    name: str = Field(..., min_length=1, max_length=100, description="Display name for the vault")
    repo_url: str = Field(..., description="GitHub repository URL (HTTPS)")
    token: str = Field(..., min_length=1, description="GitHub deploy token for authentication")
    refresh_interval_minutes: int | None = Field(
        default=None,
        ge=1,
        le=1440,
        description="Optional sync interval in minutes (1-1440)"
    )


class VaultDeleteRequest(BaseModel):
    """Request to delete a vault."""

    delete_files: bool = Field(
        default=True,
        description="Whether to also delete vault files from disk"
    )


class VaultSyncResponse(BaseModel):
    """Response from a vault sync operation."""

    success: bool
    message: str
    vault_id: str


# File tree schemas
class FileTreeItem(BaseModel):
    """A single item in the file tree."""

    name: str
    path: str
    type: Literal["file", "folder"]
    children: list["FileTreeItem"] | None = None


class FileTreeResponse(BaseModel):
    """File tree response for a vault."""

    vault_id: str
    tree: list[FileTreeItem]


# Note schemas
class BacklinkInfo(BaseModel):
    """Information about a backlink."""

    path: str
    title: str


class NoteResponse(BaseModel):
    """Response containing a rendered note."""

    path: str
    title: str
    content_html: str
    frontmatter: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    backlinks: list[BacklinkInfo] = Field(default_factory=list)
    modified_at: datetime | None = None


# Search schemas
class SearchResult(BaseModel):
    """A single search result."""

    path: str
    title: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    """Search results response."""

    query: str
    results: list[SearchResult]
    total: int


# General response schemas
class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
    success: bool = True

