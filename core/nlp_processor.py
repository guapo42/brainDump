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
- Write a 1-2 sentence summary of the overall communication.

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
