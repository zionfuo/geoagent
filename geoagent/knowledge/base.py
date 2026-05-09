"""Knowledge base system for geoagent."""
from dataclasses import dataclass, field
from typing import Optional
import hashlib
import re


@dataclass
class KnowledgeBase:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    content: str = ""
    character_count: int = 0
    used_task_count: int = 0
    file_type: str = "markdown"
    file_path: str = ""
    word_count: int = 0
    usage_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class KnowledgeChunk:
    id: Optional[int] = None
    knowledge_base_id: int = 0
    chunk_index: int = 0
    content: str = ""
    content_hash: str = ""
    token_count: int = 0
    embedding_json: str = ""
    embedding_model_id: Optional[int] = None
    embedding_dimensions: int = 0
    embedding_provider: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TextChunker:
    """Splits text into chunks by character count (900 chars), grouping paragraphs.

    Split strategy:
    1. Split on double newlines (\n\n) to get paragraphs
    2. Buffer paragraphs until adding next would exceed max_chars
    3. If a single paragraph exceeds max_chars, slice it by character offset
    """

    def __init__(self, max_chars: int = 900):
        self.max_chars = max_chars

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Chinese: ~1 token per character
        English: ~1.3 tokens per word
        """
        chinese_chars = len(re.findall(r'[一-鿿]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        return chinese_chars + int(english_words * 1.3)

    def compute_hash(self, content: str) -> str:
        """Compute SHA256 hash for deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def chunk(self, text: str) -> list[KnowledgeChunk]:
        """Split text into chunks of max_chars characters, grouping paragraphs."""
        chunks = []
        buffer: list[str] = []
        buffer_size = 0
        chunk_index = 0

        paragraphs = re.split(r'\n{2,}', text)

        for para in paragraphs:
            para_len = len(para)

            # If single paragraph exceeds max_chars, slice it directly
            if para_len > self.max_chars:
                # Emit current buffer first
                if buffer:
                    chunk_text = '\n\n'.join(buffer)
                    chunks.append(self._make_chunk(chunk_text, chunk_index))
                    chunk_index += 1
                    buffer = []
                    buffer_size = 0

                # Slice the long paragraph
                offset = 0
                while offset < para_len:
                    slice_text = para[offset:offset + self.max_chars]
                    chunks.append(self._make_chunk(slice_text, chunk_index))
                    chunk_index += 1
                    offset += self.max_chars
                continue

            # Add paragraph to buffer
            if buffer_size + para_len + 2 > self.max_chars and buffer:
                # Emit current buffer
                chunk_text = '\n\n'.join(buffer)
                chunks.append(self._make_chunk(chunk_text, chunk_index))
                chunk_index += 1
                buffer = []
                buffer_size = 0

            buffer.append(para)
            buffer_size += para_len + 2

        # Emit remaining buffer
        if buffer:
            chunk_text = '\n\n'.join(buffer)
            chunks.append(self._make_chunk(chunk_text, chunk_index))

        return chunks

    def _make_chunk(self, content: str, index: int) -> KnowledgeChunk:
        return KnowledgeChunk(
            content=content,
            content_hash=self.compute_hash(content),
            token_count=self.estimate_tokens(content),
            chunk_index=index,
        )
