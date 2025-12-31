"""Search service using SQLite FTS5 for full-text search."""

import logging
import re
import sqlite3
from pathlib import Path
from typing import Any

import frontmatter

from ..core.config import settings
from ..models.schemas import SearchResult

logger = logging.getLogger(__name__)


class SearchIndex:
    """SQLite FTS5 search index for a single vault."""

    def __init__(self, vault_id: str, vault_path: Path):
        self.vault_id = vault_id
        self.vault_path = vault_path
        self.db_path = settings.data_dir / f"{vault_id}.db"
        self._connection: sqlite3.Connection | None = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            settings.data_dir.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def initialize(self) -> None:
        """Create the FTS5 virtual table if it doesn't exist."""
        conn = self._get_connection()

        # Create the FTS5 table for full-text search
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                path,
                title,
                content,
                tags,
                aliases,
                tokenize='porter unicode61'
            )
        """)

        # Create a metadata table to track indexing
        conn.execute("""
            CREATE TABLE IF NOT EXISTS index_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        logger.info(f"Search index initialized for vault: {self.vault_id}")

    def build_index(self) -> int:
        """Build or rebuild the search index from vault files."""
        conn = self._get_connection()

        # Clear existing data
        conn.execute("DELETE FROM notes_fts")

        indexed_count = 0

        for md_file in self.vault_path.rglob("*.md"):
            # Skip hidden files
            if any(part.startswith(".") for part in md_file.parts):
                continue

            try:
                # Parse the file
                post = frontmatter.load(md_file)
                content = post.content

                # Extract metadata
                fm = post.metadata or {}
                title = fm.get("title") or md_file.stem

                # Handle aliases
                aliases = fm.get("aliases", [])
                if isinstance(aliases, str):
                    aliases = [aliases]
                aliases_str = " ".join(str(a) for a in aliases)

                # Extract tags from frontmatter and content
                tags: set[str] = set()

                fm_tags = fm.get("tags", [])
                if isinstance(fm_tags, list):
                    tags.update(str(t) for t in fm_tags)
                elif isinstance(fm_tags, str):
                    tags.add(fm_tags)

                # Extract inline tags
                tag_pattern = r"(?:^|\s)#([a-zA-Z0-9_/-]+)"
                for match in re.finditer(tag_pattern, content):
                    tags.add(match.group(1))

                tags_str = " ".join(tags)

                # Get relative path
                rel_path = str(md_file.relative_to(self.vault_path)).replace(".md", "")

                # Insert into FTS table
                conn.execute(
                    """
                    INSERT INTO notes_fts (path, title, content, tags, aliases)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (rel_path, str(title), content, tags_str, aliases_str),
                )

                indexed_count += 1

            except Exception as e:
                logger.warning(f"Failed to index {md_file}: {e}")
                continue

        conn.commit()
        logger.info(f"Indexed {indexed_count} notes for vault: {self.vault_id}")

        return indexed_count

    def search(self, query: str, limit: int = 50) -> list[SearchResult]:
        """Search for notes matching the query."""
        conn = self._get_connection()

        results: list[SearchResult] = []

        # Handle special search operators
        search_query = query

        # Tag search: tag:name -> search in tags column
        if query.startswith("tag:"):
            tag_name = query[4:]
            search_query = f'tags:"{tag_name}"'
        else:
            # Regular search - escape special characters and add wildcards
            # FTS5 query syntax
            words = query.split()
            search_terms = []
            for word in words:
                # Escape special characters
                word = word.replace('"', '""')
                # Add prefix matching with *
                search_terms.append(f'"{word}"*')
            search_query = " OR ".join(search_terms)

        try:
            # Use FTS5 BM25 ranking
            cursor = conn.execute(
                """
                SELECT
                    path,
                    title,
                    snippet(notes_fts, 2, '<mark>', '</mark>', '...', 50) as snippet,
                    bm25(notes_fts) as score
                FROM notes_fts
                WHERE notes_fts MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (search_query, limit),
            )

            for row in cursor:
                results.append(
                    SearchResult(
                        path=row["path"],
                        title=row["title"],
                        snippet=row["snippet"],
                        score=abs(row["score"]),  # BM25 returns negative scores
                    )
                )

        except sqlite3.OperationalError as e:
            # If FTS query fails, try simple LIKE search
            logger.warning(f"FTS search failed, falling back to LIKE: {e}")
            results = self._simple_search(query, limit)

        return results

    def _simple_search(self, query: str, limit: int) -> list[SearchResult]:
        """Fallback simple search using LIKE."""
        conn = self._get_connection()
        results: list[SearchResult] = []

        like_query = f"%{query}%"

        cursor = conn.execute(
            """
            SELECT path, title, substr(content, 1, 200) as snippet
            FROM notes_fts
            WHERE content LIKE ? OR title LIKE ? OR tags LIKE ?
            LIMIT ?
            """,
            (like_query, like_query, like_query, limit),
        )

        for row in cursor:
            results.append(
                SearchResult(
                    path=row["path"],
                    title=row["title"],
                    snippet=row["snippet"] + "...",
                    score=1.0,
                )
            )

        return results

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            try:
                self._connection.close()
            except sqlite3.ProgrammingError:
                # Ignore threading errors on close
                pass
            self._connection = None


class SearchService:
    """Service for managing search indexes across multiple vaults."""

    def __init__(self):
        self._indexes: dict[str, SearchIndex] = {}

    def get_or_create_index(self, vault_id: str, vault_path: Path) -> SearchIndex:
        """Get or create a search index for a vault."""
        if vault_id not in self._indexes:
            index = SearchIndex(vault_id, vault_path)
            index.initialize()
            self._indexes[vault_id] = index
        return self._indexes[vault_id]

    def build_index(self, vault_id: str, vault_path: Path) -> int:
        """Build or rebuild the search index for a vault."""
        index = self.get_or_create_index(vault_id, vault_path)
        return index.build_index()

    def search(self, vault_id: str, vault_path: Path, query: str) -> list[SearchResult]:
        """Search in a specific vault."""
        index = self.get_or_create_index(vault_id, vault_path)
        return index.search(query)

    def close_all(self) -> None:
        """Close all search index connections."""
        for index in self._indexes.values():
            index.close()
        self._indexes.clear()


# Global search service instance
search_service = SearchService()

