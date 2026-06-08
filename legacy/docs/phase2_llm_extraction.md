# Phase 2: LLM Extraction Pipeline (Ollama + Instructor)

## Objective
Build the NLP processor that takes raw text and strictly outputs our `ExtractionResult` Pydantic model using Qwen2.5-Coder via Ollama.

## Specifications
1. **Dependencies:** Add `openai` and `instructor` to the project.
2. **NLP Processor (`core/nlp_processor.py`):**
   - Implement an `Extractor` class.
   - In the `__init__`, configure the OpenAI client to point to the local Ollama instance (default port 11434, base_url="http://localhost:11434/v1", api_key="ollama").
   - Patch the client using `instructor.from_openai()`.
   - Write an async method `extract_entities(text: str) -> ExtractionResult` that prompts the LLM to extract project management data and enforces the Pydantic response model.
3. **Testing (`tests/test_nlp_processor.py`):**
   - Use `unittest.mock.patch` to mock the `instructor` patched client's `create` method.
   - Do NOT hit the actual Ollama endpoint during the automated test. The mock should simply return a pre-defined `ExtractionResult` object when called.
   - Assert that `extract_entities` returns the expected Pydantic object.

## Prompt for Claude Code
"Read `docs/phase2_llm_extraction.md`. Implement the `nlp_processor.py` using `instructor` and Ollama. Write the corresponding mocked tests in `test_nlp_processor.py`. Run the tests and fix any issues until they pass."
