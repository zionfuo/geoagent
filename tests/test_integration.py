# tests/test_integration.py
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

def test_pipeline_with_sample_file():
    """Integration test with sample markdown file."""
    from geoagent.pipeline import Pipeline
    from geoagent.models.client import MiniMaxClient
    from geoagent.geo.rules import GEORules

    sample_path = "examples/input/sample.md"
    if not os.path.exists(sample_path):
        pytest.skip("Sample file not found")

    client = MiniMaxClient(api_key="test")

    # Mock the complete method to avoid actual API calls
    mock_response = "Mocked response for structured content extraction with sufficient length to pass validation"
    client.complete = MagicMock(return_value=mock_response)

    rules = GEORules.from_rubric_file("shared/rubrics/content-quality-rubric.md")
    pipeline = Pipeline(client, client, rules, "MiniMax-M2.7")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_files = pipeline.transform(sample_path, tmpdir, ["en"])

        assert len(output_files) == 1
        assert any("en.geo.md" in f for f in output_files)

        for f in output_files:
            content = Path(f).read_text()
            assert len(content) > 100
            assert "---" in content
            assert "<!-- Thinking:" not in content