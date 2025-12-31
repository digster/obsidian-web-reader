"""Markdown parser with Obsidian-specific extensions."""

import html
import re
from typing import Any
from xml.etree import ElementTree as ET

import markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor, Pattern
from markdown.preprocessors import Preprocessor
from markdown.postprocessors import Postprocessor
from markdown.blockprocessors import BlockProcessor
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer


# Pattern constants
WIKI_LINK_PATTERN = r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"
EMBED_PATTERN = r"!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"
TAG_PATTERN = r"(?<![#\w])#([a-zA-Z][a-zA-Z0-9_/-]*)"
INLINE_MATH_PATTERN = r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)"
BLOCK_MATH_PATTERN = r"\$\$(.+?)\$\$"
CALLOUT_PATTERN = r"^>\s*\[!(\w+)\]([+-])?(?:\s*(.*))?$"


class WikiLinkInlineProcessor(InlineProcessor):
    """Process Obsidian-style wiki links: [[page]], [[page|alias]], [[page#heading]]."""

    def handleMatch(self, m: re.Match, data: str) -> tuple[ET.Element | None, int, int]:
        target = m.group(1).strip()
        heading = m.group(2).strip() if m.group(2) else None
        alias = m.group(3).strip() if m.group(3) else None

        # Create the link element
        el = ET.Element("a")
        el.set("class", "internal-link")

        # Build href
        href = f"/note/{target}"
        if heading:
            # Convert heading to anchor format
            anchor = heading.lower().replace(" ", "-")
            href += f"#{anchor}"
        el.set("href", href)
        el.set("data-target", target)

        # Set display text
        if alias:
            el.text = alias
        elif heading:
            el.text = f"{target} > {heading}"
        else:
            el.text = target

        return el, m.start(0), m.end(0)


class EmbedInlineProcessor(InlineProcessor):
    """Process Obsidian-style embeds: ![[image.png]], ![[note]], ![[note#heading]]."""

    def handleMatch(self, m: re.Match, data: str) -> tuple[ET.Element | None, int, int]:
        target = m.group(1).strip()
        heading = m.group(2).strip() if m.group(2) else None
        alias = m.group(3).strip() if m.group(3) else None

        # Determine if this is an image or note embed
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}
        is_image = any(target.lower().endswith(ext) for ext in image_extensions)

        if is_image:
            # Image embed
            el = ET.Element("img")
            el.set("src", f"/api/vault/attachment/{target}")
            el.set("alt", alias or target)
            el.set("class", "embedded-image max-w-full h-auto rounded-lg")
            el.set("loading", "lazy")
        else:
            # Note embed - create a placeholder div
            el = ET.Element("div")
            el.set("class", "embedded-note border-l-4 border-accent-400 pl-4 my-4 bg-obsidian-100 dark:bg-obsidian-800 rounded-r-lg p-4")
            el.set("data-embed-target", target)
            if heading:
                el.set("data-embed-heading", heading)

            # Add a link to the embedded note
            inner = ET.SubElement(el, "a")
            inner.set("href", f"/note/{target}")
            inner.set("class", "internal-link font-medium")
            inner.text = f"📄 {alias or target}"
            if heading:
                inner.text += f" > {heading}"

        return el, m.start(0), m.end(0)


class TagInlineProcessor(InlineProcessor):
    """Process Obsidian-style tags: #tag, #nested/tag."""

    def handleMatch(self, m: re.Match, data: str) -> tuple[ET.Element | None, int, int]:
        tag = m.group(1)

        el = ET.Element("a")
        el.set("href", f"/search?q=tag:{tag}")
        el.set("class", "tag")
        el.text = f"#{tag}"

        return el, m.start(0), m.end(0)


class InlineMathInlineProcessor(InlineProcessor):
    """Process inline math: $equation$."""

    def handleMatch(self, m: re.Match, data: str) -> tuple[ET.Element | None, int, int]:
        math_content = m.group(1)

        el = ET.Element("span")
        el.set("class", "math-inline")
        el.set("data-math", html.escape(math_content))
        el.text = f"${math_content}$"

        return el, m.start(0), m.end(0)


class EmbedPreprocessor(Preprocessor):
    """Convert Obsidian embeds to HTML before main markdown processing."""

    EMBED_PATTERN = re.compile(r"!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]")

    def run(self, lines: list[str]) -> list[str]:
        new_lines: list[str] = []

        for line in lines:
            new_line = self.EMBED_PATTERN.sub(self._replace_embed, line)
            new_lines.append(new_line)

        return new_lines

    def _replace_embed(self, m: re.Match) -> str:
        target = m.group(1).strip()
        heading = m.group(2).strip() if m.group(2) else None
        alias = m.group(3).strip() if m.group(3) else None

        # Determine if this is an image or note embed
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}
        is_image = any(target.lower().endswith(ext) for ext in image_extensions)

        if is_image:
            # Image embed
            alt = html.escape(alias or target)
            return f'<img src="/api/vault/attachment/{html.escape(target)}" alt="{alt}" class="embedded-image max-w-full h-auto rounded-lg" loading="lazy">'
        else:
            # Note embed
            display = html.escape(alias or target)
            if heading:
                display += f" > {html.escape(heading)}"
                heading_attr = f' data-embed-heading="{html.escape(heading)}"'
            else:
                heading_attr = ""

            return f'''<div class="embedded-note border-l-4 border-accent-400 pl-4 my-4 bg-obsidian-100 dark:bg-obsidian-800 rounded-r-lg p-4" data-embed-target="{html.escape(target)}"{heading_attr}>
<a href="/note/{html.escape(target)}" class="internal-link font-medium">📄 {display}</a>
</div>'''


class CalloutPreprocessor(Preprocessor):
    """Convert Obsidian callouts to HTML before main markdown processing."""

    CALLOUT_TYPES = {
        "note": ("📝", "callout-note"),
        "abstract": ("📋", "callout-note"),
        "summary": ("📋", "callout-note"),
        "tldr": ("📋", "callout-note"),
        "info": ("ℹ️", "callout-info"),
        "todo": ("☑️", "callout-info"),
        "tip": ("💡", "callout-tip"),
        "hint": ("💡", "callout-tip"),
        "important": ("🔥", "callout-tip"),
        "success": ("✅", "callout-tip"),
        "check": ("✅", "callout-tip"),
        "done": ("✅", "callout-tip"),
        "question": ("❓", "callout-warning"),
        "help": ("❓", "callout-warning"),
        "faq": ("❓", "callout-warning"),
        "warning": ("⚠️", "callout-warning"),
        "caution": ("⚠️", "callout-warning"),
        "attention": ("⚠️", "callout-warning"),
        "failure": ("❌", "callout-danger"),
        "fail": ("❌", "callout-danger"),
        "missing": ("❌", "callout-danger"),
        "danger": ("⛔", "callout-danger"),
        "error": ("🚫", "callout-danger"),
        "bug": ("🐛", "callout-danger"),
        "example": ("📎", "callout-example"),
        "quote": ("💬", "callout-quote"),
        "cite": ("💬", "callout-quote"),
    }

    def run(self, lines: list[str]) -> list[str]:
        new_lines: list[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            match = re.match(CALLOUT_PATTERN, line)

            if match:
                callout_type = match.group(1).lower()
                # collapsed = match.group(2)  # + or - for collapsible (not implemented)
                title = match.group(3) or callout_type.title()

                icon, css_class = self.CALLOUT_TYPES.get(
                    callout_type, ("📌", "callout-note")
                )

                # Collect callout content
                content_lines: list[str] = []
                i += 1
                while i < len(lines) and lines[i].startswith(">"):
                    # Remove the > prefix and add to content
                    content = lines[i][1:].strip()
                    if content.startswith(" "):
                        content = content[1:]
                    content_lines.append(content)
                    i += 1

                # Build callout HTML
                content_html = "\n".join(content_lines)
                callout_html = f"""
<div class="callout {css_class}">
<div class="callout-title">{icon} {html.escape(title)}</div>
<div class="callout-content">

{content_html}

</div>
</div>
"""
                new_lines.extend(callout_html.split("\n"))
            else:
                new_lines.append(line)
                i += 1

        return new_lines


class BlockMathPreprocessor(Preprocessor):
    """Convert block math ($$...$$) to HTML placeholders."""

    def run(self, lines: list[str]) -> list[str]:
        text = "\n".join(lines)

        def replace_block_math(m: re.Match) -> str:
            math_content = m.group(1).strip()
            escaped = html.escape(math_content)
            return f'\n<div class="math-block" data-math="{escaped}">\n$${math_content}$$\n</div>\n'

        text = re.sub(BLOCK_MATH_PATTERN, replace_block_math, text, flags=re.DOTALL)
        return text.split("\n")


class TaskListPostprocessor(Postprocessor):
    """Convert task list items to proper checkboxes."""

    def run(self, text: str) -> str:
        # Convert [ ] to unchecked checkbox
        text = re.sub(
            r"<li>\[ \]",
            '<li class="task-list-item"><input type="checkbox" class="task-checkbox" disabled>',
            text,
        )
        # Convert [x] or [X] to checked checkbox
        text = re.sub(
            r"<li>\[[xX]\]",
            '<li class="task-list-item"><input type="checkbox" class="task-checkbox" disabled checked>',
            text,
        )
        return text


class ObsidianExtension(Extension):
    """Markdown extension for Obsidian-specific syntax."""

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        # Preprocessors (run before main parsing)
        md.preprocessors.register(EmbedPreprocessor(md), "embed", 35)
        md.preprocessors.register(CalloutPreprocessor(md), "callout", 30)
        md.preprocessors.register(BlockMathPreprocessor(md), "block_math", 25)

        # Inline processors
        md.inlinePatterns.register(
            WikiLinkInlineProcessor(WIKI_LINK_PATTERN, md), "wiki_link", 200
        )
        md.inlinePatterns.register(
            TagInlineProcessor(TAG_PATTERN, md), "tag", 198
        )
        md.inlinePatterns.register(
            InlineMathInlineProcessor(INLINE_MATH_PATTERN, md), "inline_math", 197
        )

        # Postprocessors
        md.postprocessors.register(TaskListPostprocessor(md), "task_list", 25)


class CodeBlockFormatter:
    """Format code blocks with syntax highlighting."""

    @staticmethod
    def highlight_code(code: str, language: str | None = None) -> str:
        """Highlight code using Pygments."""
        try:
            if language:
                lexer = get_lexer_by_name(language, stripall=True)
            else:
                lexer = guess_lexer(code)
        except Exception:
            lexer = TextLexer()

        formatter = HtmlFormatter(
            cssclass="highlight",
            nowrap=False,
            style="monokai",
        )
        return highlight(code, lexer, formatter)


class MarkdownService:
    """Service for rendering Obsidian markdown to HTML."""

    def __init__(self):
        self.md = markdown.Markdown(
            extensions=[
                "fenced_code",
                "tables",
                "footnotes",
                "toc",
                "nl2br",
                "sane_lists",
                ObsidianExtension(),
            ],
            extension_configs={
                "toc": {
                    "permalink": True,
                    "permalink_class": "header-anchor",
                    "permalink_title": "Link to this section",
                },
            },
        )

    def render(self, content: str) -> str:
        """Render markdown content to HTML."""
        # Reset the markdown processor for each render
        self.md.reset()

        # Apply syntax highlighting to fenced code blocks
        content = self._highlight_code_blocks(content)

        # Render markdown
        html_content = self.md.convert(content)

        return html_content

    def _highlight_code_blocks(self, content: str) -> str:
        """Pre-process fenced code blocks with syntax highlighting."""

        def replace_code_block(match: re.Match) -> str:
            language = match.group(1) or ""
            code = match.group(2)

            if language:
                highlighted = CodeBlockFormatter.highlight_code(code, language)
                return f'<div class="code-block">{highlighted}</div>'
            else:
                # No language specified, just wrap in pre/code
                escaped = html.escape(code)
                return f'<div class="code-block"><pre><code>{escaped}</code></pre></div>'

        # Match fenced code blocks
        pattern = r"```(\w*)\n(.*?)```"
        return re.sub(pattern, replace_code_block, content, flags=re.DOTALL)


# Global markdown service instance
markdown_service = MarkdownService()


def render_markdown(content: str) -> str:
    """Render markdown content to HTML using the global service."""
    return markdown_service.render(content)

