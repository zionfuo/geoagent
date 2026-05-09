"""Embedding generation for knowledge chunks."""
from typing import Optional
import math
import re


class Embedder:
    """Generates embeddings for knowledge chunks.

    Supports:
    - Real embeddings via model API (when embedding_model_id is configured)
    - Fallback normalized hash vectors stored as JSON
    """

    def __init__(self, model_client=None, embedding_provider: str = ""):
        self.model_client = model_client
        self.embedding_provider = embedding_provider

    def build_fallback_vector(self, text: str, dimensions: int = 256) -> list[float]:
        """Build a normalized term-frequency vector for fallback search.

        Uses term frequency scoring: alphanumeric + CJK tokens.
        Returns a normalized (L2) vector.
        """
        tokens = self._extract_tokens(text)
        freq: dict[str, int] = {}
        for tok in tokens:
            freq[tok] = freq.get(tok, 0) + 1

        # Build sparse vector for top tokens by frequency
        sorted_tokens = sorted(freq.items(), key=lambda x: -x[1])
        vector = [0.0] * dimensions
        for i, (tok, count) in enumerate(sorted_tokens[:dimensions]):
            vector[i] = float(count)

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def _extract_tokens(self, text: str) -> list[str]:
        """Extract alphanumeric tokens and CJK character sequences."""
        latin = re.findall(r'[a-z0-9][a-z0-9._+#-]{1,}', text.lower())
        cjk = re.findall(r'[\p{Han}]{2,32}', text)
        return latin + cjk

    def encode(self, text: str) -> list[float]:
        """Encode text to embedding vector.

        Uses real embedding API if model_client is available,
        otherwise returns fallback vector.
        """
        if self.model_client:
            # Real embedding via API
            try:
                messages = [
                    {"role": "user", "content": f"Embedding: {text[:500]}"}
                ]
                result = self.model_client.complete(
                    "embed",
                    messages,
                    max_tokens=512
                )
                # Parse JSON result: {"embedding": [...]} or raw list
                import json
                try:
                    data = json.loads(result)
                    if isinstance(data, dict) and "embedding" in data:
                        return data["embedding"]
                    if isinstance(data, list):
                        return data
                except json.JSONDecodeError:
                    pass
            except Exception:
                pass

        # Fallback: normalized hash vector
        return self.build_fallback_vector(text, 256)

    def decode_vector(self, json_str: str) -> list[float]:
        """Decode a JSON string back to a vector."""
        import json
        data = json.loads(json_str)
        return data if isinstance(data, list) else []
