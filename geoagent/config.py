# geoagent/config.py
"""Configuration loader for geoagent."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml

from geoagent.models.client import MiniMaxClient, ClaudeClient, OpenAIClient, ModelClient


@dataclass
class ModelConfig:
    api_key_env: str
    base_url: Optional[str] = None
    default_model: Optional[str] = None


@dataclass
class Config:
    default_model: str
    models: dict[str, ModelConfig]
    geo_rules_path: Optional[str] = None
    geo_min_score: int = 4
    max_tokens_translate: int = 8192
    max_tokens_geo: int = 8192
    max_tokens_understand: int = 2048
    max_retries: int = 3
    retry_base_delay: float = 1.0

    @classmethod
    def from_file(cls, path: str) -> "Config":
        with open(path) as f:
            data = yaml.safe_load(f)

        models = {}
        for name, model_data in data.get('models', {}).items():
            models[name] = ModelConfig(
                api_key_env=model_data['api_key_env'],
                base_url=model_data.get('base_url'),
                default_model=model_data.get('default_model')
            )

        pipeline_config = data.get('pipeline', {})
        return cls(
            default_model=data.get('default_model', 'minimax/MiniMax-M2.7'),
            models=models,
            geo_rules_path=data.get('geo', {}).get('default_rules'),
            geo_min_score=data.get('geo', {}).get('min_score', 4),
            max_tokens_translate=pipeline_config.get('max_tokens_translate', 8192),
            max_tokens_geo=pipeline_config.get('max_tokens_geo', 8192),
            max_tokens_understand=pipeline_config.get('max_tokens_understand', 2048),
            max_retries=pipeline_config.get('max_retries', 3),
            retry_base_delay=pipeline_config.get('retry_base_delay', 1.0)
        )

    def get_model_client(self, provider: str, api_key: str) -> ModelClient:
        model_config = self.models.get(provider)
        if not model_config:
            raise ValueError(f"Unknown model provider: {provider}")

        if provider == 'minimax':
            return MiniMaxClient(
                api_key=api_key,
                base_url=model_config.base_url or "https://api.minimaxi.com/anthropic"
            )
        elif provider == 'claude':
            return ClaudeClient(
                api_key=api_key,
                base_url=model_config.base_url or "https://api.anthropic.com"
            )
        elif provider == 'openai':
            return OpenAIClient(
                api_key=api_key,
                base_url=model_config.base_url or "https://api.openai.com"
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def get_default_model(self, provider: str) -> str:
        model_config = self.models.get(provider)
        if model_config and model_config.default_model:
            return model_config.default_model
        return "MiniMax-M2.7"

    @classmethod
    def default(cls) -> "Config":
        """Create a default config without reading from file."""
        return cls(
            default_model="minimax/MiniMax-M2.7",
            models={
                "minimax": ModelConfig(
                    api_key_env="ANTHROPIC_API_KEY",
                    base_url="https://api.minimaxi.com/anthropic",
                    default_model="MiniMax-M2.7"
                )
            }
        )