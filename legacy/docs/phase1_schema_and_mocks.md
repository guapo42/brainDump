# Phase 1: Core Schema & TDD Infrastructure

## Objective
Establish the foundational data structures (Ontology) using Pydantic and set up the `pytest` testing infrastructure with mock data. No database connections or LLM calls should be made in this phase.

## Specifications
1. **Dependencies:** Ensure `pytest`, `pytest-asyncio`, and `pydantic` are in the project requirements.
2. **Schema Definition (`models/schemas.py`):**
   - Create a `SourceMetadata` Pydantic model (fields: `source_id`, `platform`, `sender`, `timestamp`).
   - Create a `TaskEntity` model (fields: `description`, `status` defaulting to "pending", `due_date`, `assignee`, `priority`).
   - Create an `ExtractionResult` model (fields: `projects` (List[str]), `people` (List[str]), `tasks` (List[TaskEntity]), `summary`).
3. **Mock Data Generator (`tests/conftest.py`):**
   - Create a pytest fixture that returns a dummy raw text string representing an email. 
   - Example text to embed in the fixture: *"Hey team, for Operation Dormant Seed, I need Sarah to finalize the database migration by next Friday. I'm currently blocked waiting on the AWS credentials from John."*

## Prompt for Claude Code
"Read `docs/phase1_schema_and_mocks.md`. Initialize the project structure, write the Pydantic models in `models/schemas.py`, and create the pytest fixtures in `tests/conftest.py`. Write a basic test in `tests/test_schemas.py` to ensure the Pydantic models validate correctly. Run the tests to confirm."