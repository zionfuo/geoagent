# Geoagent Plugin for Hermes Agent

Enables Hermes Agent to transform markdown articles with geoagent capabilities.

## Installation

1. Copy plugin to your Hermes plugins directory:
   ```bash
   cp -r geoagent_plugin ~/.hermes/plugins/geoagent
   ```

2. Ensure geoagent is installed:
   ```bash
   pip install geoagent
   ```

3. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   ```

4. Enable the plugin in your hermes config, then restart Hermes Agent.

## Available Tools

### geoagent_transform
Transform a single article or directory to GEO-optimized versions.

```python
geoagent_transform(
    input_path="/path/to/article.md",
    lang="zh-TW",           # Target language(s)
    output_dir=None,         # Optional output directory
    verbose=False,           # Show detailed logs
    resume=False             # Skip completed
)
```

### geoagent_batch
Batch transform with concurrent processing.

```python
geoagent_batch(
    input_dir="/path/to/articles/",
    lang="en,ko,ja",        # Multi-language
    output_dir=None,
    concurrency=4,           # Thread count
    recursive=False
)
```

## Example Usage

In Hermes Agent conversation:

```
Transform /Users/me/articles/ to Traditional Chinese (Taiwan style)
```

```
Batch translate ./news/ to English, Japanese, and Korean with 8 threads
```

```
Resume the interrupted translation job in /data/articles/
```