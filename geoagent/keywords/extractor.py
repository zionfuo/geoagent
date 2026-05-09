"""Keyword extraction for geoagent."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class KeywordLibrary:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    keyword_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Keyword:
    id: Optional[int] = None
    library_id: int = 0
    keyword: str = ""
    used_count: int = 0
    usage_count: int = 0
    created_at: Optional[str] = None


class KeywordExtractor:
    """Extract keywords from text using LLM."""

    def __init__(self, model_client):
        self.model_client = model_client

    def extract(self, text: str, max_keywords: int = 10) -> list[str]:
        """Extract keywords from text using the model."""
        prompt = f"""Extract the {max_keywords} most important keywords from the following text.
Return only a JSON array of keyword strings, nothing else.

Text:
{text[:2000]}

Output format: ["keyword1", "keyword2", ...]"""

        messages = [{"role": "user", "content": prompt}]
        response = self.model_client.complete("generate", messages, max_tokens=500)

        import json
        try:
            keywords = json.loads(response.strip())
            if isinstance(keywords, list):
                return [k for k in keywords if isinstance(k, str)]
        except json.JSONDecodeError:
            pass

        return []
