"""
Tool execution logic for geoagent.
Handles shell command execution and result parsing.
"""

import json
import subprocess
from pathlib import Path


def _run_geoagent(cmd: list, timeout: int = 300) -> dict:
    """Run geoagent command and return parsed result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent.parent
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout}s"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def geoagent_transform_tool(input_path: str, lang: str = "zh-TW", output_dir: str = None,
                           verbose: bool = False, resume: bool = False, **kwargs) -> str:
    """
    Transform a markdown article or directory.

    Args:
        input_path: Path to markdown file or directory
        lang: Target languages (comma-separated)
        output_dir: Output directory
        verbose: Show detailed logs
        resume: Resume interrupted job
    """
    cmd = ["geoagent", "transform", input_path, "--lang", lang]

    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    if verbose:
        cmd.append("--verbose")
    if resume:
        cmd.append("--resume")

    result = _run_geoagent(cmd)

    if result["success"]:
        return json.dumps({
            "status": "success",
            "message": "Transformation completed",
            "output": result["stdout"]
        })
    else:
        return json.dumps({
            "status": "error",
            "error": result.get("stderr", result.get("error", "Unknown error")),
            "returncode": result.get("returncode", -1)
        })


def geoagent_batch_tool(input_dir: str, lang: str = "zh-TW", output_dir: str = None,
                        concurrency: int = 4, recursive: bool = False, **kwargs) -> str:
    """
    Batch transform multiple markdown articles.

    Args:
        input_dir: Directory containing markdown files
        lang: Target languages
        output_dir: Output directory
        concurrency: Number of concurrent threads
        recursive: Process recursively
    """
    cmd = ["geoagent", "transform", input_dir, "--lang", lang, "-c", str(concurrency)]

    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    if recursive:
        cmd.append("--recursive")

    result = _run_geoagent(cmd, timeout=600)

    if result["success"]:
        return json.dumps({
            "status": "success",
            "message": "Batch transformation completed",
            "output": result["stdout"]
        })
    else:
        return json.dumps({
            "status": "error",
            "error": result.get("stderr", result.get("error", "Unknown error")),
            "returncode": result.get("returncode", -1)
        })