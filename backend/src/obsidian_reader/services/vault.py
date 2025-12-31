"""Vault service for reading and processing a single Obsidian vault."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter

from ..models.schemas import BacklinkInfo, FileTreeItem, NoteResponse


class VaultService:
    """Service for reading and processing a single Obsidian vault."""

    def __init__(self, vault_id: str, vault_path: Path, vault_name: str):
        self.vault_id = vault_id
        self.vault_path = vault_path
        self.vault_name = vault_name
        self._note_cache: dict[str, dict[str, Any]] = {}
        self._backlinks: dict[str, list[BacklinkInfo]] = {}

    def validate(self) -> bool:
        """Check if the vault path exists and is accessible."""
        return self.vault_path.exists() and self.vault_path.is_dir()

    def get_note_count(self) -> int:
        """Count the number of markdown files in the vault."""
        if not self.validate():
            return 0
        return sum(1 for _ in self.vault_path.rglob("*.md"))

    def build_file_tree(self) -> list[FileTreeItem]:
        """Build a hierarchical file tree of the vault."""
        if not self.validate():
            return []

        def build_tree(path: Path, relative_base: Path) -> list[FileTreeItem]:
            items: list[FileTreeItem] = []

            # Get sorted entries (folders first, then files)
            try:
                entries = sorted(
                    path.iterdir(),
                    key=lambda x: (not x.is_dir(), x.name.lower()),
                )
            except PermissionError:
                return items

            for entry in entries:
                # Skip hidden files and directories
                if entry.name.startswith("."):
                    continue

                relative_path = str(entry.relative_to(relative_base))

                if entry.is_dir():
                    # Recursively build tree for directories
                    children = build_tree(entry, relative_base)
                    # Only include non-empty directories
                    if children:
                        items.append(
                            FileTreeItem(
                                name=entry.name,
                                path=relative_path,
                                type="folder",
                                children=children,
                            )
                        )
                elif entry.suffix.lower() == ".md":
                    # Include markdown files
                    items.append(
                        FileTreeItem(
                            name=entry.stem,  # Remove .md extension for display
                            path=relative_path,
                            type="file",
                            children=None,
                        )
                    )

            return items

        return build_tree(self.vault_path, self.vault_path)

    def get_note(self, note_path: str) -> NoteResponse | None:
        """Get a note by its path relative to the vault root."""
        # Normalize path and ensure it ends with .md
        if not note_path.endswith(".md"):
            note_path = f"{note_path}.md"

        full_path = self.vault_path / note_path

        # Security check: ensure path is within vault
        try:
            full_path = full_path.resolve()
            self.vault_path.resolve()
            if not str(full_path).startswith(str(self.vault_path.resolve())):
                return None
        except (OSError, ValueError):
            return None

        if not full_path.exists() or not full_path.is_file():
            return None

        try:
            # Parse the note with frontmatter
            post = frontmatter.load(full_path)

            # Extract metadata
            fm_data = dict(post.metadata) if post.metadata else {}
            title = fm_data.get("title") or fm_data.get("aliases", [None])[0] or full_path.stem
            tags = self._extract_tags(post.content, fm_data)

            # Get file modification time
            stat = full_path.stat()
            modified_at = datetime.fromtimestamp(stat.st_mtime)

            # Get backlinks for this note
            backlinks = self._get_backlinks(note_path)

            # Content will be rendered by the markdown service
            return NoteResponse(
                path=note_path.replace(".md", ""),
                title=str(title),
                content_html=post.content,  # Raw markdown, will be rendered later
                frontmatter=fm_data,
                tags=tags,
                backlinks=backlinks,
                modified_at=modified_at,
            )

        except Exception:
            return None

    def _extract_tags(self, content: str, frontmatter_data: dict[str, Any]) -> list[str]:
        """Extract tags from both frontmatter and content."""
        tags: set[str] = set()

        # Tags from frontmatter
        fm_tags = frontmatter_data.get("tags", [])
        if isinstance(fm_tags, list):
            tags.update(str(t) for t in fm_tags)
        elif isinstance(fm_tags, str):
            tags.add(fm_tags)

        # Tags from content (inline #tags)
        import re

        tag_pattern = r"(?:^|\s)#([a-zA-Z0-9_/-]+)"
        for match in re.finditer(tag_pattern, content):
            tags.add(match.group(1))

        return sorted(tags)

    def _get_backlinks(self, note_path: str) -> list[BacklinkInfo]:
        """Get all notes that link to this note."""
        # Normalize the target path
        target = note_path.replace(".md", "")
        target_name = Path(target).name

        backlinks: list[BacklinkInfo] = []

        # Search all markdown files for links to this note
        for md_file in self.vault_path.rglob("*.md"):
            if str(md_file.relative_to(self.vault_path)).replace(".md", "") == target:
                continue  # Skip self

            try:
                content = md_file.read_text(encoding="utf-8")

                # Check for wiki links to this note
                import re

                # Match [[note]] or [[note|alias]] or [[note#heading]]
                link_pattern = r"\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]"
                for match in re.finditer(link_pattern, content):
                    link_target = match.group(1).strip()
                    # Check if this link points to our target
                    if link_target == target_name or link_target == target:
                        # Get title from the linking note
                        try:
                            post = frontmatter.load(md_file)
                            link_title = (
                                post.metadata.get("title")
                                or post.metadata.get("aliases", [None])[0]
                                or md_file.stem
                            )
                        except Exception:
                            link_title = md_file.stem

                        rel_path = str(md_file.relative_to(self.vault_path)).replace(".md", "")
                        backlinks.append(BacklinkInfo(path=rel_path, title=str(link_title)))
                        break  # Only add each file once

            except Exception:
                continue

        return backlinks

    def get_attachment_path(self, attachment_path: str) -> Path | None:
        """Get the full path to an attachment file."""
        full_path = self.vault_path / attachment_path

        # Security check
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(self.vault_path.resolve())):
                return None
        except (OSError, ValueError):
            return None

        if full_path.exists() and full_path.is_file():
            return full_path
        return None

    def search_content(self, query: str) -> list[tuple[str, str, str]]:
        """Simple content search (used as fallback when FTS is not available).

        Returns list of (path, title, snippet) tuples.
        """
        results: list[tuple[str, str, str]] = []
        query_lower = query.lower()

        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                content_lower = content.lower()

                if query_lower in content_lower:
                    # Get title
                    try:
                        post = frontmatter.load(md_file)
                        title = (
                            post.metadata.get("title")
                            or post.metadata.get("aliases", [None])[0]
                            or md_file.stem
                        )
                    except Exception:
                        title = md_file.stem

                    # Create snippet around first match
                    idx = content_lower.find(query_lower)
                    start = max(0, idx - 50)
                    end = min(len(content), idx + len(query) + 50)
                    snippet = content[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(content):
                        snippet = snippet + "..."

                    rel_path = str(md_file.relative_to(self.vault_path)).replace(".md", "")
                    results.append((rel_path, str(title), snippet))

            except Exception:
                continue

        return results

