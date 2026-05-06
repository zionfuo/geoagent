# tests/test_translator.py
import pytest

def test_translator_initialization():
    from geoagent.translator.translator import Translator
    from geoagent.models.client import MiniMaxClient

    client = MiniMaxClient(api_key="test")
    translator = Translator(client, default_model="MiniMax-M2.7")
    assert translator.client is not None

def test_translator_language_codes():
    from geoagent.translator.translator import Translator
    from geoagent.models.client import MiniMaxClient

    client = MiniMaxClient(api_key="test")
    translator = Translator(client, default_model="MiniMax-M2.7")

    assert translator.get_language_display("en") == "English"
    assert translator.get_language_display("zh-TW") == "Traditional Chinese (Taiwan)"
    assert translator.get_language_display("ko") == "Korean"
    assert translator.get_language_display("fr") == "French"