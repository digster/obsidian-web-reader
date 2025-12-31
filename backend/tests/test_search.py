"""Tests for search functionality."""

import tempfile
from pathlib import Path

import pytest

from obsidian_reader.services.search import SearchIndex, SearchService


class TestSearchIndex:
    """Test suite for SearchIndex."""

    def test_initialize(self, temp_vault: Path, tmp_path: Path):
        """Test index initialization."""
        index = SearchIndex("test", temp_vault)
        index.db_path = tmp_path / "test.db"
        index.initialize()

        assert index.db_path.exists()

    def test_build_index(self, temp_vault: Path, tmp_path: Path):
        """Test building search index."""
        index = SearchIndex("test", temp_vault)
        index.db_path = tmp_path / "test.db"
        index.initialize()

        count = index.build_index()
        assert count == 3  # 3 markdown files in temp_vault

    def test_search_basic(self, temp_vault: Path, tmp_path: Path):
        """Test basic search."""
        index = SearchIndex("test", temp_vault)
        index.db_path = tmp_path / "test.db"
        index.initialize()
        index.build_index()

        results = index.search("callout")
        assert len(results) >= 1
        assert any(r.path == "test_note" for r in results)

    def test_search_by_title(self, temp_vault: Path, tmp_path: Path):
        """Test searching by title."""
        index = SearchIndex("test", temp_vault)
        index.db_path = tmp_path / "test.db"
        index.initialize()
        index.build_index()

        results = index.search("Test Note")
        assert len(results) >= 1

    def test_search_by_tag(self, temp_vault: Path, tmp_path: Path):
        """Test searching by tag."""
        index = SearchIndex("test", temp_vault)
        index.db_path = tmp_path / "test.db"
        index.initialize()
        index.build_index()

        results = index.search("tag:test")
        assert len(results) >= 1

    def test_search_no_results(self, temp_vault: Path, tmp_path: Path):
        """Test search with no results."""
        index = SearchIndex("test", temp_vault)
        index.db_path = tmp_path / "test.db"
        index.initialize()
        index.build_index()

        results = index.search("xyznonexistent123")
        assert len(results) == 0

    def test_search_snippet(self, temp_vault: Path, tmp_path: Path):
        """Test that search returns snippets."""
        index = SearchIndex("test", temp_vault)
        index.db_path = tmp_path / "test.db"
        index.initialize()
        index.build_index()

        results = index.search("important")
        assert len(results) >= 1
        assert results[0].snippet  # Should have a snippet

    def test_close(self, temp_vault: Path, tmp_path: Path):
        """Test closing the index."""
        index = SearchIndex("test", temp_vault)
        index.db_path = tmp_path / "test.db"
        index.initialize()

        index.close()
        assert index._connection is None


class TestSearchService:
    """Test suite for SearchService."""

    def test_get_or_create_index(self, temp_vault: Path, tmp_path: Path):
        """Test getting or creating an index."""
        import os
        os.environ["DATA_DIR"] = str(tmp_path)

        service = SearchService()
        index = service.get_or_create_index("test", temp_vault)

        assert index is not None
        assert "test" in service._indexes

    def test_build_index(self, temp_vault: Path, tmp_path: Path):
        """Test building index through service."""
        import os
        os.environ["DATA_DIR"] = str(tmp_path)

        service = SearchService()
        count = service.build_index("test", temp_vault)

        assert count == 3

    def test_search(self, temp_vault: Path, tmp_path: Path):
        """Test searching through service."""
        import os
        os.environ["DATA_DIR"] = str(tmp_path)

        service = SearchService()
        service.build_index("test", temp_vault)

        results = service.search("test", temp_vault, "callout")
        assert len(results) >= 1

    def test_close_all(self, temp_vault: Path, tmp_path: Path):
        """Test closing all indexes."""
        import os
        os.environ["DATA_DIR"] = str(tmp_path)

        service = SearchService()
        service.get_or_create_index("test", temp_vault)

        service.close_all()
        assert len(service._indexes) == 0

