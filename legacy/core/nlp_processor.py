"""NLP Extraction Pipeline — supports Ollama, Azure OpenAI, and AWS Bedrock Claude."""

import os

import instructor
from openai import OpenAI

from models.schemas import ExtractionResult


EXTRACTION_PROMPT = """\
You are an expert project management assistant. Analyze the following communication \
and extract ALL structured entities.

Rules:
- Extract every person mentioned by name.
- Extract every project, initiative, or operation by name.
- Extract every task, action item, or deliverable as a separate TaskEntity.
- For each task, identify who is assigned (assignee) and who it is waiting on (waiting_on).
- Extract deadlines as ISO date strings (YYYY-MM-DD) when mentioned.
- Infer priority from urgency cues (e.g. "URGENT", "critical", "high priority").
- Estimate time needed for each task in minutes when possible.
- Write a 1-2 sentence summary of the overall communication.

Tone Analysis — read HOW the sender is communicating:
- urgency_language: 0.0 for "when you get a chance", 1.0 for "URGENT/ACTION REQUIRED"
- escalation_signals: true if the message mentions VP, HR, client, compliance, or consequences
- emotional_temperature: "neutral", "warm", "frustrated", "panicked", or "passive_aggressive"
- is_follow_up: true if this references a previous unanswered request
- references_deliverable: true if this task connects to a milestone, client deadline, or go-live
- peer_progress_mentioned: true if other team members are described as having completed work \
  or making progress on the same project (social proof that you should also be contributing)

Communication:
{text}
"""

SYSTEM_PROMPT = "You extract structured project management data from communications."


def _create_ollama_client(base_url: str, api_key: str, model: str):
    """Create instructor-patched client for local Ollama.

    Uses JSON mode rather than tool-calling: tool-call support varies
    widely across Ollama models (gemma3 has none; qwen2.5-coder<30b emits
    JSON as content; qwen3-coder stringifies nested arguments). JSON mode
    works uniformly with any model that can follow a "respond in JSON"
    instruction.
    """
    raw = OpenAI(base_url=base_url, api_key=api_key)
    return instructor.from_openai(raw, mode=instructor.Mode.JSON), model


def _create_azure_client(endpoint: str, api_key: str, api_version: str, deployment: str):
    """Create instructor-patched client for Azure OpenAI."""
    from openai import AzureOpenAI
    raw = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )
    return instructor.from_openai(raw), deployment


def _create_bedrock_client(region: str, model_id: str):
    """Create instructor-patched client for AWS Bedrock Claude."""
    from anthropic import AnthropicBedrock
    raw = AnthropicBedrock(aws_region=region)
    return instructor.from_anthropic(raw), model_id


class Extractor:
    """Extracts structured entities from raw communication text using an LLM.

    Supports three approved backends:
    - ollama: Local Qwen2.5-Coder via Ollama (default)
    - azure: Azure OpenAI GPT-4
    - bedrock: AWS Bedrock Claude
    """

    def __init__(self, backend: str = "ollama", **kwargs):
        self.backend = backend

        if backend == "ollama":
            self.client, self.model = _create_ollama_client(
                base_url=kwargs.get("base_url", "http://localhost:11434/v1"),
                api_key=kwargs.get("api_key", "ollama"),
                model=kwargs.get("model", "qwen2.5-coder:30b"),
            )
        elif backend == "azure":
            self.client, self.model = _create_azure_client(
                endpoint=kwargs["endpoint"],
                api_key=kwargs["api_key"],
                api_version=kwargs.get("api_version", "2024-02-01"),
                deployment=kwargs["deployment"],
            )
        elif backend == "bedrock":
            self.client, self.model = _create_bedrock_client(
                region=kwargs.get("region", "us-east-1"),
                model_id=kwargs.get("model_id", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
            )
        else:
            raise ValueError(f"Unknown LLM backend: {backend}. Use: ollama, azure, bedrock")

    def extract_entities(self, text: str) -> ExtractionResult:
        """Extract people, projects, tasks, and relationships from text."""
        create_kwargs = {
            "model": self.model,
            "response_model": ExtractionResult,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": EXTRACTION_PROMPT.format(text=text)},
            ],
        }
        # Bedrock Claude requires max_tokens
        if self.backend == "bedrock":
            create_kwargs["max_tokens"] = 4096

        return self.client.chat.completions.create(**create_kwargs)


def create_extractor_from_env() -> Extractor:
    """Factory that reads LLM_BACKEND and related env vars."""
    backend = os.getenv("LLM_BACKEND", "ollama")

    if backend == "ollama":
        return Extractor(
            backend="ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            model=os.getenv("LLM_MODEL", "qwen2.5-coder:30b"),
        )
    elif backend == "azure":
        return Extractor(
            backend="azure",
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
        )
    elif backend == "bedrock":
        return Extractor(
            backend="bedrock",
            region=os.getenv("AWS_REGION", "us-east-1"),
            model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
        )
    else:
        raise ValueError(f"Unknown LLM_BACKEND: {backend}")
