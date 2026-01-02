"""Background scheduler for periodic vault synchronization."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..core.security import decrypt_token
from .git_service import GitAuthenticationError, GitRepositoryError, git_service

if TYPE_CHECKING:
    from .vault_manager import VaultManager

logger = logging.getLogger(__name__)


class VaultScheduler:
    """Manages scheduled sync jobs for vaults with git repositories."""

    def __init__(self):
        self._scheduler = BackgroundScheduler()
        self._vault_manager: "VaultManager | None" = None
        self._started = False

    def set_vault_manager(self, vault_manager: "VaultManager") -> None:
        """Set reference to vault manager for accessing vault configs."""
        self._vault_manager = vault_manager

    def start(self) -> None:
        """Start the background scheduler."""
        if not self._started:
            self._scheduler.start()
            self._started = True
            logger.info("Vault scheduler started")

    def shutdown(self) -> None:
        """Shutdown the scheduler gracefully."""
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False
            logger.info("Vault scheduler stopped")

    def schedule_vault_sync(
        self,
        vault_id: str,
        vault_path: Path,
        encrypted_token: str,
        interval_minutes: int,
    ) -> None:
        """Schedule periodic sync for a vault.

        Args:
            vault_id: Unique identifier for the vault.
            vault_path: Path to the vault directory.
            encrypted_token: Encrypted deploy token for git operations.
            interval_minutes: Sync interval in minutes.
        """
        job_id = f"sync_{vault_id}"

        # Remove existing job if present
        self.remove_vault_sync(vault_id)

        # Add new job
        self._scheduler.add_job(
            func=self._sync_vault,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            args=[vault_id, vault_path, encrypted_token],
            replace_existing=True,
            max_instances=1,  # Prevent overlapping sync jobs
            coalesce=True,  # Combine missed runs
        )

        logger.info(
            f"Scheduled sync for vault '{vault_id}' every {interval_minutes} minutes"
        )

    def remove_vault_sync(self, vault_id: str) -> None:
        """Remove scheduled sync for a vault.

        Args:
            vault_id: The vault ID whose sync job should be removed.
        """
        job_id = f"sync_{vault_id}"
        try:
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)
                logger.info(f"Removed sync schedule for vault '{vault_id}'")
        except Exception as e:
            logger.warning(f"Error removing sync job for vault '{vault_id}': {e}")

    def trigger_sync_now(self, vault_id: str, vault_path: Path, encrypted_token: str) -> dict:
        """Trigger an immediate sync for a vault.

        Args:
            vault_id: The vault identifier.
            vault_path: Path to the vault directory.
            encrypted_token: Encrypted deploy token.

        Returns:
            Dict with sync result: {"success": bool, "message": str}
        """
        return self._sync_vault(vault_id, vault_path, encrypted_token)

    def _sync_vault(
        self, vault_id: str, vault_path: Path, encrypted_token: str
    ) -> dict:
        """Internal method to perform vault sync.

        Args:
            vault_id: The vault identifier.
            vault_path: Path to the vault directory.
            encrypted_token: Encrypted deploy token.

        Returns:
            Dict with sync result.
        """
        logger.info(f"Starting sync for vault '{vault_id}'")

        # Decrypt the token
        token = decrypt_token(encrypted_token)
        if not token:
            error_msg = f"Failed to decrypt token for vault '{vault_id}'"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

        # Check if path is a git repository
        if not git_service.is_git_repository(vault_path):
            error_msg = f"Vault '{vault_id}' at {vault_path} is not a git repository"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

        try:
            git_service.pull_repository(vault_path, token)
            success_msg = f"Successfully synced vault '{vault_id}'"
            logger.info(success_msg)
            return {"success": True, "message": success_msg}

        except GitAuthenticationError as e:
            error_msg = f"Authentication failed for vault '{vault_id}': {e}"
            logger.error(error_msg)
            return {"success": False, "message": str(e)}

        except GitRepositoryError as e:
            error_msg = f"Repository error for vault '{vault_id}': {e}"
            logger.error(error_msg)
            return {"success": False, "message": str(e)}

        except Exception as e:
            error_msg = f"Unexpected error syncing vault '{vault_id}': {e}"
            logger.error(error_msg)
            return {"success": False, "message": str(e)}

    def get_scheduled_jobs(self) -> list[dict]:
        """Get list of all scheduled sync jobs.

        Returns:
            List of job info dicts with vault_id, next_run_time, etc.
        """
        jobs = []
        for job in self._scheduler.get_jobs():
            if job.id.startswith("sync_"):
                vault_id = job.id.replace("sync_", "")
                jobs.append({
                    "vault_id": vault_id,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                })
        return jobs

    def reschedule_all_vaults(self) -> None:
        """Reschedule sync jobs for all vaults that have refresh intervals.

        This should be called after vault manager initialization to set up
        sync jobs for existing vaults.
        """
        if not self._vault_manager:
            logger.warning("Vault manager not set, cannot reschedule vaults")
            return

        config = self._vault_manager.get_config()
        if not config:
            return

        for vault_id, vault_config in config.vaults.items():
            if vault_config.refresh_interval_minutes and vault_config.encrypted_token:
                vault_path = Path(vault_config.path)
                if vault_path.exists():
                    self.schedule_vault_sync(
                        vault_id=vault_id,
                        vault_path=vault_path,
                        encrypted_token=vault_config.encrypted_token,
                        interval_minutes=vault_config.refresh_interval_minutes,
                    )


# Global scheduler instance
vault_scheduler = VaultScheduler()

