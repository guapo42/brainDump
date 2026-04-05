"""NLP Extraction Pipeline using Qwen2.5-Coder via Ollama + Instructor."""

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


class Extractor:
    """Extracts structured entities from raw communication text using an LLM."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        model: str = "qwen2.5-coder:30b",
    ):
        self.model = model
        self._raw_client = OpenAI(base_url=base_url, api_key=api_key)
        self.client = instructor.from_openai(self._raw_client)

    def extract_entities(self, text: str) -> ExtractionResult:
        """Extract people, projects, tasks, and relationships from text."""
        return self.client.chat.completions.create(
            model=self.model,
            response_model=ExtractionResult,
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured project management data from communications.",
                },
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(text=text),
                },
            ],
        )
