"""Multi-vault manager for handling multiple Obsidian vaults."""

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from ..core.config import settings
from ..core.security import decrypt_token, encrypt_token
from ..models.schemas import FileTreeItem, NoteResponse, VaultInfo
from .git_service import GitAuthenticationError, GitRepositoryError, GitService, git_service
from .vault import VaultService

logger = logging.getLogger(__name__)


class VaultConfig(BaseModel):
    """Configuration for a single vault."""

    path: str
    name: str
    repo_url: str | None = None
    encrypted_token: str | None = None
    refresh_interval_minutes: int | None = None


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
        self._git_service: GitService = git_service

    async def initialize(self) -> None:
        """Initialize the vault manager by loading configuration."""
        if self._initialized:
            return

        config_path = settings.vaults_config

        if not config_path.exists() or config_path.is_dir():
            if config_path.is_dir():
                logger.warning(
                    f"Vault configuration path is a directory: {config_path}. "
                    "This can happen if the Docker volume mount target doesn't exist on the host."
                )
            else:
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

            # Schedule sync jobs for vaults with refresh intervals
            self._schedule_vault_syncs()

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in vault configuration: {e}")
            self._config = VaultsConfiguration(vaults={}, default_vault=None)
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to load vault configuration: {e}")
            self._config = VaultsConfiguration(vaults={}, default_vault=None)
            self._initialized = True

    def _schedule_vault_syncs(self) -> None:
        """Schedule sync jobs for vaults with refresh intervals."""
        # Import here to avoid circular imports
        from .scheduler import vault_scheduler

        vault_scheduler.set_vault_manager(self)
        vault_scheduler.start()
        vault_scheduler.reschedule_all_vaults()

    def get_config(self) -> VaultsConfiguration | None:
        """Get the current vault configuration."""
        return self._config

    def _save_config(self) -> None:
        """Save the current configuration to the config file."""
        if not self._config:
            return

        config_path = settings.vaults_config

        try:
            # Handle case where config path is a directory (Docker mount issue)
            if config_path.is_dir():
                logger.warning(
                    f"Config path {config_path} is a directory, removing it to create file"
                )
                config_path.rmdir()

            # Create parent directory if needed
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self._config.model_dump(), f, indent=2)

            logger.info(f"Saved vault configuration to {config_path}")

        except Exception as e:
            logger.error(f"Failed to save vault configuration: {e}")
            raise

    def _generate_vault_id(self, name: str) -> str:
        """Generate a unique vault ID from the name."""
        # Sanitize: lowercase, replace spaces with hyphens, remove special chars
        vault_id = re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))

        # Ensure uniqueness
        base_id = vault_id
        counter = 1
        while vault_id in self._vaults or (self._config and vault_id in self._config.vaults):
            vault_id = f"{base_id}-{counter}"
            counter += 1

        return vault_id

    async def add_vault(
        self,
        name: str,
        repo_url: str,
        token: str,
        refresh_interval_minutes: int | None = None,
    ) -> VaultInfo:
        """Add a new vault by cloning from a git repository.

        Args:
            name: Display name for the vault.
            repo_url: GitHub repository URL (HTTPS).
            token: GitHub deploy token for authentication.
            refresh_interval_minutes: Optional interval for automatic sync.

        Returns:
            VaultInfo for the newly created vault.

        Raises:
            GitAuthenticationError: If authentication fails.
            GitRepositoryError: If clone fails.
            ValueError: If vault with same name exists.
        """
        if not self._config:
            self._config = VaultsConfiguration(vaults={}, default_vault=None)

        # Generate unique vault ID
        vault_id = self._generate_vault_id(name)

        # Determine target path
        vaults_dir = settings.vaults_dir
        vaults_dir.mkdir(parents=True, exist_ok=True)

        # Use sanitized repo name for folder
        repo_name = self._git_service._sanitize_repo_name(repo_url)
        target_path = vaults_dir / repo_name

        # Ensure path is unique
        base_path = target_path
        counter = 1
        while target_path.exists():
            target_path = Path(f"{base_path}-{counter}")
            counter += 1

        # Clone the repository
        logger.info(f"Creating vault '{name}' from {repo_url}")
        self._git_service.clone_repository(repo_url, token, target_path)

        # Encrypt the token for storage
        encrypted_token = encrypt_token(token)

        # Create vault config
        vault_config = VaultConfig(
            path=str(target_path),
            name=name,
            repo_url=repo_url,
            encrypted_token=encrypted_token,
            refresh_interval_minutes=refresh_interval_minutes,
        )

        # Add to configuration
        self._config.vaults[vault_id] = vault_config

        # Set as default if it's the first vault
        if self._config.default_vault is None:
            self._config.default_vault = vault_id
            self._default_vault = vault_id

        # Save configuration
        self._save_config()

        # Create and register vault service
        vault_service = VaultService(
            vault_id=vault_id,
            vault_path=target_path,
            vault_name=name,
        )
        self._vaults[vault_id] = vault_service

        # Schedule sync if interval is set
        if refresh_interval_minutes and refresh_interval_minutes > 0:
            from .scheduler import vault_scheduler

            vault_scheduler.schedule_vault_sync(
                vault_id=vault_id,
                vault_path=target_path,
                encrypted_token=encrypted_token,
                interval_minutes=refresh_interval_minutes,
            )

        logger.info(f"Successfully created vault '{name}' ({vault_id})")

        return VaultInfo(
            id=vault_id,
            name=name,
            path=str(target_path),
            note_count=vault_service.get_note_count(),
        )

    async def delete_vault(self, vault_id: str, delete_files: bool = True) -> bool:
        """Delete a vault.

        Args:
            vault_id: ID of the vault to delete.
            delete_files: If True, also delete the vault files from disk.

        Returns:
            True if deletion was successful.

        Raises:
            ValueError: If vault doesn't exist.
        """
        if not self._config or vault_id not in self._config.vaults:
            raise ValueError(f"Vault '{vault_id}' not found")

        vault_config = self._config.vaults[vault_id]
        vault_path = Path(vault_config.path)

        # Remove from scheduler
        from .scheduler import vault_scheduler

        vault_scheduler.remove_vault_sync(vault_id)

        # Remove from active vaults
        if vault_id in self._vaults:
            del self._vaults[vault_id]

        # Remove from session mappings
        sessions_to_clear = [
            sid for sid, vid in self._session_vaults.items() if vid == vault_id
        ]
        for sid in sessions_to_clear:
            del self._session_vaults[sid]

        # Delete files if requested
        if delete_files and vault_path.exists():
            try:
                shutil.rmtree(vault_path)
                logger.info(f"Deleted vault files at {vault_path}")
            except Exception as e:
                logger.error(f"Failed to delete vault files: {e}")

        # Remove from configuration
        del self._config.vaults[vault_id]

        # Update default vault if needed
        if self._config.default_vault == vault_id:
            if self._config.vaults:
                self._config.default_vault = next(iter(self._config.vaults.keys()))
                self._default_vault = self._config.default_vault
            else:
                self._config.default_vault = None
                self._default_vault = None

        # Save configuration
        self._save_config()

        logger.info(f"Deleted vault '{vault_id}'")
        return True

    async def sync_vault(self, vault_id: str) -> dict:
        """Manually trigger sync for a vault.

        Args:
            vault_id: ID of the vault to sync.

        Returns:
            Dict with sync result: {"success": bool, "message": str}
        """
        if not self._config or vault_id not in self._config.vaults:
            return {"success": False, "message": f"Vault '{vault_id}' not found"}

        vault_config = self._config.vaults[vault_id]

        if not vault_config.encrypted_token:
            return {"success": False, "message": "Vault has no stored credentials"}

        if not vault_config.repo_url:
            return {"success": False, "message": "Vault is not linked to a repository"}

        from .scheduler import vault_scheduler

        return vault_scheduler.trigger_sync_now(
            vault_id=vault_id,
            vault_path=Path(vault_config.path),
            encrypted_token=vault_config.encrypted_token,
        )

    def list_vaults(self) -> list[VaultInfo]:
        """Get list of all available vaults."""
        vaults: list[VaultInfo] = []

        for vault_id, vault_service in self._vaults.items():
            # Get additional info from config if available
            has_sync = False
            if self._config and vault_id in self._config.vaults:
                cfg = self._config.vaults[vault_id]
                has_sync = bool(cfg.repo_url and cfg.encrypted_token)

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

    def get_vault_sync_info(self, vault_id: str) -> dict | None:
        """Get sync information for a vault.

        Returns dict with repo_url, has_token, refresh_interval, or None if vault not found.
        """
        if not self._config or vault_id not in self._config.vaults:
            return None

        cfg = self._config.vaults[vault_id]
        return {
            "repo_url": cfg.repo_url,
            "has_token": bool(cfg.encrypted_token),
            "refresh_interval_minutes": cfg.refresh_interval_minutes,
        }


# Global vault manager instance
vault_manager = VaultManager()
