# tests/test_geo_optimizer.py
import pytest

def test_georules_from_file():
    from geoagent.geo.rules import GEORules

    rules = GEORules.from_rubric_file("shared/rubrics/content-quality-rubric.md")
    assert len(rules.dimensions) == 6
    assert "source_quality" in rules.dimensions
    assert "anti_hallucination" in rules.dimensions

def test_geo_optimizer_initialization():
    from geoagent.geo.optimizer import GEOOptimizer
    from geoagent.geo.rules import GEORules

    rules = GEORules.from_rubric_file("shared/rubrics/content-quality-rubric.md")
    optimizer = GEOOptimizer(rules)
    assert optimizer.rules is not None