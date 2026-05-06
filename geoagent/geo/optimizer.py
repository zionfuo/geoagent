# geoagent/geo/optimizer.py
"""GEO optimization logic."""
from geoagent.geo.rules import GEORules
from geoagent.models.client import ModelClient
from geoagent.models.document import MarkdownDocument, DocContext


GEO_OPTIMIZATION_PROMPT = """You are a GEO (Generative Engine Optimization) expert. Optimize the following document to maximize its likelihood of being cited by AI search engines.

{geo_rules}

Original document:
---
{content}
---

Document context:
{context}

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

    def optimize(
        self,
        doc: MarkdownDocument,
        context: DocContext,
        model_client: ModelClient,
        model: str,
        max_tokens: int = 8192
    ) -> MarkdownDocument:
        """Optimize document using GEO rules."""
        if not model_client:
            if not self.client:
                raise ValueError("No model client provided")
            model_client = self.client

        geo_rules_prompt = self.rules.get_optimization_prompt()
        context_prompt = context.format_for_prompt() if context else "No additional context"

        system_prompt = """You are a GEO (Generative Engine Optimization) expert.
Optimize content to be cited by AI search engines like Perplexity, ChatGPT, and Claude.
Focus on: authority, freshness, directness, fairness, traceability, and avoiding hallucinations."""

        user_prompt = GEO_OPTIMIZATION_PROMPT.format(
            geo_rules=geo_rules_prompt,
            content=doc.content,
            context=context_prompt
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

        if context and context.themes:
            frontmatter["tags"] = context.themes

        return MarkdownDocument(
            title=doc.title,
            content=optimized_content.strip(),
            frontmatter=frontmatter
        )