# Brain Dump

A "Second Brain" ingestion engine that turns fragmented communications (email, Slack, Teams) into a structured knowledge graph. Extracts people, projects, tasks, deadlines, dependencies, and tone from raw text using a local LLM, stores them in Neo4j (graph) and ChromaDB (vector), and surfaces what matters through natural language queries.

Includes an ADHD cognitive simulation that models realistic executive dysfunction, hyperfocus, and task-selection behavior over a 12-month office scenario.

## Prerequisites

- **Python 3.11 or 3.12** (3.14 works but requires chromadb >= 1.5)
- **Docker Desktop** (for Neo4j and ChromaDB)
- **Ollama** (for local LLM extraction) — https://ollama.com

## Quick Start

### 1. Clone and install

```bash
git clone <repo-url> brain-dump
cd brain-dump
pip install -r requirements.txt
```

### 2. Pull an Ollama model

Any model that supports structured JSON output works. Tested models:

```bash
# Recommended — good accuracy, runs on 16GB RAM
ollama pull qwen2.5-coder:7b

# Higher accuracy, needs 32GB+ RAM
ollama pull qwen2.5-coder:14b
ollama pull qwen3-coder:30b
```

### 3. Start Docker services

```bash
docker-compose up -d
```

This starts:
- **Neo4j** on `localhost:7474` (browser) / `localhost:7687` (bolt)
- **ChromaDB** on `localhost:8000`

Wait ~15 seconds for Neo4j to initialize on first run.

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` to set your model name (must match what you pulled in step 2):

```
LLM_BACKEND=ollama
LLM_MODEL=qwen2.5-coder:7b
```

If you changed the Neo4j password in `docker-compose.yml`, update `NEO4J_PASSWORD` to match.

### 5. Ingest and query

```bash
# Ingest a text file (email, Slack export, etc.)
python main.py ingest -f tests/email_1.txt

# Query — natural language routing
python main.py query -q "project overview"
python main.py query -q "overdue"
python main.py query -q "what's blocked"
python main.py query -q "relationship health"
python main.py query -q "EPA pipeline"           # semantic search fallback

# ADHD nudge — one task, timeboxed
python main.py nudge --timebox 15
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `ingest -f <file>` | Extract entities from a text file and store in graph + vector DB |
| `query -q <question>` | Natural language query with smart routing (see below) |
| `nudge --timebox <min>` | Pick the most urgent forgotten task, make it approachable |
| `fetch-outlook --since <date>` | Pull emails from Office 365 (requires Azure AD setup) |
| `fetch-slack --channel <id>` | Pull messages from Slack (requires bot token) |

### Query routing

The query engine pattern-matches your question to the right data source:

| Phrase | Query type |
|--------|-----------|
| "my tasks", "assigned to me" | Tasks assigned to you |
| "due this week", "due today" | Deadline filtering |
| "overdue" | Past-due tasks |
| "frustrated", "annoyed" | Stakeholder frustration heatmap |
| "forgetting" | Tasks you're neglecting (high frustration, not started) |
| "blocked", "hanging", "waiting" | Tasks waiting on others + RAG context |
| "relationship health" | Person-by-person task health scores |
| "project overview" | All projects with task status |
| "unanswered threads" | Threads where you haven't replied |
| anything else | Semantic search via ChromaDB |

## Architecture

```
raw text ──> Extractor (Ollama/Azure/Bedrock)
                │
                ├──> Neo4j (entities, relationships, provenance)
                │       Person, Project, Task, Source nodes
                │       ASSIGNED_TO, WAITING_ON, PART_OF, REQUESTED_BY edges
                │
                └──> ChromaDB (raw text for semantic RAG search)
```

### LLM Backends

| Backend | Config | Notes |
|---------|--------|-------|
| **Ollama** (default) | `LLM_BACKEND=ollama` | Free, local, uses JSON mode for broad model compatibility |
| **Azure OpenAI** | `LLM_BACKEND=azure` | GPT-4, requires Azure subscription |
| **AWS Bedrock** | `LLM_BACKEND=bedrock` | Claude 3.5 Sonnet, requires AWS credentials |

## Running Tests

```bash
# Unit tests (no Docker/Ollama needed)
pytest -m "not integration"

# Integration tests (requires Docker up)
pytest -m integration -v

# End-to-end with real Ollama extraction (requires Docker + Ollama)
pytest tests/test_e2e_ollama.py -v -m integration -s

# Everything
pytest -v
```

## Office Simulation

The `simulation/` module runs a 12-month simulated office environment to validate the query engine and ADHD cognitive model. No Docker or LLM needed — uses in-memory stores.

```bash
# Run simulation tests
pytest simulation/ -v
```

The ADHD agent models:
- **Dopamine-driven task selection** via ICNU scoring (Interest, Challenge, Novelty, Urgency)
- **Hyperfocus** locking onto novel tasks
- **Executive dysfunction** when dopamine is low
- **Object permanence loss** (forgetting to check the system)
- **Wall of awful** (emotional paralysis on boring tasks)
- **Time blindness** (inaccurate effort estimates)

## Connectors

### Office 365 (Outlook)

Requires an Azure AD app registration with delegated `Mail.Read` permission. See `docs/office365_setup.md` for step-by-step setup.

```bash
# Set in .env
OUTLOOK_TENANT_ID=your-tenant-id
OUTLOOK_CLIENT_ID=your-client-id

# Fetch
python main.py fetch-outlook --since 2026-01-01
```

### Slack

Requires a Slack app with `channels:history` and `channels:read` scopes.

```bash
# Set in .env
SLACK_BOT_TOKEN=xoxb-your-token

# Fetch
python main.py fetch-slack --channel C0123456789
```

## Project Structure

```
brain-dump/
  main.py                  # CLI entry point
  core/
    nlp_processor.py       # LLM extraction (Ollama, Azure, Bedrock)
    graph_engine.py        # Neo4j Cypher queries
    vector_engine.py       # ChromaDB RAG search
    orchestrator.py        # Pipeline orchestration
  models/
    schemas.py             # Pydantic models
  connectors/
    outlook.py             # Office 365 connector
    slack.py               # Slack connector
  simulation/              # 12-month office simulation + ADHD agent
  tests/                   # Unit + integration tests
  docs/                    # Architecture docs, setup guides
  docker-compose.yml       # Neo4j + ChromaDB
  .env.example             # Configuration template
```
