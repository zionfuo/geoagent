"""Document models for markdown processing."""
import re
from dataclasses import dataclass, field
from typing import Optional


THINKING_PATTERN = re.compile(r'<!-- Thinking:[\s\S]*?-->')
THINKING_BLOCK_PATTERN = re.compile(r'<!\-\- Thinking:[\s\S]*?\-\->', re.MULTILINE)


@dataclass
class MarkdownDocument:
    title: str
    content: str
    frontmatter: dict = field(default_factory=dict)

    def _clean_content(self, content: str) -> str:
        """Remove thinking comments from content."""
        content = THINKING_BLOCK_PATTERN.sub('', content)
        content = THINKING_PATTERN.sub('', content)
        return content.strip()

    def __str__(self) -> str:
        lines = ["---"]
        for key, value in self.frontmatter.items():
            lines.append(f"{key}: {value}")
        lines.append("---")
        if self.title and self.title != "Untitled":
            lines.append("")
            lines.append(f"# {self.title}")
        cleaned_content = self._clean_content(self.content)
        if cleaned_content:
            lines.append("")
            lines.append(cleaned_content)
        return "\n".join(lines)

    def with_frontmatter(self, **kwargs) -> "MarkdownDocument":
        """Return a copy with additional frontmatter."""
        new_fm = {**self.frontmatter, **kwargs}
        return MarkdownDocument(title=self.title, content=self.content, frontmatter=new_fm)


@dataclass
class DocContext:
    """Context extracted from document during understanding phase."""
    title: str
    themes: list[str] = field(default_factory=list)
    terminology: dict[str, str] = field(default_factory=dict)
    structure: dict = field(default_factory=dict)
    summary: str = ""

    def format_for_prompt(self) -> str:
        parts = [f"Title: {self.title}"]
        if self.themes:
            parts.append(f"Themes: {', '.join(self.themes)}")
        if self.terminology:
            terms = [f"{k}: {v}" for k, v in self.terminology.items()]
            parts.append(f"Key Terms: {', '.join(terms)}")
        if self.summary:
            parts.append(f"Summary: {self.summary}")
        return "\n".join(parts)