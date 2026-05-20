---
name: geoagent
description: Transform Chinese markdown articles into GEO-optimized multi-language versions. Use this to translate articles to Traditional Chinese (zh-TW), English, Korean, Japanese, and other languages with SEO optimization.
user-invocable: true
command-dispatch: "tool"
command-tool: "shell"
command-arg-mode: "raw"
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["geoagent"] },
        "install": [
          { "id": "pip", "kind": "uv", "formula": "geoagent", "bins": ["geoagent"], "label": "Install geoagent (pip)" }
        ],
      },
  }
---

# Geoagent - Article Translation & GEO Optimization

Geoagent transforms markdown articles into GEO-optimized (Generative Engine Optimization) versions with multi-language translation support.

## Usage

### Transform a single article
```
geoagent transform /path/to/article.md --lang zh-TW
```

### Batch transform a directory
```
geoagent transform /path/to/articles/ --lang en,ko,fr -c 4 --recursive
```

### Common language codes:
- `zh-TW` - Traditional Chinese (Taiwan style)
- `zh-HK` - Traditional Chinese (Hong Kong style)
- `en` - English
- `ja` - Japanese
- `ko` - Korean
- `fr` - French
- `de` - German
- `es` - Spanish
- `ar` - Arabic

## Options

| Option | Description |
|--------|-------------|
| `--lang` | Target languages (comma-separated) |
| `--output-dir` | Output directory |
| `-c N` | Concurrent threads (default: 4) |
| `-r` | Process recursively |
| `--resume` | Skip completed files |
| `--verbose` | Show detailed logs |

## Environment Variables

- `ANTHROPIC_API_KEY` - Required for API access
- Config file: `~/.geoagent/config.yaml`

## Examples

### Translate to Taiwanese Chinese
```
geoagent transform article.md --lang zh-TW
```

### Multi-language batch
```
geoagent transform ./news/ --lang en,ja,ko -c 8 --recursive
```

### Resume interrupted job
```
geoagent transform ./articles/ --lang zh-TW --resume
```