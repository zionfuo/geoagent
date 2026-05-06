import pytest

def test_model_client_base_has_complete_method():
    from geoagent.models.client import ModelClient
    assert hasattr(ModelClient, 'complete')

def test_minimax_client_complete():
    from geoagent.models.client import MiniMaxClient
    client = MiniMaxClient(api_key="test", base_url="http://test")
    assert hasattr(client, 'complete')

def test_claude_client_complete():
    from geoagent.models.client import ClaudeClient
    client = ClaudeClient(api_key="test")
    assert hasattr(client, 'complete')

def test_openai_client_complete():
    from geoagent.models.client import OpenAIClient
    client = OpenAIClient(api_key="test")
    assert hasattr(client, 'complete')