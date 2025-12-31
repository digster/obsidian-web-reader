"""Tests for markdown parsing and caching."""

from datetime import datetime, timedelta

import pytest

from obsidian_reader.services.markdown import (
    CacheStats,
    MarkdownCache,
    MarkdownService,
    clear_cache,
    get_cache_stats,
    render_markdown,
    render_markdown_cached,
)


class TestMarkdownRendering:
    """Test suite for markdown rendering."""

    def test_basic_markdown(self):
        """Test basic markdown rendering."""
        content = "# Heading\n\nParagraph with **bold** and *italic*."
        html = render_markdown(content)

        assert "<h1" in html
        assert "Heading" in html
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_wiki_links(self):
        """Test wiki link rendering."""
        content = "Link to [[Another Note]]."
        html = render_markdown(content)

        assert 'href="/note/Another Note"' in html
        assert 'class="internal-link"' in html
        assert "Another Note" in html

    def test_wiki_links_with_alias(self):
        """Test wiki links with display text alias."""
        content = "Link to [[Another Note|Display Text]]."
        html = render_markdown(content)

        assert 'href="/note/Another Note"' in html
        assert "Display Text" in html

    def test_wiki_links_with_heading(self):
        """Test wiki links with heading reference."""
        content = "Link to [[Note#Section]]."
        html = render_markdown(content)

        assert 'href="/note/Note#section"' in html

    def test_image_embeds(self):
        """Test image embed rendering."""
        content = "![[image.png]]"
        html = render_markdown(content)

        assert "<img" in html
        assert 'src="/api/vault/attachment/image.png"' in html
        assert 'class="embedded-image' in html

    def test_note_embeds(self):
        """Test note embed rendering."""
        content = "![[embedded_note]]"
        html = render_markdown(content)

        assert 'class="embedded-note' in html
        assert 'data-embed-target="embedded_note"' in html

    def test_tags(self):
        """Test inline tag rendering."""
        content = "This has a #test-tag inline."
        html = render_markdown(content)

        assert 'href="/search?q=tag:test-tag"' in html
        assert 'class="tag"' in html
        assert "#test-tag" in html

    def test_nested_tags(self):
        """Test nested tag rendering."""
        content = "Nested #parent/child tag."
        html = render_markdown(content)

        assert "tag:parent/child" in html

    def test_callout_note(self):
        """Test note callout rendering."""
        content = """> [!note] Title
> Content here."""
        html = render_markdown(content)

        assert 'class="callout callout-note"' in html
        assert "Title" in html
        assert "Content here" in html

    def test_callout_warning(self):
        """Test warning callout rendering."""
        content = """> [!warning]
> Be careful!"""
        html = render_markdown(content)

        assert "callout-warning" in html

    def test_callout_tip(self):
        """Test tip callout rendering."""
        content = """> [!tip] Pro Tip
> This is helpful."""
        html = render_markdown(content)

        assert "callout-tip" in html

    def test_inline_math(self):
        """Test inline math rendering."""
        content = "The equation $E = mc^2$ is famous."
        html = render_markdown(content)

        assert 'class="math-inline"' in html
        assert 'data-math="E = mc^2"' in html

    def test_block_math(self):
        """Test block math rendering."""
        content = """$$
\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}
$$"""
        html = render_markdown(content)

        assert 'class="math-block"' in html

    def test_code_block(self):
        """Test fenced code block rendering."""
        content = """```python
def hello():
    print("Hello!")
```"""
        html = render_markdown(content)

        assert 'class="code-block"' in html

    def test_task_list(self):
        """Test task list rendering."""
        content = """- [ ] Unchecked
- [x] Checked"""
        html = render_markdown(content)

        assert 'type="checkbox"' in html
        assert "checked" in html
        assert "disabled" in html

    def test_tables(self):
        """Test table rendering."""
        content = """| Header 1 | Header 2 |
| --- | --- |
| Cell 1 | Cell 2 |"""
        html = render_markdown(content)

        assert "<table>" in html
        assert "<th>" in html
        assert "<td>" in html

    def test_footnotes(self):
        """Test footnote rendering."""
        content = """Text with footnote[^1].

[^1]: Footnote content."""
        html = render_markdown(content)

        assert "footnote" in html.lower()

    def test_external_links(self):
        """Test external links remain unchanged."""
        content = "Visit [Google](https://google.com)."
        html = render_markdown(content)

        assert 'href="https://google.com"' in html

    def test_multiple_features(self):
        """Test multiple features in one document."""
        content = """# Mixed Content

This has [[wiki links]], #tags, and $math$.

> [!note] Callout
> With content.

```python
code()
```
"""
        html = render_markdown(content)

        assert "internal-link" in html
        assert "tag" in html
        assert "math-inline" in html
        assert "callout" in html
        assert "code-block" in html


class TestMarkdownCache:
    """Test suite for markdown cache functionality."""

    def test_cache_basic_operation(self):
        """Test basic cache get/set operations."""
        cache = MarkdownCache(max_size=100)
        vault_id = "test_vault"
        note_path = "test/note.md"
        modified_at = datetime.now()
        html_content = "<h1>Test</h1>"

        # Initially cache should be empty
        assert cache.get(vault_id, note_path, modified_at) is None

        # Set content in cache
        cache.set(vault_id, note_path, modified_at, html_content)

        # Should retrieve from cache
        cached = cache.get(vault_id, note_path, modified_at)
        assert cached == html_content

    def test_cache_invalidation_on_mtime_change(self):
        """Test that cache is invalidated when modification time changes."""
        cache = MarkdownCache(max_size=100)
        vault_id = "test_vault"
        note_path = "test/note.md"
        old_mtime = datetime.now()
        new_mtime = old_mtime + timedelta(seconds=1)
        html_content = "<h1>Test</h1>"

        # Cache with old mtime
        cache.set(vault_id, note_path, old_mtime, html_content)
        assert cache.get(vault_id, note_path, old_mtime) == html_content

        # New mtime should miss cache
        assert cache.get(vault_id, note_path, new_mtime) is None

    def test_cache_different_vaults(self):
        """Test that different vaults have separate cache entries."""
        cache = MarkdownCache(max_size=100)
        note_path = "same/note.md"
        modified_at = datetime.now()

        # Cache for vault A
        cache.set("vault_a", note_path, modified_at, "<h1>Vault A</h1>")
        # Cache for vault B
        cache.set("vault_b", note_path, modified_at, "<h1>Vault B</h1>")

        assert cache.get("vault_a", note_path, modified_at) == "<h1>Vault A</h1>"
        assert cache.get("vault_b", note_path, modified_at) == "<h1>Vault B</h1>"

    def test_cache_stats(self):
        """Test cache statistics tracking."""
        cache = MarkdownCache(max_size=100)
        vault_id = "test_vault"
        note_path = "test/note.md"
        modified_at = datetime.now()

        # Initial stats
        stats = cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.size == 0

        # Miss
        cache.get(vault_id, note_path, modified_at)
        stats = cache.get_stats()
        assert stats.misses == 1

        # Set and hit
        cache.set(vault_id, note_path, modified_at, "<h1>Test</h1>")
        cache.get(vault_id, note_path, modified_at)
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.size == 1

    def test_cache_hit_rate(self):
        """Test cache hit rate calculation."""
        stats = CacheStats(hits=75, misses=25, size=50, max_size=100)
        assert stats.hit_rate == 75.0

        # Zero requests
        empty_stats = CacheStats(hits=0, misses=0, size=0, max_size=100)
        assert empty_stats.hit_rate == 0.0

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = MarkdownCache(max_size=100)
        vault_id = "test_vault"
        modified_at = datetime.now()

        # Add some entries
        for i in range(5):
            cache.set(vault_id, f"note_{i}.md", modified_at, f"<h1>{i}</h1>")

        assert cache.get_stats().size == 5

        # Clear cache
        cache.clear()

        assert cache.get_stats().size == 0
        assert cache.get_stats().hits == 0
        assert cache.get_stats().misses == 0

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = MarkdownCache(max_size=3)
        vault_id = "test_vault"
        modified_at = datetime.now()

        # Fill cache
        cache.set(vault_id, "note_1.md", modified_at, "<h1>1</h1>")
        cache.set(vault_id, "note_2.md", modified_at, "<h1>2</h1>")
        cache.set(vault_id, "note_3.md", modified_at, "<h1>3</h1>")

        # Access note_1 to make it recently used
        cache.get(vault_id, "note_1.md", modified_at)

        # Add new entry - should evict note_2 (least recently used)
        cache.set(vault_id, "note_4.md", modified_at, "<h1>4</h1>")

        assert cache.get_stats().size == 3
        # note_1 should still be cached (was accessed)
        assert cache.get(vault_id, "note_1.md", modified_at) == "<h1>1</h1>"
        # note_4 should be cached (just added)
        assert cache.get(vault_id, "note_4.md", modified_at) == "<h1>4</h1>"

    def test_cache_none_modified_at(self):
        """Test cache works with None modification time."""
        cache = MarkdownCache(max_size=100)
        vault_id = "test_vault"
        note_path = "test/note.md"

        cache.set(vault_id, note_path, None, "<h1>Test</h1>")
        assert cache.get(vault_id, note_path, None) == "<h1>Test</h1>"


class TestMarkdownServiceCaching:
    """Test suite for MarkdownService caching integration."""

    def test_render_cached_stores_and_retrieves(self):
        """Test that render_cached stores and retrieves from cache."""
        service = MarkdownService(cache_max_size=100)
        content = "# Test Heading"
        vault_id = "test_vault"
        note_path = "test.md"
        modified_at = datetime.now()

        # First call should render and cache
        html1 = service.render_cached(content, vault_id, note_path, modified_at)
        stats1 = service.get_cache_stats()
        assert stats1.misses == 1
        assert stats1.size == 1

        # Second call should hit cache
        html2 = service.render_cached(content, vault_id, note_path, modified_at)
        stats2 = service.get_cache_stats()
        assert stats2.hits == 1
        assert html1 == html2

    def test_render_cached_vs_uncached_consistency(self):
        """Test that cached and uncached rendering produce same output."""
        service = MarkdownService(cache_max_size=100)
        content = """# Test

This has [[wiki links]] and #tags.

> [!note] Callout
> Content here.
"""
        vault_id = "test_vault"
        note_path = "test.md"
        modified_at = datetime.now()

        # Uncached render
        html_uncached = service.render(content)

        # Cached render
        html_cached = service.render_cached(content, vault_id, note_path, modified_at)

        assert html_uncached == html_cached

    def test_service_clear_cache(self):
        """Test MarkdownService cache clearing."""
        service = MarkdownService(cache_max_size=100)
        content = "# Test"
        vault_id = "test_vault"
        modified_at = datetime.now()

        # Add to cache
        service.render_cached(content, vault_id, "test.md", modified_at)
        assert service.get_cache_stats().size == 1

        # Clear
        service.clear_cache()
        assert service.get_cache_stats().size == 0


class TestGlobalCacheFunctions:
    """Test suite for global cache functions."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_render_markdown_cached_global(self):
        """Test global render_markdown_cached function."""
        content = "# Test"
        vault_id = "test_vault"
        note_path = "test.md"
        modified_at = datetime.now()

        html = render_markdown_cached(content, vault_id, note_path, modified_at)
        assert "<h1" in html
        assert "Test" in html

        stats = get_cache_stats()
        assert stats.size == 1

    def test_global_clear_cache(self):
        """Test global clear_cache function."""
        content = "# Test"
        vault_id = "test_vault"
        modified_at = datetime.now()

        render_markdown_cached(content, vault_id, "test.md", modified_at)
        assert get_cache_stats().size == 1

        clear_cache()
        assert get_cache_stats().size == 0

