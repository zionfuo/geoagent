# geoagent/pipeline.py
"""Main pipeline orchestrator for document transformation."""
import os
import re
from pathlib import Path
from typing import Optional

from geoagent.models.client import ModelClient
from geoagent.models.document import MarkdownDocument
from geoagent.geo.rules import GEORules
from geoagent.geo.optimizer import GEOOptimizer
from geoagent.translator.translator import Translator


class Pipeline:
    """Orchestrates the document transformation pipeline."""

    def __init__(
        self,
        model_client: ModelClient,
        translation_client: ModelClient,
        geo_rules: GEORules,
        default_model: str,
        max_tokens_translate: int = 8192,
        max_tokens_geo: int = 8192,
        max_tokens_understand: int = 2048,
        geo_prompt_template: Optional[str] = None,
        db_path: Optional[str] = None,
        template_type: str = "trust"
    ):
        self.client = model_client
        self.model_client = model_client
        self.translation_client = translation_client
        self.geo_rules = geo_rules
        self.default_model = default_model
        self.max_tokens_translate = max_tokens_translate
        self.max_tokens_geo = max_tokens_geo
        self.max_tokens_understand = max_tokens_understand
        self.translator = Translator(translation_client, default_model, max_tokens_translate)
        self.optimizer = GEOOptimizer(geo_rules, prompt_template_name=geo_prompt_template, db_path=db_path, template_type=template_type)
        self._db_path = db_path
        self._template_type = template_type

    def read_input(self, path: str) -> MarkdownDocument:
        """Read and parse input markdown file."""
        content = Path(path).read_text(encoding='utf-8')

        # Strip WeChat HTML export garbage
        content = self._strip_wechat_garbage(content)

        title = self._extract_title(content)
        body = self._strip_title(content)

        return MarkdownDocument(
            title=title,
            content=body.strip(),
            frontmatter={
                "source": Path(path).name,
                "lang": "zh",
                "created_at": self._get_date()
            }
        )

    def transform(
        self,
        input_path: str,
        output_dir: str,
        target_languages: list[str],
        resume: bool = False,
        source_root: str = None
    ) -> list[str]:
        """Run full transformation pipeline."""
        input_file = Path(input_path)
        source_root_path = Path(source_root) if source_root else input_file.parent

        # Calculate relative path to preserve directory structure
        try:
            rel_path = input_file.relative_to(source_root_path)
            rel_dir = rel_path.parent
            output_subdir = Path(output_dir) / rel_dir if rel_dir != Path('.') else Path(output_dir)
        except ValueError:
            output_subdir = Path(output_dir)

        output_subdir.mkdir(parents=True, exist_ok=True)

        base_name = input_file.stem

        doc = self.read_input(input_path)

        output_files = []

        for lang in target_languages:
            translated_geo_path = str(output_subdir / f"{base_name}.{lang}.geo.md")

            # Resume check: skip if output file already exists
            if resume and os.path.exists(translated_geo_path):
                from logging import getLogger
                getLogger(__name__).info(f"Skipping {lang} - output file already exists: {translated_geo_path}")
                output_files.append(translated_geo_path)
                continue

            translated = self.translator.translate(doc, lang)
            translated_geo = self.optimizer.optimize(
                translated, self.model_client, self.default_model,
                max_tokens=self.max_tokens_geo,
                lang=lang
            )
            Path(translated_geo_path).write_text(str(translated_geo), encoding='utf-8')
            output_files.append(translated_geo_path)

        return output_files

    def _extract_title(self, content: str) -> str:
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled"

    def _strip_wechat_garbage(self, content: str) -> str:
        """Strip WeChat HTML export garbage and convert title format."""
        lines = content.split('\n')
        cleaned_lines = []
        found_content = False
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Check for title with underline pattern: "Title\n========"
            if not found_content and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if (next_line and all(c == '=' for c in next_line) and
                    not stripped.startswith('# ') and
                    len(stripped) > 5 and
                    not stripped.startswith('{') and
                    not stripped.startswith('}') and
                    not stripped.startswith('.__') and
                    not 'margin:' in stripped and
                    not 'font-family:' in stripped and
                    not 'padding:' in stripped):
                    # This is a title line with underline - convert to markdown heading
                    found_content = True
                    cleaned_lines.append('# ' + stripped)
                    i += 2  # Skip the title line and the underline
                    continue

            if not found_content:
                if stripped.startswith('# ') or stripped.startswith('## ') or stripped.startswith('---'):
                    found_content = True
                    cleaned_lines.append(line)
                elif (len(stripped) > 10 and
                      not stripped.startswith('{') and
                      not stripped.startswith('}') and
                      not stripped.startswith('.__') and
                      not 'margin:' in stripped and
                      not 'font-family:' in stripped and
                      not 'padding:' in stripped):
                    found_content = True
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)

            i += 1

        return '\n'.join(cleaned_lines)

    def _strip_title(self, content: str) -> str:
        return re.sub(r'^#\s+.+\n+', '', content, count=1)

    def _get_date(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
