"""Model client implementations for MiniMax, Claude, OpenAI."""
from abc import ABC, abstractmethod
import time
import logging
from typing import Any
import anthropic
import openai

logger = logging.getLogger(__name__)


class ModelClient(ABC):
    """Base class for model clients."""

    max_retries: int = 3
    retry_base_delay: float = 1.0

    @abstractmethod
    def complete(self, model: str, messages: list[dict], **kwargs) -> str:
        """Send messages to model and return response."""
        raise NotImplementedError

    def _retry_on_error(self, func, *args, **kwargs):
        """Retry a function with exponential backoff on errors."""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
        raise last_exception


class MiniMaxClient(ModelClient):
    """MiniMax API (Anthropic-compatible)."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.minimaxi.com/anthropic",
        max_retries: int = 3,
        retry_base_delay: float = 1.0
    ):
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

    def complete(self, model: str, messages: list[dict], thinking: bool = False, include_thinking: bool = True, **kwargs) -> str:
        def _call():
            extra_kwargs = {}
            if thinking:
                extra_kwargs["thinking"] = {"type": "enabled", "budget_tokens": 10000}

            response = self.client.messages.create(
                model=model,
                messages=messages,
                **kwargs,
                **extra_kwargs
            )

            output = []
            for block in response.content:
                if block.type == "thinking":
                    if include_thinking:
                        output.append(f"<!-- Thinking:\n{block.thinking}\n-->")
                elif block.type == "text":
                    output.append(block.text)
            return "\n".join(output)

        return self._retry_on_error(_call)


class ClaudeClient(ModelClient):
    """Anthropic Claude API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com",
        max_retries: int = 3,
        retry_base_delay: float = 1.0
    ):
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

    def complete(self, model: str, messages: list[dict], **kwargs) -> str:
        def _call():
            response = self.client.messages.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return "\n".join(block.text for block in response.content if block.type == "text")

        return self._retry_on_error(_call)


class OpenAIClient(ModelClient):
    """OpenAI API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com",
        max_retries: int = 3,
        retry_base_delay: float = 1.0
    ):
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

    def complete(self, model: str, messages: list[dict], **kwargs) -> str:
        def _call():
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content

        return self._retry_on_error(_call)
