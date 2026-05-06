import pytest
from datetime import datetime

def test_markdown_document_creation():
    from geoagent.models.document import MarkdownDocument

    doc = MarkdownDocument(
        title="Test",
        content="# Test\n\nContent",
        frontmatter={"source": "test.md"}
    )
    assert doc.title == "Test"
    assert "Test" in doc.content

def test_markdown_document_to_string():
    from geoagent.models.document import MarkdownDocument

    doc = MarkdownDocument(
        title="Test",
        content="# Test\n\nContent",
        frontmatter={"source": "test.md", "lang": "zh"}
    )
    output = str(doc)
    assert "source: test.md" in output
    assert "lang: zh" in output
    assert "# Test" in output

def test_doc_context():
    from geoagent.models.document import DocContext

    ctx = DocContext(
        title="Test Article",
        themes=["AI", "Technology"],
        terminology={"LLM": "Large Language Model"},
        structure={"sections": ["intro", "body", "conclusion"]}
    )
    assert "AI" in ctx.themes
    assert ctx.terminology["LLM"] == "Large Language Model"