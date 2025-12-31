"""Tests for markdown parsing."""

import pytest

from obsidian_reader.services.markdown import render_markdown, MarkdownService


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

