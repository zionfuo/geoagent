# tests/test_config.py
import os
import tempfile
import yaml

def test_load_config_from_file():
    from geoagent.config import Config

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'default_model': 'minimax/MiniMax-M2.7',
            'models': {'minimax': {'api_key_env': 'TEST_KEY'}},
            'pipeline': {
                'max_tokens_translate': 4096,
                'max_tokens_geo': 4096,
                'max_tokens_understand': 1024,
                'max_retries': 5
            }
        }, f)
        f.flush()

        config = Config.from_file(f.name)
        assert config.default_model == 'minimax/MiniMax-M2.7'
        assert config.max_tokens_translate == 4096
        assert config.max_tokens_geo == 4096
        assert config.max_tokens_understand == 1024
        assert config.max_retries == 5

    os.unlink(f.name)

def test_config_get_model_client():
    from geoagent.config import Config

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'default_model': 'minimax/MiniMax-M2.7',
            'models': {
                'minimax': {
                    'api_key_env': 'ANTHROPIC_API_KEY',
                    'base_url': 'https://api.minimaxi.com/anthropic',
                    'default_model': 'MiniMax-M2.7'
                }
            }
        }, f)
        f.flush()

        config = Config.from_file(f.name)
        client = config.get_model_client('minimax', 'test-key')
        assert client is not None

    os.unlink(f.name)


def test_config_default():
    from geoagent.config import Config

    config = Config.default()
    assert config.default_model == 'minimax/MiniMax-M2.7'
    assert 'minimax' in config.models
    assert config.max_retries == 3
    assert config.retry_base_delay == 1.0