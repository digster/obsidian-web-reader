"""Git service for cloning and updating vault repositories."""

import logging
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

from git import GitCommandError, InvalidGitRepositoryError, Repo
from git.exc import NoSuchPathError

logger = logging.getLogger(__name__)


class GitServiceError(Exception):
    """Base exception for git service errors."""

    pass


class GitAuthenticationError(GitServiceError):
    """Raised when git authentication fails."""

    pass


class GitRepositoryError(GitServiceError):
    """Raised when there's an issue with the repository."""

    pass


class GitService:
    """Service for managing git operations on vault repositories."""

    @staticmethod
    def _build_authenticated_url(repo_url: str, token: str) -> str:
        """Build an authenticated HTTPS URL for git operations.

        Converts a GitHub URL to use the deploy token for authentication.
        Example: https://github.com/user/repo -> https://oauth2:TOKEN@github.com/user/repo
        """
        parsed = urlparse(repo_url)

        # Ensure it's an HTTPS URL
        if parsed.scheme != "https":
            raise GitServiceError("Only HTTPS repository URLs are supported")

        # Build authenticated URL
        # Format: https://oauth2:TOKEN@github.com/user/repo.git
        auth_url = f"https://oauth2:{token}@{parsed.netloc}{parsed.path}"

        # Ensure URL ends with .git
        if not auth_url.endswith(".git"):
            auth_url += ".git"

        return auth_url

    @staticmethod
    def _sanitize_repo_name(repo_url: str) -> str:
        """Extract a sanitized repository name from URL for use as folder name."""
        parsed = urlparse(repo_url)
        path = parsed.path.strip("/")

        # Remove .git suffix if present
        if path.endswith(".git"):
            path = path[:-4]

        # Get the repo name (last part of path)
        repo_name = path.split("/")[-1] if "/" in path else path

        # Sanitize: only allow alphanumeric, hyphen, underscore
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", repo_name)

        return sanitized.lower()

    @staticmethod
    def validate_repo_url(repo_url: str) -> bool:
        """Validate that the URL looks like a valid GitHub repository URL."""
        try:
            parsed = urlparse(repo_url)
            if parsed.scheme != "https":
                return False
            if not parsed.netloc:
                return False
            # Check path has at least user/repo format
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) < 2:
                return False
            return True
        except Exception:
            return False

    def clone_repository(
        self,
        repo_url: str,
        token: str,
        target_path: Path,
        branch: str | None = None,
    ) -> Path:
        """Clone a repository to the target path.

        Args:
            repo_url: The HTTPS URL of the repository.
            token: GitHub deploy token for authentication.
            target_path: Directory where the repo should be cloned.
            branch: Optional branch to checkout after cloning.

        Returns:
            Path to the cloned repository.

        Raises:
            GitAuthenticationError: If authentication fails.
            GitRepositoryError: If clone fails for other reasons.
        """
        if target_path.exists():
            raise GitRepositoryError(f"Target path already exists: {target_path}")

        # Create parent directory if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)

        auth_url = self._build_authenticated_url(repo_url, token)

        try:
            logger.info(f"Cloning repository to {target_path}")

            clone_kwargs = {"depth": 1}  # Shallow clone for efficiency
            if branch:
                clone_kwargs["branch"] = branch

            Repo.clone_from(auth_url, target_path, **clone_kwargs)

            logger.info(f"Successfully cloned repository to {target_path}")
            return target_path

        except GitCommandError as e:
            # Clean up partial clone
            if target_path.exists():
                shutil.rmtree(target_path)

            error_msg = str(e).lower()
            if "authentication" in error_msg or "403" in error_msg or "401" in error_msg:
                raise GitAuthenticationError(
                    "Authentication failed. Please check your deploy token."
                ) from e
            elif "not found" in error_msg or "404" in error_msg:
                raise GitRepositoryError(
                    "Repository not found. Please check the URL."
                ) from e
            else:
                raise GitRepositoryError(f"Failed to clone repository: {e}") from e
        except Exception as e:
            # Clean up partial clone
            if target_path.exists():
                shutil.rmtree(target_path)
            raise GitRepositoryError(f"Unexpected error cloning repository: {e}") from e

    def pull_repository(self, repo_path: Path, token: str | None = None) -> bool:
        """Pull latest changes from the remote repository.

        Args:
            repo_path: Path to the local repository.
            token: Optional token to update remote URL for auth.

        Returns:
            True if pull was successful (or no changes), False otherwise.

        Raises:
            GitRepositoryError: If the path is not a valid git repository.
            GitAuthenticationError: If authentication fails.
        """
        try:
            repo = Repo(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            raise GitRepositoryError(f"Invalid git repository: {repo_path}") from e

        try:
            origin = repo.remotes.origin

            # If token is provided, update the remote URL with authentication
            if token:
                current_url = origin.url
                # Extract the base URL (without any existing auth)
                if "@" in current_url:
                    # Remove existing auth
                    parsed = urlparse(current_url)
                    base_url = f"https://{parsed.hostname}{parsed.path}"
                else:
                    base_url = current_url

                auth_url = self._build_authenticated_url(base_url, token)
                origin.set_url(auth_url)

            logger.info(f"Pulling latest changes for {repo_path}")
            origin.pull()
            logger.info(f"Successfully pulled changes for {repo_path}")
            return True

        except GitCommandError as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "403" in error_msg or "401" in error_msg:
                raise GitAuthenticationError(
                    "Authentication failed during pull. Token may have expired."
                ) from e
            else:
                logger.error(f"Git pull failed for {repo_path}: {e}")
                raise GitRepositoryError(f"Failed to pull repository: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during pull for {repo_path}: {e}")
            raise GitRepositoryError(f"Unexpected error during pull: {e}") from e

    def is_git_repository(self, path: Path) -> bool:
        """Check if a path is a valid git repository."""
        try:
            Repo(path)
            return True
        except (InvalidGitRepositoryError, NoSuchPathError):
            return False

    def get_remote_url(self, repo_path: Path) -> str | None:
        """Get the remote origin URL of a repository."""
        try:
            repo = Repo(repo_path)
            if repo.remotes:
                url = repo.remotes.origin.url
                # Remove any embedded credentials from URL
                if "@" in url:
                    parsed = urlparse(url)
                    return f"https://{parsed.hostname}{parsed.path}"
                return url
            return None
        except Exception:
            return None

    def delete_repository(self, repo_path: Path) -> bool:
        """Delete a repository directory.

        Args:
            repo_path: Path to the repository to delete.

        Returns:
            True if deletion was successful.
        """
        try:
            if repo_path.exists():
                shutil.rmtree(repo_path)
                logger.info(f"Deleted repository at {repo_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete repository at {repo_path}: {e}")
            return False


# Global git service instance
git_service = GitService()

