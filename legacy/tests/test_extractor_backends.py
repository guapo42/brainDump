"""Tests for multi-LLM backend support (mocked — no real LLM calls)."""

import importlib
from unittest.mock import MagicMock, patch

import pytest

from core.nlp_processor import Extractor, create_extractor_from_env

has_anthropic = importlib.util.find_spec("anthropic") is not None


class TestOllamaBackend:
    def test_creates_openai_client(self):
        with patch("core.nlp_processor.OpenAI") as mock_openai:
            with patch("core.nlp_processor.instructor") as mock_instructor:
                mock_instructor.from_openai.return_value = MagicMock()
                ext = Extractor(backend="ollama", base_url="http://test:11434/v1")

        mock_openai.assert_called_once_with(base_url="http://test:11434/v1", api_key="ollama")
        assert ext.backend == "ollama"
        assert ext.model == "qwen2.5-coder:30b"


class TestAzureBackend:
    @patch("core.nlp_processor.instructor")
    def test_creates_azure_client(self, mock_instructor):
        mock_instructor.from_openai.return_value = MagicMock()
        with patch("openai.AzureOpenAI") as mock_azure:
            ext = Extractor(
                backend="azure",
                endpoint="https://test.openai.azure.com/",
                api_key="test-key",
                deployment="gpt-4",
            )

        assert ext.backend == "azure"
        assert ext.model == "gpt-4"


@pytest.mark.skipif(not has_anthropic, reason="anthropic package not installed")
class TestBedrockBackend:
    @patch("core.nlp_processor.instructor")
    def test_creates_bedrock_client(self, mock_instructor):
        mock_instructor.from_anthropic.return_value = MagicMock()
        with patch("anthropic.AnthropicBedrock") as mock_bedrock:
            ext = Extractor(
                backend="bedrock",
                region="us-west-2",
                model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            )

        assert ext.backend == "bedrock"
        assert ext.model == "anthropic.claude-3-5-sonnet-20241022-v2:0"

    @patch("core.nlp_processor.instructor")
    def test_bedrock_adds_max_tokens(self, mock_instructor):
        mock_client = MagicMock()
        mock_instructor.from_anthropic.return_value = mock_client
        with patch("anthropic.AnthropicBedrock"):
            ext = Extractor(backend="bedrock", region="us-east-1")

        mock_create = MagicMock(return_value=MagicMock())
        ext.client.chat.completions.create = mock_create

        ext.extract_entities("test text")

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 4096


class TestInvalidBackend:
    def test_raises_on_unknown(self):
        try:
            Extractor(backend="openrouter")
            assert False, "Should have raised"
        except ValueError as e:
            assert "openrouter" in str(e)


class TestFactoryFromEnv:
    @patch.dict("os.environ", {"LLM_BACKEND": "ollama", "OLLAMA_BASE_URL": "http://test:11434/v1"})
    @patch("core.nlp_processor.OpenAI")
    @patch("core.nlp_processor.instructor")
    def test_ollama_from_env(self, mock_instructor, mock_openai):
        mock_instructor.from_openai.return_value = MagicMock()
        ext = create_extractor_from_env()
        assert ext.backend == "ollama"

    @patch.dict("os.environ", {
        "LLM_BACKEND": "azure",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "key",
        "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
    })
    @patch("core.nlp_processor.instructor")
    def test_azure_from_env(self, mock_instructor):
        mock_instructor.from_openai.return_value = MagicMock()
        with patch("openai.AzureOpenAI"):
            ext = create_extractor_from_env()
        assert ext.backend == "azure"
