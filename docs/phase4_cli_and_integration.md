# Phase 4: Integration Loop & CLI (User Testing Milestone)

## Objective
Tie the pipeline together into a functional CLI tool that reads from a local `.txt` file, processes it, and allows the user to query the system.

## Specifications
1. **Integration Logic (`core/orchestrator.py`):**
   - Create a `process_local_file(filepath: str)` function.
   - It should read the text file, pass it to `Extractor.extract_entities()`, then pass the result to `GraphStore.upsert_extraction()` and `VectorStore.upsert_document()`.
2. **CLI Interface (`main.py`):**
   - Use the built-in `argparse` library (or `rich` if preferred for better terminal output).
   - Implement two commands:
     - `python main.py ingest --file mock_email.txt`: Triggers the integration logic.
     - `python main.py query --question "Who is waiting for what?"`: Triggers a hardcoded Cypher query to the Graph Engine to print blocked tasks, and fetches related raw text from the Vector Engine.
3. **User Testing Prep:**
   - Ensure the code allows for easy swapping from mocked DBs to the real local Docker instances we defined earlier.

## Prompt for Claude Code
"Read `docs/phase4_cli_and_integration.md`. Build the orchestrator to tie everything together and create a simple CLI in `main.py` using `argparse`. Ensure I can run 'ingest' on a local text file and 'query' to see results. Print clear instructions on how I can run this CLI manually to test the pipeline."