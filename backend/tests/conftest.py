"""Pytest fixtures for testing."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


# Set test environment before importing anything
os.environ["APP_PASSWORD"] = "test_password"
os.environ["ENV"] = "development"


@pytest.fixture
def temp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault directory with test files."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    # Create some test markdown files
    (vault_path / "test_note.md").write_text(
        """---
title: Test Note
tags:
  - test
  - example
aliases:
  - Test
---

# Test Note

This is a test note with [[Another Note|a link]] and a #inline-tag.

> [!note] Important
> This is a callout.

Some math: $E = mc^2$

```python
print("Hello, World!")
```
"""
    )

    (vault_path / "Another Note.md").write_text(
        """---
title: Another Note
---

# Another Note

This note links back to [[test_note]].
"""
    )

    # Create a subfolder with notes
    subfolder = vault_path / "subfolder"
    subfolder.mkdir()

    (subfolder / "nested_note.md").write_text(
        """# Nested Note

This is a note in a subfolder.
"""
    )

    # Create an attachments folder
    attachments = vault_path / "attachments"
    attachments.mkdir()

    # Create a test image (just a small valid PNG)
    (attachments / "test.png").write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
        b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    return vault_path


@pytest.fixture
def vault_config(temp_vault: Path, tmp_path: Path) -> Path:
    """Create a vault configuration file."""
    config = {
        "vaults": {
            "test": {
                "path": str(temp_vault),
                "name": "Test Vault"
            }
        },
        "default_vault": "test"
    }

    config_path = tmp_path / "vaults.json"
    config_path.write_text(json.dumps(config))

    return config_path


@pytest.fixture
def test_client(vault_config: Path, tmp_path: Path, temp_vault: Path):
    """Create a test client with configured vaults."""
    from fastapi.testclient import TestClient

    # Set environment variables BEFORE importing anything
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)

    os.environ["VAULTS_CONFIG"] = str(vault_config)
    os.environ["DATA_DIR"] = str(data_dir)

    # Now import and reload settings
    from obsidian_reader.core.config import Settings

    # Create fresh settings
    import obsidian_reader.core.config as config_module
    config_module.settings = Settings()

    # Reset vault manager
    from obsidian_reader.services.vault_manager import VaultManager
    import obsidian_reader.services.vault_manager as vm_module
    vm_module.vault_manager = VaultManager()

    # Reset search service
    from obsidian_reader.services.search import SearchService
    import obsidian_reader.services.search as search_module
    search_module.search_service = SearchService()

    # Initialize vault manager synchronously
    async def init():
        await vm_module.vault_manager.initialize()

    asyncio.run(init())

    # Import app AFTER initialization
    from obsidian_reader.main import app

    with TestClient(app) as client:
        yield client

    # Cleanup
    search_module.search_service.close_all()


@pytest.fixture
def authenticated_client(test_client):
    """Create an authenticated test client."""
    # Login to get token
    response = test_client.post(
        "/api/auth/login",
        json={"password": "test_password"}
    )
    assert response.status_code == 200

    return test_client
