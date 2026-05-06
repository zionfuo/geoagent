# GeoAgent

CLI tool for transforming Chinese markdown articles into GEO-optimized versions with multi-language translations.

## Project Overview

- **Type**: Python CLI application
- **Core Functionality**: Read markdown articles, translate to multiple languages, optimize for AI search engine citation (GEO)
- **Tech Stack**: Python 3.10+, click, anthropic, openai, pyyaml, rich, markdown

## Architecture

```
Input: article.md
         │
         ▼
Pipeline: read → understand → translate → GEO optimize → write
         │
         ▼
Output: article.zh.md, article.en.md, article.en.geo.md, etc.
```

## Key Files

| File | Purpose |
|------|---------|
| `geoagent/cli.py` | CLI entry point using click |
| `geoagent/pipeline.py` | Main transformation pipeline orchestrator |
| `geoagent/config.py` | YAML config loader and model client factory |
| `geoagent/models/client.py` | Model clients (MiniMax, Claude, OpenAI) |
| `geoagent/models/document.py` | MarkdownDocument and DocContext |
| `geoagent/translator/translator.py` | Multi-language translation |
| `geoagent/geo/rules.py` | GEO rules (6 dimensions) |
| `geoagent/geo/optimizer.py` | GEO optimization logic |
| `shared/rubrics/content-quality-rubric.md` | GEO quality rubric |

## Commands

```bash
# Install
pip install -e .

# Run
export ANTHROPIC_API_KEY="your-key"

# Single file
geoagent transform article.md --lang en,ko,fr --verbose

# Batch processing with 4 threads (default)
geoagent transform cdcc --lang zh-TW -c 4 --verbose

# Recursive batch processing
geoagent transform cdcc -r --lang zh-TW
```

## Development

```bash
# Run tests
pytest -v

# All tests should pass (18 tests)
```

## Supported Languages

en, zh-TW, zh-HK, ja, ko, ar, fr, de, es

## GEO Rules (6 dimensions)

1. source_quality - Authoritative citations
2. freshness - Recent developments
3. directness - Front-load key points
4. fairness - Balanced view
5. traceability - Citation anchors
6. anti_hallucination - Avoid absolute claims

## Adding New Model Providers

Implement `ModelClient` interface in `geoagent/models/client.py`:

```python
class ModelClient(ABC):
    @abstractmethod
    def complete(self, model: str, messages: list[dict], **kwargs) -> str:
        raise NotImplementedError
```

Then register in `geoagent/config.py` → `Config.get_model_client()`.

## Design Decisions

- Uses Anthropic-compatible API interface for MiniMax
- GEO rules based on yao-geo-skills rubric
- TDD approach with tests in `tests/`
- YAML configuration in `~/.geoagent/config.yaml`
- API calls include automatic retry with exponential backoff (configurable via `max_retries`, `retry_base_delay`)
- `understand()` parses LLM response as JSON for structured DocContext

## Config Options

| Option | Default | Description |
|--------|---------|-------------|
| `max_tokens_translate` | 8192 | Max tokens for translation |
| `max_tokens_geo` | 8192 | Max tokens for GEO optimization |
| `max_tokens_understand` | 2048 | Max tokens for document understanding |
| `max_retries` | 3 | API retry attempts |
| `retry_base_delay` | 1.0 | Base delay for exponential backoff (seconds) |
