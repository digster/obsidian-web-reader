"""Tests for vault service."""

from pathlib import Path

import pytest

from obsidian_reader.services.vault import VaultService


class TestVaultService:
    """Test suite for VaultService."""

    def test_validate_existing_vault(self, temp_vault: Path):
        """Test validating an existing vault."""
        service = VaultService("test", temp_vault, "Test Vault")
        assert service.validate() is True

    def test_validate_nonexistent_vault(self, tmp_path: Path):
        """Test validating a non-existent vault."""
        service = VaultService("test", tmp_path / "nonexistent", "Test")
        assert service.validate() is False

    def test_get_note_count(self, temp_vault: Path):
        """Test counting notes in vault."""
        service = VaultService("test", temp_vault, "Test Vault")
        count = service.get_note_count()
        assert count == 3  # test_note, Another Note, nested_note

    def test_build_file_tree(self, temp_vault: Path):
        """Test building file tree."""
        service = VaultService("test", temp_vault, "Test Vault")
        tree = service.build_file_tree()

        # Should have root-level items
        assert len(tree) > 0

        # Find files and folders
        file_names = [item.name for item in tree if item.type == "file"]
        folder_names = [item.name for item in tree if item.type == "folder"]

        assert "test_note" in file_names
        assert "Another Note" in file_names
        assert "subfolder" in folder_names

    def test_get_note(self, temp_vault: Path):
        """Test getting a specific note."""
        service = VaultService("test", temp_vault, "Test Vault")
        note = service.get_note("test_note")

        assert note is not None
        assert note.title == "Test Note"
        assert "test" in note.tags
        assert "example" in note.tags
        assert "inline-tag" in note.tags

    def test_get_note_with_md_extension(self, temp_vault: Path):
        """Test getting a note with .md extension in path."""
        service = VaultService("test", temp_vault, "Test Vault")
        note = service.get_note("test_note.md")

        assert note is not None
        assert note.title == "Test Note"

    def test_get_nonexistent_note(self, temp_vault: Path):
        """Test getting a non-existent note."""
        service = VaultService("test", temp_vault, "Test Vault")
        note = service.get_note("nonexistent")

        assert note is None

    def test_get_nested_note(self, temp_vault: Path):
        """Test getting a note in a subfolder."""
        service = VaultService("test", temp_vault, "Test Vault")
        note = service.get_note("subfolder/nested_note")

        assert note is not None
        assert "Nested Note" in note.content_html

    def test_backlinks(self, temp_vault: Path):
        """Test finding backlinks to a note."""
        service = VaultService("test", temp_vault, "Test Vault")
        note = service.get_note("test_note")

        assert note is not None
        # "Another Note" links back to test_note
        backlink_paths = [b.path for b in note.backlinks]
        assert "Another Note" in backlink_paths

    def test_get_attachment_path(self, temp_vault: Path):
        """Test getting attachment path."""
        service = VaultService("test", temp_vault, "Test Vault")
        path = service.get_attachment_path("attachments/test.png")

        assert path is not None
        assert path.exists()

    def test_get_nonexistent_attachment(self, temp_vault: Path):
        """Test getting non-existent attachment."""
        service = VaultService("test", temp_vault, "Test Vault")
        path = service.get_attachment_path("nonexistent.png")

        assert path is None

    def test_path_traversal_prevention(self, temp_vault: Path):
        """Test that path traversal is prevented."""
        service = VaultService("test", temp_vault, "Test Vault")

        # Attempt path traversal
        note = service.get_note("../../../etc/passwd")
        assert note is None

        attachment = service.get_attachment_path("../../../etc/passwd")
        assert attachment is None

    def test_search_content(self, temp_vault: Path):
        """Test basic content search."""
        service = VaultService("test", temp_vault, "Test Vault")
        results = service.search_content("callout")

        assert len(results) == 1
        assert results[0][0] == "test_note"  # path

