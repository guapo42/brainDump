"""Runtime configuration.

The LLM is intentionally **provider-neutral**: any OpenAI-compatible local server
works (Ollama, llama.cpp's ``llama-server``, vLLM, …). The provider is chosen by
configuration — ``LLM_BASE_URL`` + ``LLM_MODEL`` — never hardcoded. Do not couple
code to a specific backend; the choice between Ollama and llama.cpp is still open
(see docs/decisions/0005-llm-provider-deferred.md).
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """Connection settings for an OpenAI-compatible chat-completions endpoint."""

    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")

    # A label for diagnostics/logs only; it must not drive code paths.
    # Examples: "ollama", "llamacpp", "vllm", "openai_compatible".
    provider: str = "openai_compatible"

    # OpenAI-compatible base URL. Defaults to a common local port; override per
    # provider, e.g. llama.cpp -> http://localhost:8080/v1.
    base_url: str = "http://localhost:11434/v1"

    # Provider-specific model identifier (Ollama tag, llama.cpp alias, …).
    model: str = "local-model"

    # Most local servers ignore the key but the OpenAI client requires a value.
    api_key: str = "not-needed"

    timeout_s: float = 30.0
    max_retries: int = 2


class Settings(BaseSettings):
    """Top-level service settings."""

    model_config = SettingsConfigDict(extra="ignore")

    llm: LLMSettings = Field(default_factory=LLMSettings)


def load_settings() -> Settings:
    """Build settings from the environment."""
    return Settings()
