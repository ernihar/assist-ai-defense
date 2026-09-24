"""
Smoke test: verifies the project scaffolding loads correctly.

This is the test CI runs first to confirm the environment is wired
correctly before any guardrail logic is added.
"""
from app.config.settings import Settings, settings


def test_settings_singleton_loads():
    assert settings is not None
    assert isinstance(settings, Settings)


def test_default_ollama_model_is_llama3_2():
    assert settings.ollama_model == "llama3.2"


def test_default_ollama_base_url():
    assert settings.ollama_base_url.startswith("http")


def test_max_input_length_is_positive_int():
    assert isinstance(settings.max_input_length, int)
    assert settings.max_input_length > 0


def test_injection_confidence_threshold_in_valid_range():
    assert 0.0 <= settings.injection_confidence_threshold <= 1.0


def test_app_env_has_default():
    assert settings.app_env in {"development", "production", "test"}
