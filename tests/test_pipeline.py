# tests/test_pipeline.py
import pytest
import tempfile
import os

def test_pipeline_initialization():
    from geoagent.pipeline import Pipeline
    from geoagent.models.client import MiniMaxClient
    from geoagent.geo.rules import GEORules

    client = MiniMaxClient(api_key="test")
    rules = GEORules.from_rubric_file("shared/rubrics/content-quality-rubric.md")
    pipeline = Pipeline(client, client, rules, "MiniMax-M2.7")
    assert pipeline.client is not None


def test_pipeline_read_input():
    from geoagent.pipeline import Pipeline
    from geoagent.models.client import MiniMaxClient
    from geoagent.geo.rules import GEORules

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Test\n\nTest content")
        f.flush()
        temp_path = f.name

    try:
        client = MiniMaxClient(api_key="test")
        rules = GEORules.from_rubric_file("shared/rubrics/content-quality-rubric.md")
        pipeline = Pipeline(client, client, rules, "MiniMax-M2.7")

        doc = pipeline.read_input(temp_path)
        assert doc.title == "Test"
        assert "Test content" in doc.content
    finally:
        os.unlink(temp_path)