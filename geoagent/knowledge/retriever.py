"""Hybrid search retriever for knowledge chunks."""
import math
import re
from typing import Optional

from geoagent.db.connection import Database
from geoagent.knowledge.embedder import Embedder


class KnowledgeRetriever:
    """Retrieves knowledge chunks using hybrid scoring (75% vector + 25% lexical)."""

    def __init__(self, db: Optional[Database] = None, embedder: Optional[Embedder] = None):
        self.db = db or Database.get_instance()
        self.embedder = embedder or Embedder()

    def _conn(self):
        return self.db.get_connection()

    def term_frequencies(self, text: str) -> dict[str, int]:
        """Extract tokens and count frequencies."""
        latin = re.findall(r'[a-z0-9][a-z0-9._+#-]{1,}', text.lower())
        cjk = re.findall(r'[\p{Han}]{2,32}', text)
        tokens = latin + cjk
        freq = {}
        for tok in tokens:
            freq[tok] = freq.get(tok, 0) + 1
        return freq

    def lexical_score(self, query_terms: dict[str, int], chunk_terms: dict[str, int]) -> float:
        """Compute term frequency overlap score: matched / total_query_terms."""
        matched = sum(1 for t in query_terms if t in chunk_terms)
        total = len(query_terms)
        return matched / total if total > 0 else 0.0

    def dot_product(self, a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def fetch_knowledge_context(
        self,
        knowledge_base_id: int,
        query: str,
        limit: int = 4,
        max_chars: int = 2400
    ) -> str:
        """Fetch top knowledge chunks for a query using hybrid scoring.

        Returns concatenated chunks as a string, ready for {{Knowledge}} injection.
        """
        conn = self._conn()
        cursor = conn.cursor()

        # Try pgvector first
        vector_score_rows = self._pgvector_search(cursor, knowledge_base_id, query, limit * 3)
        if vector_score_rows is not None:
            return self._compose_result(vector_score_rows, limit, max_chars)

        # Fallback: hybrid scoring
        rows = cursor.execute(
            "SELECT id, chunk_index, content, embedding_json FROM knowledge_chunks WHERE knowledge_base_id = ?",
            (knowledge_base_id,)
        ).fetchall()

        if not rows:
            return ""

        query_terms = self.term_frequencies(query)
        query_vector = self.embedder.build_fallback_vector(query, 256)

        scored = []
        for row in rows:
            chunk_terms = self.term_frequencies(row["content"])
            lexical = self.lexical_score(query_terms, chunk_terms)

            embed_json = row["embedding_json"]
            if embed_json:
                chunk_vector = self.embedder.decode_vector(embed_json)
                vector_score = self.dot_product(query_vector, chunk_vector)
            else:
                vector_score = 0.0

            score = (vector_score * 0.75) + (lexical * 0.25)
            scored.append({
                "chunk_index": row["chunk_index"],
                "content": row["content"],
                "score": score,
            })

        scored.sort(key=lambda x: (-x["score"], x["chunk_index"]))
        return self._compose_result(scored, limit, max_chars)

    def _pgvector_search(
        self,
        cursor,
        knowledge_base_id: int,
        query: str,
        limit: int
    ):
        """Try pgvector cosine similarity search. Returns None if pgvector unavailable."""
        try:
            query_vector = self.embedder.encode(query)
            if not query_vector:
                return None

            # Build vector literal string for PostgreSQL
            vec_str = "[" + ",".join(str(v) for v in query_vector) + "]"

            rows = cursor.execute(
                f"""SELECT id, chunk_index, content, embedding_vector
                    FROM knowledge_chunks
                    WHERE knowledge_base_id = ?
                    ORDER BY embedding_vector <=> CAST(:vec AS vector)
                    LIMIT :limit""",
                {"vec": vec_str, "limit": limit}
            ).fetchall()

            if not rows:
                return None

            # Convert pgvector to similarity scores (lower = closer)
            scored = []
            for row in rows:
                # embedding_vector <=> returns cosine distance (0=identical, 2=opposite)
                # Convert to similarity score
                scored.append({
                    "chunk_index": row["chunk_index"],
                    "content": row["content"],
                    "score": 1.0 - row["embedding_vector"],  # approximate
                })
            return scored
        except Exception:
            return None

    def _compose_result(self, scored: list[dict], limit: int, max_chars: int) -> str:
        """Compose knowledge context from top scored chunks, sorted by chunk_index."""
        selected = sorted(scored[:limit], key=lambda x: x["chunk_index"])
        parts = []
        total = 0
        for i, item in enumerate(selected):
            header = f"【知识片段{i + 1}】"
            content = item["content"]
            if total + len(header) + len(content) + 2 > max_chars:
                break
            parts.append(f"{header}\n{content}")
            total += len(header) + len(content) + 2

        return "\n\n".join(parts)
