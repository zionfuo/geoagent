# geoagent/pipeline.py
"""Main pipeline orchestrator for document transformation."""
import os
import re
from pathlib import Path

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
        max_tokens_understand: int = 2048
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
        self.optimizer = GEOOptimizer(geo_rules)

    def read_input(self, path: str) -> MarkdownDocument:
        """Read and parse input markdown file."""
        content = Path(path).read_text(encoding='utf-8')

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
        resume: bool = False
    ) -> list[str]:
        """Run full transformation pipeline."""
        os.makedirs(output_dir, exist_ok=True)
        input_file = Path(input_path)
        base_name = input_file.stem

        doc = self.read_input(input_path)

        output_files = []

        for lang in target_languages:
            translated_geo_path = os.path.join(output_dir, f"{base_name}.{lang}.geo.md")

            # Resume check: skip if output file already exists
            if resume and os.path.exists(translated_geo_path):
                logger.info(f"Skipping {lang} - output file already exists: {translated_geo_path}")
                output_files.append(translated_geo_path)
                continue

            translated = self.translator.translate(doc, lang)
            translated_geo = self.optimizer.optimize(
                translated, self.model_client, self.default_model,
                max_tokens=self.max_tokens_geo,
                max_tokens_understand=self.max_tokens_understand
            )
            Path(translated_geo_path).write_text(str(translated_geo), encoding='utf-8')
            output_files.append(translated_geo_path)

        return output_files

    def _extract_title(self, content: str) -> str:
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled"

    def _strip_title(self, content: str) -> str:
        return re.sub(r'^#\s+.+\n+', '', content, count=1)

    def _get_date(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
