"""
Tool schemas for geoagent tools.
Defines how the LLM sees and calls geoagent transformation tools.
"""

GEOAGENT_TRANSFORM_SCHEMA = {
    "name": "geoagent_transform",
    "description": "Transform a markdown article or directory of articles into GEO-optimized versions. Supports multi-language translation including zh-TW (Traditional Chinese), en, ko, ja, fr, de, es, ar and more.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_path": {
                "type": "string",
                "description": "Path to the markdown file or directory to transform. Can be a single article or batch directory."
            },
            "lang": {
                "type": "string",
                "description": "Target languages (comma-separated). Examples: 'zh-TW', 'en,ko', 'zh-TW,en,ja'. Default: 'zh-TW'",
                "default": "zh-TW"
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory for transformed files. If not specified, creates 'output' subdirectory in input path."
            },
            "verbose": {
                "type": "boolean",
                "description": "Show detailed logs during transformation.",
                "default": False
            },
            "resume": {
                "type": "boolean",
                "description": "Resume interrupted job - skip completed language outputs.",
                "default": False
            }
        },
        "required": ["input_path"]
    }
}

GEOAGENT_BATCH_SCHEMA = {
    "name": "geoagent_batch",
    "description": "Batch transform multiple markdown articles using concurrent processing. Good for large document sets.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_dir": {
                "type": "string",
                "description": "Directory containing markdown files to transform."
            },
            "lang": {
                "type": "string",
                "description": "Target languages (comma-separated).",
                "default": "zh-TW"
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory for transformed files."
            },
            "concurrency": {
                "type": "integer",
                "description": "Number of concurrent threads (default: 4, max: 16)",
                "default": 4
            },
            "recursive": {
                "type": "boolean",
                "description": "Process directories recursively.",
                "default": False
            }
        },
        "required": ["input_dir"]
    }
}