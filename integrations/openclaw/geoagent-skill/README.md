# Geoagent Skill for OpenClaw

This skill enables OpenClaw to transform markdown articles using the geoagent CLI tool.

## Installation

1. Copy this folder to your OpenClaw workspace skills directory:
   ```bash
   cp -r geoagent-skill ~/.openclaw/workspace/skills/geoagent
   ```

2. Install geoagent if not already installed:
   ```bash
   pip install geoagent
   ```

3. Set your API key:
   ```bash
   export ANTHROPIC_API_KEY="your-key-here"
   ```

4. Optionally copy the config example:
   ```bash
   cp config.json.example ~/.openclaw/openclaw.json
   # Then edit to add your API key
   ```

## Usage

After installation, you can invoke geoagent directly:

```
/geoagent transform /path/to/article.md --lang zh-TW
/geoagent transform ./articles/ --lang en,ja -c 8 --recursive
```

Or describe what you want in natural language and OpenClaw will route to the geoagent tool.