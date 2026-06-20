"""Tests for configuration loading."""

from src.config import Config, get_config, _default_config_path


def test_default_config_path_exists():
    assert _default_config_path() is not None


def test_config_loads_yaml_model_settings():
    config = Config(_default_config_path())
    assert config.get("model.embedding_dim") == 128
    assert config.get("model.hidden_dim") == 256
    assert config.get("model.num_layers") == 2


def test_get_config_singleton():
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2
