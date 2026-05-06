# GeoAgent

CLI tool that transforms Chinese markdown articles into GEO-optimized versions with multi-language translations.

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Set API key
export ANTHROPIC_API_KEY="your-api-key"

# Transform an article (outputs target language GEO version)
geoagent transform article.md

# Specify target languages
geoagent transform article.md --lang en,ko,fr

# Full options
geoagent transform article.md \
  --model minimax/MiniMax-M2.7 \
  --output-dir ./output \
  --lang en,zh-TW,ko \
  --verbose
```

## Batch Processing

```bash
# Process all files in a directory (single-threaded)
geoagent transform cdcc --lang zh-TW

# Process with 4 concurrent threads (default)
geoagent transform cdcc --lang zh-TW -c 4

# Process with 8 concurrent threads (faster, but may hit API limits)
geoagent transform cdcc --lang zh-TW -c 8 --verbose

# Process directory recursively
geoagent transform cdcc -r --lang zh-TW
```

## CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `INPUT_PATH` | (required) | Input markdown file or directory |
| `--model` | `minimax/MiniMax-M2.7` | Model to use (`provider/model`) |
| `--output-dir` | `./output` | Output directory |
| `--lang` | `en` | Target languages (comma-separated) |
| `--geo-rules` | (built-in) | Custom GEO rules file |
| `--verbose` | false | Show detailed logs |
| `-r, --recursive` | false | Process directories recursively |
| `-c, --concurrency` | 4 | Number of concurrent threads |

## Supported Languages

- `en` - English
- `zh-TW` - Traditional Chinese (Taiwan)
- `zh-HK` - Traditional Chinese (Hong Kong)
- `ja` - Japanese
- `ko` - Korean
- `ar` - Arabic
- `fr` - French
- `de` - German
- `es` - Spanish

## Output Files

Given `article.md` with `--lang en,ko`, outputs only the GEO-optimized versions:

```
output/
├── article.en.geo.md   # GEO-optimized English
└── article.ko.geo.md   # GEO-optimized Korean
```

Each output file includes frontmatter with:
- `source`: Original filename
- `lang`: Target language
- `translated_from`: Source language
- `geo_optimized`: true
- `geo_rules_applied`: List of applied GEO rules
- `tags`: Extracted themes/topics

## Configuration

Create `~/.geoagent/config.yaml` to customize:

```yaml
default_model: minimax/MiniMax-M2.7

models:
  minimax:
    api_key_env: ANTHROPIC_API_KEY
    base_url: https://api.minimaxi.com/anthropic
    default_model: MiniMax-M2.7

  claude:
    api_key_env: ANTHROPIC_API_KEY
    base_url: https://api.anthropic.com
    default_model: claude-3-5-sonnet-20241022

  openai:
    api_key_env: OPENAI_API_KEY
    base_url: https://api.openai.com
    default_model: gpt-4o

geo:
  default_rules: shared/rubrics/content-quality-rubric.md
  min_score: 4

pipeline:
  max_tokens_translate: 8192   # Max tokens for translation
  max_tokens_geo: 8192         # Max tokens for GEO optimization
  max_tokens_understand: 2048   # Max tokens for document understanding
  max_retries: 3                # API retry attempts
  retry_base_delay: 1.0         # Base delay for exponential backoff (seconds)
```

## GEO Rules

The tool applies 6 optimization dimensions:

| Dimension | Description |
|-----------|-------------|
| `source_quality` | Add authoritative citations and official sources |
| `freshness` | Add dates, mention recent developments |
| `directness` | Lead with conclusion, front-load key points |
| `fairness` | Avoid promotion, balanced view |
| `traceability` | Add citation anchors, reference list |
| `anti_hallucination` | Avoid absolute claims, note uncertainty |

## Development

```bash
# Run tests
pytest -v

# Install in development mode
pip install -e ".[dev]"
```

## Project Structure

```
geoagent/
├── cli.py              # CLI entry point
├── config.py           # Configuration loader
├── pipeline.py         # Transformation pipeline
├── models/
│   ├── client.py      # Model clients (MiniMax, Claude, OpenAI)
│   └── document.py    # Document models
├── translator/
│   └── translator.py  # Multi-language translation
└── geo/
    ├── rules.py       # GEO rules definitions
    └── optimizer.py   # GEO optimization logic
```
