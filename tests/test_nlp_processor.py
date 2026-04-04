"""Tests for the NLP extraction pipeline (mocked — no Ollama required)."""

from unittest.mock import MagicMock, patch

from core.nlp_processor import Extractor
from models.schemas import ExtractionResult


class TestExtractor:
    def test_extract_entities_returns_pydantic_model(
        self, sample_email_text, sample_extraction_result
    ):
        """Verify extract_entities returns an ExtractionResult without hitting Ollama."""
        extractor = Extractor()

        # Mock the instructor-patched client's create method
        mock_create = MagicMock(return_value=sample_extraction_result)
        extractor.client.chat.completions.create = mock_create

        result = extractor.extract_entities(sample_email_text)

        assert isinstance(result, ExtractionResult)
        assert len(result.people) == 3
        assert len(result.tasks) == 3
        assert result.projects[0].name == "Operation Dormant Seed"

        # Verify the LLM was called with the right model and response_model
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs["model"] == "qwen2.5-coder:30b"
        assert call_kwargs.kwargs["response_model"] is ExtractionResult

    def test_extract_entities_prompt_includes_text(
        self, sample_email_text, sample_extraction_result
    ):
        """Verify the user's text is included in the prompt sent to the LLM."""
        extractor = Extractor()
        mock_create = MagicMock(return_value=sample_extraction_result)
        extractor.client.chat.completions.create = mock_create

        extractor.extract_entities(sample_email_text)

        messages = mock_create.call_args.kwargs["messages"]
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "Operation Dormant Seed" in user_msg["content"]
        assert "AWS credentials" in user_msg["content"]
