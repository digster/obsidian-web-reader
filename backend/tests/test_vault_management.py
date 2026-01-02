"""Tests for vault management functionality."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Set test environment before importing anything
os.environ["APP_PASSWORD"] = "test_password"
os.environ["ENV"] = "development"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_purposes_only"


class TestTokenEncryption:
    """Tests for token encryption/decryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        from obsidian_reader.core.security import decrypt_token, encrypt_token

        original_token = "ghp_1234567890abcdef"
        encrypted = encrypt_token(original_token)

        # Encrypted token should be different from original
        assert encrypted != original_token
        assert len(encrypted) > 0

        # Decryption should return original
        decrypted = decrypt_token(encrypted)
        assert decrypted == original_token

    def test_encrypt_empty_token(self):
        """Test encrypting an empty token."""
        from obsidian_reader.core.security import encrypt_token

        result = encrypt_token("")
        assert result == ""

    def test_decrypt_empty_token(self):
        """Test decrypting an empty token."""
        from obsidian_reader.core.security import decrypt_token

        result = decrypt_token("")
        assert result is None

    def test_decrypt_invalid_token(self):
        """Test decrypting an invalid token returns None."""
        from obsidian_reader.core.security import decrypt_token

        result = decrypt_token("invalid_encrypted_data")
        assert result is None


class TestGitService:
    """Tests for git service functionality."""

    def test_validate_repo_url_valid(self):
        """Test valid repository URLs."""
        from obsidian_reader.services.git_service import GitService

        service = GitService()

        # Valid URLs
        assert service.validate_repo_url("https://github.com/user/repo") is True
        assert service.validate_repo_url("https://github.com/user/repo.git") is True
        assert service.validate_repo_url("https://gitlab.com/user/repo") is True

    def test_validate_repo_url_invalid(self):
        """Test invalid repository URLs."""
        from obsidian_reader.services.git_service import GitService

        service = GitService()

        # Invalid URLs
        assert service.validate_repo_url("http://github.com/user/repo") is False  # Not HTTPS
        assert service.validate_repo_url("git@github.com:user/repo.git") is False  # SSH
        assert service.validate_repo_url("https://github.com/user") is False  # No repo name
        assert service.validate_repo_url("not-a-url") is False

    def test_sanitize_repo_name(self):
        """Test repository name sanitization."""
        from obsidian_reader.services.git_service import GitService

        service = GitService()

        assert service._sanitize_repo_name("https://github.com/user/my-repo") == "my-repo"
        assert service._sanitize_repo_name("https://github.com/user/my-repo.git") == "my-repo"
        assert service._sanitize_repo_name("https://github.com/user/My_Repo") == "my_repo"
        # Special chars are replaced with hyphens, then lowercased
        result = service._sanitize_repo_name("https://github.com/user/repo!@#")
        assert result.startswith("repo")

    def test_build_authenticated_url(self):
        """Test building authenticated URL."""
        from obsidian_reader.services.git_service import GitService

        service = GitService()

        url = service._build_authenticated_url(
            "https://github.com/user/repo",
            "test_token"
        )

        assert "oauth2:test_token@" in url
        assert url.startswith("https://")
        assert url.endswith(".git")


class TestVaultManagerConfig:
    """Tests for VaultManager configuration."""

    def test_vault_config_model(self):
        """Test VaultConfig model with all fields."""
        from obsidian_reader.services.vault_manager import VaultConfig

        config = VaultConfig(
            path="/path/to/vault",
            name="My Vault",
            repo_url="https://github.com/user/repo",
            encrypted_token="encrypted123",
            refresh_interval_minutes=60,
        )

        assert config.path == "/path/to/vault"
        assert config.name == "My Vault"
        assert config.repo_url == "https://github.com/user/repo"
        assert config.encrypted_token == "encrypted123"
        assert config.refresh_interval_minutes == 60

    def test_vault_config_model_minimal(self):
        """Test VaultConfig model with minimal fields."""
        from obsidian_reader.services.vault_manager import VaultConfig

        config = VaultConfig(
            path="/path/to/vault",
            name="My Vault",
        )

        assert config.path == "/path/to/vault"
        assert config.name == "My Vault"
        assert config.repo_url is None
        assert config.encrypted_token is None
        assert config.refresh_interval_minutes is None


class TestVaultManagerOperations:
    """Tests for VaultManager vault operations."""

    @pytest.fixture
    def vault_manager_setup(self, tmp_path):
        """Set up a vault manager with a temp config."""
        # Create config file
        config_path = tmp_path / "vaults.json"
        config_data = {
            "vaults": {},
            "default_vault": None
        }
        config_path.write_text(json.dumps(config_data))

        # Create vaults directory
        vaults_dir = tmp_path / "vaults"
        vaults_dir.mkdir()

        # Patch settings
        with patch("obsidian_reader.services.vault_manager.settings") as mock_settings:
            mock_settings.vaults_config = config_path
            mock_settings.vaults_dir = vaults_dir

            from obsidian_reader.services.vault_manager import VaultManager

            manager = VaultManager()
            yield manager, tmp_path

    def test_generate_vault_id(self, vault_manager_setup):
        """Test vault ID generation."""
        manager, _ = vault_manager_setup
        manager._config = MagicMock()
        manager._config.vaults = {}

        vault_id = manager._generate_vault_id("My Test Vault")
        assert vault_id == "my-test-vault"

        # Leading/trailing spaces become hyphens, multiple spaces become multiple hyphens
        vault_id = manager._generate_vault_id("Spaces Around")
        assert "spaces" in vault_id and "around" in vault_id

    def test_generate_vault_id_uniqueness(self, vault_manager_setup):
        """Test that vault IDs are unique."""
        manager, _ = vault_manager_setup
        manager._config = MagicMock()
        manager._config.vaults = {"my-vault": MagicMock()}

        vault_id = manager._generate_vault_id("My Vault")
        assert vault_id == "my-vault-1"


class TestScheduler:
    """Tests for vault scheduler."""

    def test_scheduler_start_stop(self):
        """Test scheduler start and stop."""
        from obsidian_reader.services.scheduler import VaultScheduler

        scheduler = VaultScheduler()
        assert scheduler._started is False

        scheduler.start()
        assert scheduler._started is True

        scheduler.shutdown()
        assert scheduler._started is False

    def test_scheduler_schedule_job(self):
        """Test scheduling a sync job."""
        from obsidian_reader.services.scheduler import VaultScheduler

        scheduler = VaultScheduler()
        scheduler.start()

        try:
            scheduler.schedule_vault_sync(
                vault_id="test-vault",
                vault_path=Path("/tmp/test"),
                encrypted_token="encrypted123",
                interval_minutes=60,
            )

            jobs = scheduler.get_scheduled_jobs()
            assert len(jobs) == 1
            assert jobs[0]["vault_id"] == "test-vault"

        finally:
            scheduler.shutdown()

    def test_scheduler_remove_job(self):
        """Test removing a sync job."""
        from obsidian_reader.services.scheduler import VaultScheduler

        scheduler = VaultScheduler()
        scheduler.start()

        try:
            scheduler.schedule_vault_sync(
                vault_id="test-vault",
                vault_path=Path("/tmp/test"),
                encrypted_token="encrypted123",
                interval_minutes=60,
            )

            scheduler.remove_vault_sync("test-vault")

            jobs = scheduler.get_scheduled_jobs()
            assert len(jobs) == 0

        finally:
            scheduler.shutdown()


class TestVaultAPISchemas:
    """Tests for vault API schemas."""

    def test_vault_create_request_schema(self):
        """Test VaultCreateRequest schema validation."""
        from obsidian_reader.models.schemas import VaultCreateRequest

        # Valid request with all fields
        request = VaultCreateRequest(
            name="My Vault",
            repo_url="https://github.com/user/repo",
            token="ghp_1234567890",
            refresh_interval_minutes=60,
        )
        assert request.name == "My Vault"
        assert request.refresh_interval_minutes == 60

        # Valid request without optional field
        request = VaultCreateRequest(
            name="My Vault",
            repo_url="https://github.com/user/repo",
            token="ghp_1234567890",
        )
        assert request.refresh_interval_minutes is None

    def test_vault_create_request_validation(self):
        """Test VaultCreateRequest validation."""
        from pydantic import ValidationError

        from obsidian_reader.models.schemas import VaultCreateRequest

        # Name too short
        with pytest.raises(ValidationError):
            VaultCreateRequest(
                name="",
                repo_url="https://github.com/user/repo",
                token="ghp_1234567890",
            )

        # Refresh interval out of range
        with pytest.raises(ValidationError):
            VaultCreateRequest(
                name="My Vault",
                repo_url="https://github.com/user/repo",
                token="ghp_1234567890",
                refresh_interval_minutes=0,
            )

        with pytest.raises(ValidationError):
            VaultCreateRequest(
                name="My Vault",
                repo_url="https://github.com/user/repo",
                token="ghp_1234567890",
                refresh_interval_minutes=1441,
            )

    def test_vault_sync_response_schema(self):
        """Test VaultSyncResponse schema."""
        from obsidian_reader.models.schemas import VaultSyncResponse

        response = VaultSyncResponse(
            vault_id="test-vault",
            success=True,
            message="Sync successful",
        )
        assert response.vault_id == "test-vault"
        assert response.success is True
        assert response.message == "Sync successful"

