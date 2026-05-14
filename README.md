# GeoAgent

CLI tool that transforms Chinese markdown articles into GEO-optimized versions with multi-language translations.

## Installation

```bash
pip install py-geoagent
```

Or install from source:

```bash
pip install -e .
```

**PyPI:** https://pypi.org/project/py-geoagent/

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

## GEO Template Types

GeoAgent supports two article generation styles, each with templates in all 9 supported languages:

### Trust-Based (default)
Long-form articles with E-E-A-T signals, structured sections (Key Takeaways, Intro, 3-5 Main Sections, FAQ, Conclusion).

### Ranking-Style
Comparison/ranking articles with TOP1 rankings, strengths+limitations, comparison tables, scenario recommendations.

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
| `--geo-prompt` | (auto) | Specific GEO template name |
| `--template-type` | `trust` | Template style: `trust` or `ranking` |
| `--verbose` | false | Show detailed logs |
| `-r, --recursive` | false | Process directories recursively |
| `-c, --concurrency` | 4 | Number of concurrent threads |
| `--resume` | false | Skip completed language outputs |

## GEO Prompt Templates

Each language auto-selects the correct template. Use `geoagent prompts list` to see all available templates.

```bash
# Initialize database and seed all 20 prompt templates
geoagent init-db

# List all templates
geoagent prompts list

# Show a specific template
geoagent prompts show "GEO Marketing · Trust-Based Article Generation (Japanese)"

# Render a template with variables
geoagent prompts render "GEO Marketing · Trust-Based Article Generation (English)" \
  --var title="How to Choose a Laptop" \
  --var keyword="laptop buying guide"
```

### Auto Language Matching

When running `transform`, GeoAgent automatically selects the template matching the target language:

| Language | Trust-Based Template | Ranking Template |
|----------|---------------------|------------------|
| `en` | English | English |
| `zh-TW` | Traditional Chinese (Taiwan) | Traditional Chinese (Taiwan) |
| `zh-HK` | Traditional Chinese (Hong Kong) | Traditional Chinese (Hong Kong) |
| `ja` | Japanese | Japanese |
| `ko` | Korean | Korean |
| `ar` | Arabic | Arabic |
| `fr` | French | French |
| `de` | German | German |
| `es` | Spanish | Spanish |

### Template Type Selection

```bash
# Use Trust-Based style (default)
geoagent transform article.md --lang en

# Use Ranking style
geoagent transform article.md --lang en --template-type ranking

# Use a specific template (overrides auto-select)
geoagent transform article.md --lang en \
  --geo-prompt "GEO Ranking-Style Article Generation (English)"
```

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

## Database

GeoAgent uses SQLite for persistent storage of prompt templates, articles, tasks, and more.

```bash
# Initialize database (creates tables and seeds default prompts)
geoagent init-db

# Database location: ~/.geoagent/geoagent.db (or custom via config)
```

### Database CLI Commands

```bash
# Article management
geoagent article new "My Article Title" --content "Article body..." --category-id 1 --author-id 1
geoagent article list
geoagent article list --status draft
geoagent article publish 123
geoagent article hot 123 --enable
geoagent article featured 123 --disable

# Task management
geoagent task list
geoagent task run 1
geoagent task stop 1

# URL import pipeline
geoagent url-import submit https://example.com/article
geoagent url-import status 1
geoagent url-import logs 1

# Admin settings
geoagent admin settings --key site_name --value "My Site"
geoagent admin settings --key site_name
```

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
- `geo_template`: Name of GEO template used
- `geo_rules_applied`: List of applied GEO rules

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
  max_tokens_geo: 8192           # Max tokens for GEO optimization
  max_tokens_understand: 2048   # Max tokens for document understanding
  max_retries: 3                # API retry attempts
  retry_base_delay: 1.0         # Base delay for exponential backoff (seconds)

database:
  path: ~/.geoagent/geoagent.db  # SQLite database path (optional)
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

## AI Title Generation

Generate titles in 5 styles using AI, with mock template fallback.

```bash
# Generate titles with specific keywords and style
geoagent title generate -k "AI" " laptops" --style seo --count 3

# Available styles:
#   professional  - 专业严谨的
#   attractive    - 吸引眼球的
#   seo           - SEO优化的
#   creative      - 创意新颖的
#   question      - 疑问式的
```

### Mock Fallback

When AI fails, titles are generated from built-in templates:

| Style | Example Templates |
|-------|-------------------|
| `professional` | {keyword}的深度分析与研究, 关于{kw}的专业见解 |
| `attractive` | 你绝对不知道的{kw}秘密, 揭秘{kw}背后的故事 |
| `seo` | {kw}完整指南：从入门到精通, {kw}常见问题解答大全 |
| `creative` | 重新定义{kw}的可能性, 如果{kw}会说话... |
| `question` | {kw}真的有用吗？, 为什么{kw}如此重要？ |

## Article Generation (GEOFlow Pipeline)

Generate articles using the full GEOFlow pipeline with knowledge RAG, image insertion, and auto-publishing.

```bash
# Generate article for a task
geoagent article generate 1

# With knowledge base RAG
geoagent article generate 1 --knowledge-base-id 1 --style professional

# With custom keyword
geoagent article generate 1 --keyword "AI laptops"
```

### Pipeline Steps

```
1. publishDueDraftArticle()     — Auto-publish approved drafts when due
2. getGenerationBlockReason()   — Check draft_limit / article_limit
3. pickTitle()                  — Title with lowest used_count
4. resolveKnowledgeContext()    — RAG: hybrid search (75% vector + 25% lexical)
5. buildContentPrompt()         — Render {{title}} {{keyword}} {{Knowledge}}
6. generateContent()            — AI model generation
7. insertTaskImagesIntoContent() — Distribute images by paragraph interval
8. buildExcerpt()               — First 200 chars as excerpt
9. Create Article               — status='draft', review_status='pending'
10. Update counters             — Title.used_count++, Task.created_count++
```

## Knowledge RAG

Retrieves relevant knowledge chunks for injection into prompts as `{{Knowledge}}`.

```bash
# Knowledge base chunking uses 900-char segments split on \n\n
# Retrieval uses hybrid scoring: 0.75 * cosine_similarity + 0.25 * term_overlap
# Returns up to 4 chunks with max 2400 characters total
```

### Embedding Models

- **Real embeddings**: Call embedding API (configurable via `site_settings.default_embedding_model_id`)
- **Fallback vectors**: 256-dim normalized term-frequency vectors stored as JSON

## Image Insertion

Images from task's image library are inserted at paragraph intervals, not stacked at the end.

```python
# Algorithm: interval = floor(paragraphCount / (imageCount + 1))
# Insert after paragraph where nextPosition % interval == 0
# Format: ![alt](url) Markdown
```

## Background Worker

Run the GEOFlow worker loop for automated article generation and publishing.

```bash
# Poll for due tasks and run them
geoagent worker --poll-interval 60

# Run a specific task only
geoagent worker --task-id 1

# Worker loop behavior:
#   1. recoverStaleJobs() on startup
#   2. Poll active tasks every N seconds
#   3. Advance next_run_at by 60s after enqueueing
#   4. Run task until article_limit reached or is_loop=0
#   5. Auto-publish due drafts before generating new content
```

## Batch Translation with Directory Structure Preservation

Translate a collection of articles while preserving their original category structure, including associated images.

```bash
# Translate all articles in a directory to Simplified Chinese
export ANTHROPIC_API_KEY="your-api-key"
geoagent transform /path/to/articles --lang zh-CN --output-dir /path/to/output -r -c 4
```

### Example: Batch Articles Translation

```bash
# Translate articles and preserve directory structure
ANTHROPIC_API_KEY="sk-xxx" geoagent transform /path/to/articles \
  --lang zh-CN \
  --output-dir /path/to/output \
  -r -c 4

# After translation, classify images by matching to article categories
python3 << 'EOF'
import os
import shutil
from pathlib import Path

images_dir = Path("images")
output_dir = Path("output")
articles_dir = Path("articles")

# Build mapping from filename (without extension) to relative path in articles
filename_to_relpath = {}
for md_file in articles_dir.rglob("*.md"):
    stem = md_file.stem
    rel_path = md_file.relative_to(articles_dir)
    filename_to_relpath[stem] = rel_path

# Process each image folder
image_folders = [d for d in images_dir.iterdir() if d.is_dir() and d.name != '.DS_Store']
for img_folder in image_folders:
    stem = img_folder.name
    if stem in filename_to_relpath:
        rel_path = filename_to_relpath[stem]
        dest_folder = output_dir / rel_path.parent / stem
        dest_folder.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(img_folder, dest_folder)
EOF
```

### Expected Output Structure

```
output/
├── AI/
│   └── 2026/
│       └── 05/
│           ├── article-title.zh-CN.geo.md      # Translated article
│           └── article-title/                  # Image folder
│               ├── image1.png
│               └── image2.png
├── Activism/
│   └── 2026/
│       └── 05/
│           ├── article-title.zh-CN.geo.md
│           └── article-title/
...
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
├── geo/
│   ├── rules.py       # GEO rules definitions
│   └── optimizer.py   # GEO optimization logic
├── db/
│   ├── connection.py  # SQLite connection manager
│   └── schema.py      # Database schema (22 tables)
├── prompts/
│   └── registry.py    # Prompt template registry
├── knowledge/
│   ├── base.py        # KnowledgeBase + TextChunker (900 char)
│   ├── embedder.py   # Fallback vectors + embedding API
│   └── retriever.py  # Hybrid search (75% vector + 25% lexical)
├── articles/
│   ├── models.py      # Article/Author/Category dataclasses
│   └── generator.py  # Full GEOFlow pipeline
├── keywords/
│   └── extractor.py  # Keyword extraction
├── url_import/
│   └── job.py         # URL import pipeline
├── tasks/
│   └── scheduler.py   # TaskScheduler + TaskRunner + Worker loop
├── titles/
│   └── generator.py   # AI title generation (5 styles)
├── images/
│   ├── library.py     # ImageLibrary + Image dataclasses
│   └── inserter.py   # Paragraph interval image insertion
└── admin/
    └── settings.py   # SiteSettings key-value store
```
