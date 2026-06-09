"""Config is provider-neutral and env-overridable (no hardcoded LLM backend)."""

import pytest

from brain_dump.config import LLMSettings, load_settings

pytestmark = pytest.mark.unit


def test_defaults_are_provider_neutral() -> None:
    s = LLMSettings()
    # The default provider label must not lock us to a specific backend.
    assert s.provider == "openai_compatible"
    assert s.model == "local-model"


def test_env_overrides_select_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    # Switching to llama.cpp must be a config change only.
    monkeypatch.setenv("LLM_PROVIDER", "llamacpp")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:8080/v1")
    monkeypatch.setenv("LLM_MODEL", "qwen2.5-coder-7b-instruct")
    s = load_settings().llm
    assert s.provider == "llamacpp"
    assert s.base_url == "http://localhost:8080/v1"
    assert s.model == "qwen2.5-coder-7b-instruct"
