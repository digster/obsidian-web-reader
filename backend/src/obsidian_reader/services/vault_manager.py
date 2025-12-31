"""Multi-vault manager for handling multiple Obsidian vaults."""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from ..core.config import settings
from ..models.schemas import FileTreeItem, NoteResponse, VaultInfo
from .vault import VaultService

logger = logging.getLogger(__name__)


class VaultConfig(BaseModel):
    """Configuration for a single vault."""

    path: str
    name: str


class VaultsConfiguration(BaseModel):
    """Root configuration for all vaults."""

    vaults: dict[str, VaultConfig]
    default_vault: str | None = None


class VaultManager:
    """Manages multiple Obsidian vaults and provides a unified interface."""

    def __init__(self):
        self._initialized = False
        self._vaults: dict[str, VaultService] = {}
        self._config: VaultsConfiguration | None = None
        self._default_vault: str | None = None
        # Active vault per session (in a real app, this would be per-user session)
        self._session_vaults: dict[str, str] = {}  # session_id -> vault_id

    async def initialize(self) -> None:
        """Initialize the vault manager by loading configuration."""
        if self._initialized:
            return

        config_path = settings.vaults_config

        if not config_path.exists():
            logger.warning(f"Vault configuration not found at {config_path}")
            # Create default config
            self._config = VaultsConfiguration(vaults={}, default_vault=None)
            self._initialized = True
            return

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = json.load(f)

            self._config = VaultsConfiguration(**config_data)
            self._default_vault = self._config.default_vault

            # Initialize vault services
            for vault_id, vault_config in self._config.vaults.items():
                vault_path = Path(vault_config.path)
                vault_service = VaultService(
                    vault_id=vault_id,
                    vault_path=vault_path,
                    vault_name=vault_config.name,
                )

                if vault_service.validate():
                    self._vaults[vault_id] = vault_service
                    logger.info(f"Loaded vault: {vault_config.name} ({vault_id})")
                else:
                    logger.warning(
                        f"Vault path does not exist or is not accessible: {vault_path}"
                    )

            self._initialized = True
            logger.info(f"Vault manager initialized with {len(self._vaults)} vaults")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in vault configuration: {e}")
            self._config = VaultsConfiguration(vaults={}, default_vault=None)
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to load vault configuration: {e}")
            self._config = VaultsConfiguration(vaults={}, default_vault=None)
            self._initialized = True

    def list_vaults(self) -> list[VaultInfo]:
        """Get list of all available vaults."""
        vaults: list[VaultInfo] = []

        for vault_id, vault_service in self._vaults.items():
            vaults.append(
                VaultInfo(
                    id=vault_id,
                    name=vault_service.vault_name,
                    path=str(vault_service.vault_path),
                    note_count=vault_service.get_note_count(),
                )
            )

        return vaults

    def get_default_vault(self) -> str | None:
        """Get the default vault ID."""
        if self._default_vault and self._default_vault in self._vaults:
            return self._default_vault

        # Fall back to first vault
        if self._vaults:
            return next(iter(self._vaults.keys()))

        return None

    def get_active_vault_id(self, session_id: str) -> str | None:
        """Get the active vault ID for a session."""
        if session_id in self._session_vaults:
            vault_id = self._session_vaults[session_id]
            if vault_id in self._vaults:
                return vault_id

        # Fall back to default
        return self.get_default_vault()

    def set_active_vault(self, session_id: str, vault_id: str) -> bool:
        """Set the active vault for a session."""
        if vault_id not in self._vaults:
            return False

        self._session_vaults[session_id] = vault_id
        return True

    def get_vault(self, vault_id: str) -> VaultService | None:
        """Get a specific vault service by ID."""
        return self._vaults.get(vault_id)

    def get_active_vault(self, session_id: str) -> VaultService | None:
        """Get the active vault service for a session."""
        vault_id = self.get_active_vault_id(session_id)
        if vault_id:
            return self._vaults.get(vault_id)
        return None

    def get_file_tree(self, session_id: str) -> list[FileTreeItem]:
        """Get file tree for the active vault."""
        vault = self.get_active_vault(session_id)
        if vault:
            return vault.build_file_tree()
        return []

    def get_note(self, session_id: str, note_path: str) -> NoteResponse | None:
        """Get a note from the active vault."""
        vault = self.get_active_vault(session_id)
        if vault:
            return vault.get_note(note_path)
        return None

    def get_attachment_path(self, session_id: str, attachment_path: str) -> Path | None:
        """Get attachment path from the active vault."""
        vault = self.get_active_vault(session_id)
        if vault:
            return vault.get_attachment_path(attachment_path)
        return None

    def search(self, session_id: str, query: str) -> list[tuple[str, str, str]]:
        """Search in the active vault (basic search, FTS handled separately)."""
        vault = self.get_active_vault(session_id)
        if vault:
            return vault.search_content(query)
        return []


# Global vault manager instance
vault_manager = VaultManager()
