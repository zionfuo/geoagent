# geoagent/geo/optimizer.py
"""GEO optimization logic."""
import json
import logging
from geoagent.geo.rules import GEORules
from geoagent.models.client import ModelClient
from geoagent.models.document import MarkdownDocument, DocContext


logger = logging.getLogger(__name__)

UNDERSTAND_PROMPT = """Analyze this document and return a JSON object with the following structure:

{{
    "themes": ["theme1", "theme2"],
    "summary": "Brief summary of the document content"
}}

Document:
---
{content}
---

Respond ONLY with the JSON object, no additional text."""

GEO_OPTIMIZATION_PROMPT = """You are a GEO (Generative Engine Optimization) expert. Optimize the following document to maximize its likelihood of being cited by AI search engines.

{geo_rules}

Original document:
---
{content}
---

Requirements:
1. Lead with the main conclusion or answer
2. Add specific data points, dates, and authoritative sources where missing
3. Use clear, factual language - avoid exaggeration
4. Structure with clear headings that answer common questions
5. Add a references section if none exists

Optimized version:"""


class GEOOptimizer:
    """Applies GEO rules to optimize documents for AI search citation."""

    def __init__(self, rules: GEORules, client: ModelClient = None):
        self.rules = rules
        self.client = client

    def _extract_themes(self, content: str, model_client: ModelClient, model: str, max_tokens: int) -> list[str]:
        """Extract themes from document content."""
        messages = [
            {"role": "user", "content": UNDERSTAND_PROMPT.format(content=content)}
        ]
        result = model_client.complete(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            include_thinking=False
        )
        try:
            data = json.loads(result)
            return data.get("themes", [])
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse themes JSON: {e}")
            return []

    def optimize(
        self,
        doc: MarkdownDocument,
        model_client: ModelClient,
        model: str,
        max_tokens: int = 8192,
        max_tokens_understand: int = 2048
    ) -> MarkdownDocument:
        """Optimize document using GEO rules (also extracts themes in single pass)."""
        if not model_client:
            if not self.client:
                raise ValueError("No model client provided")
            model_client = self.client

        # Extract themes from content
        themes = self._extract_themes(doc.content, model_client, model, max_tokens_understand)

        geo_rules_prompt = self.rules.get_optimization_prompt()

        system_prompt = """You are a GEO (Generative Engine Optimization) expert.
Optimize content to be cited by AI search engines like Perplexity, ChatGPT, and Claude.
Focus on: authority, freshness, directness, fairness, traceability, and avoiding hallucinations."""

        user_prompt = GEO_OPTIMIZATION_PROMPT.format(
            geo_rules=geo_rules_prompt,
            content=doc.content
        )

        messages = [
            {"role": "user", "content": user_prompt}
        ]

        optimized_content = model_client.complete(
            model=model,
            messages=messages,
            system=system_prompt,
            max_tokens=max_tokens
        )

        applied_rules = list(self.rules.dimensions.keys())

        frontmatter = {
            **doc.frontmatter,
            "geo_optimized": True,
            "geo_rules_applied": applied_rules
        }

        if themes:
            frontmatter["tags"] = themes

        return MarkdownDocument(
            title=doc.title,
            content=optimized_content.strip(),
            frontmatter=frontmatter
        )