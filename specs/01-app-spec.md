# Brain Dump — App Specification (backend internals)

> **Partially superseded by `04-integrated-design.md`.** The frontend pivoted to
> local-first Vite + React (ADR 0001/0008): **§8 (htmx frontend) is dead** — do not
> build it — and §7's FastAPI is a **JSON intelligence API only** (no HTML
> routes, no `/ui/*`). §§1–6 (domain model, ingestion, Store Protocol, query
> suite + scoring, Jira connector) remain the source of truth for backend
> internals. "Ollama" reads as "any local OpenAI-compatible server" (ADR 0005).

This is the spec for the backend service: ingestion, storage, the query/scoring
suite, the Jira connector, and the FastAPI JSON API. The Simulation Test Harness
is specified separately in `02-simulation-spec.md`.

Everything here is **backend-agnostic above the Store Protocol** (§4). The
query suite and scoring (§5) are pure functions over data the store returns;
they are the same code in tests (in-memory) and in production (Neo4j).

---

## 1. Domain model (the ontology)

Blends **PROV-O** (provenance) and a lightweight **Project Planning Ontology**.
All entities are Pydantic v2 models in the shared `models/` package.

### 1.1 Pydantic models

```
Platform (enum): gmail | slack | teams | outlook | jira

SourceMetadata          # PROV-O provenance record
  source_id: str        # email UID, Slack ts, or Jira issue key
  platform: Platform
  sender_name: str
  sender_email: str
  received_at: datetime
  thread_id: str | None # groups related messages / Jira issue comment chains

PersonEntity
  name: str
  email: str | None
  role: str | None
  aliases: list[str] = []

ProjectEntity
  name: str
  status: str = "active"      # active | blocked | completed
  priority: str = "medium"    # low | medium | high | critical

TaskEntity
  description: str
  status: str = "pending"     # pending | in_progress | done
  due_date: str | None        # ISO date
  assignee: str | None
  waiting_on: str | None
  priority: str = "medium"
  project: str | None
  estimated_minutes: int | None

MessageTone
  urgency_language: float = 0.0     # 0.0 "when you get a chance" → 1.0 "URGENT"
  escalation_signals: bool = False  # VP/HR/client/compliance/consequence
  emotional_temperature: str = "neutral"  # neutral|warm|frustrated|panicked|passive_aggressive
  is_follow_up: bool = False
  references_deliverable: bool = False
  peer_progress_mentioned: bool = False

ExtractionResult                    # the LLM (or agent) output payload
  people: list[PersonEntity] = []
  projects: list[ProjectEntity] = []
  tasks: list[TaskEntity] = []
  urls: list[str] = []
  summary: str
  tone: MessageTone | None = None
```

### 1.2 Graph nodes & relationships

| Node | Identity key | Notable props |
|---|---|---|
| `Person` | `email` if present, else `name` | role, aliases |
| `Project` | `name` | status, priority |
| `Task` | **composite `(description, project)`** | status, due_date, priority, estimated_minutes, created_at, updated_at |
| `Source` | `id` | platform, sender_name, sender_email, received_at, thread_id |

| Relationship | Meaning |
|---|---|
| `(Person)-[:ASSIGNED_TO]->(Task)` | who owns the task |
| `(Task)-[:PART_OF]->(Project)` | task belongs to project |
| `(Task)-[:DEPENDS_ON]->(Task)` | dependency (reserved; not yet surfaced in queries) |
| `(Task)-[:WAITING_ON]->(Person)` | task blocked on a person |
| `(Source)-[:GENERATED]->(Task)` | provenance: which message produced this task |
| `(Task)-[:REQUESTED_BY]->(Person)` | the Source sender who asked for it |
| `(Source)-[:RESPONDS_TO]->(Source)` | thread chaining within a `thread_id` |

### 1.3 Merge / identity invariants (correctness rules — keep these)

These were hard-won bug fixes in the prototype. They are **requirements**, with
tests:

- **INV-1 — REQUESTED_BY:** every generated Task links to the Source sender as
  the requester. Powers "what do I owe X" and relationship health.
- **INV-2 — Timestamps:** Tasks set `created_at` once (coalesce) and
  `updated_at` on every upsert.
- **INV-3 — Composite Task key:** Tasks MERGE on `(description, project)`, never
  on description alone. Two projects can have a "Submit Q1 budget" task without
  colliding.
- **INV-4 — Person identity:** MERGE on `email` when available; otherwise on
  `name`. Track alternate names in `aliases`. A short name ("Linda") resolves to
  the canonical record ("Linda Torres") when the email matches.
- **INV-5 — Thread chaining:** when a Source has a `thread_id`, create a
  `RESPONDS_TO` edge to the most recent prior Source in that thread.
- **INV-6 — Idempotent ingest:** re-ingesting the same Source must not create
  duplicate nodes or edges (MERGE semantics; edge-set dedup in-memory).

---

## 2. Ingestion pipeline

```
raw text + SourceMetadata
        │
        ▼
   Extractor.extract_entities(text) -> ExtractionResult     (§3)
        │
        ▼
   dual-write
        ├─ GraphStore.upsert_extraction(meta, extraction)   (graph)
        └─ VectorStore.upsert_document(id, text, metadata)  (vector)
```

`Pipeline` orchestrates this. `process_text(...)` takes text + provenance;
`process_file(path)` reads a `.txt` and uses the filename stem as `source_id`.
The vector metadata stores `sender_name`, `sender_email`, `platform`,
`received_at`, and the extraction `summary`.

---

## 3. LLM extraction

- **`Extractor`** wraps an `instructor`-patched client and enforces
  `ExtractionResult` as the response model.
- **Ollama (default, v1):** OpenAI-compatible client at
  `http://localhost:11434/v1`, **`instructor.Mode.JSON`** (not tool-calling —
  tool-call support varies wildly across local models; JSON mode is uniform).
- **Backend abstraction preserved:** `create_extractor_from_env()` reads
  `LLM_BACKEND`. Azure OpenAI and AWS Bedrock (Claude) code paths are kept in
  the interface but **out of scope for v1** and untested until re-enabled.
- The extraction prompt asks for: every person, every project, every task
  (with assignee/waiting_on/due_date/priority/estimated_minutes), a summary,
  and the full `MessageTone` analysis. (Prompt text extracted verbatim from the
  prototype `EXTRACTION_PROMPT`; refine during Phase 4.)

---

## 4. Storage — the Store Protocol

The single most important architectural change from the prototype. Define a
protocol (Python `typing.Protocol` / ABC) that **both** the Neo4j store and the
in-memory simulation store implement:

```
class GraphStoreProtocol(Protocol):
    def upsert_extraction(self, meta: SourceMetadata, ex: ExtractionResult) -> None
    def mark_task_done(self, description: str) -> None
    def close(self) -> None

    # --- primitive reads (return raw rows; ranking happens above) ---
    def hanging_tasks(self) -> list[dict]
    def project_overview(self) -> list[dict]
    def tasks_by_assignee(self, person: str) -> list[dict]
    def tasks_due_between(self, start: str, end: str) -> list[dict]
    def tasks_from_sender(self, sender: str) -> list[dict]
    def overdue_tasks(self, today: str) -> list[dict]
    def tasks_for_scoring(self, today: str) -> list[dict]   # rows enriched w/ mentions, tone, days_overdue
    def assigned_tasks_for_scoring(self, person: str, today: str) -> list[dict]
    def unanswered_threads(self, person: str) -> list[dict]
    def requester_task_rollup(self, today: str) -> list[dict]  # for relationship health

class VectorStoreProtocol(Protocol):
    def upsert_document(self, doc_id: str, text: str, metadata: dict) -> None
    def search_context(self, query: str, n_results: int = 5) -> dict
    def get_by_ids(self, ids: list[str]) -> dict
    def close(self) -> None
```

Two implementations:

- **`Neo4jGraphStore` / `ChromaVectorStore`** — production. Cypher /
  ChromaDB HTTP client. (Extracted from `core/graph_engine.py`,
  `core/vector_engine.py`.)
- **`InMemoryGraphStore` / `InMemoryVectorStore`** — simulation + unit tests.
  Pure Python dicts mirroring MERGE semantics; keyword search instead of
  embeddings. (Extracted from `simulation/stores.py`.)

**Scoring/ranking (frustration, forgetting, relationship-health trend,
nudge selection) lives ABOVE the store** as pure functions over the primitive
rows. This is what eliminates the prototype's logic duplication.

### 4.1 Docker services

`docker-compose.yml` brings up Neo4j (`7474` browser / `7687` bolt) and
ChromaDB (`8000`). Persistent volumes. First boot ~15s for Neo4j.

---

## 5. Query suite & scoring (the value surface)

All queries are exposed via the API (§7) and routed by keyword in the CLI/
frontend. Each is independently testable against the in-memory store using
simulation data.

### 5.1 Direct graph queries

| Query | Returns |
|---|---|
| **hanging / blocked** | tasks `-[:WAITING_ON]->` a person, not done; ordered by priority, due date. Enriched with RAG context from the vector store. |
| **project overview** | all tasks grouped by project with assignee + blocker + status. |
| **my tasks** (by assignee) | pending tasks `ASSIGNED_TO` a person, with project + blocker. |
| **due this week** (due between) | tasks with due_date in `[start,end]`, not done. |
| **what do I owe X** (from sender) | pending tasks `GENERATED` by X's Sources. |
| **overdue** | tasks with `due_date < today`, not done. |
| **unanswered threads** | threads where the person participated but isn't the last sender. |

### 5.2 Frustration score (stakeholder annoyance)

Computed per non-done task over all of its Sources:

```
priority_weight = {critical:4, high:3, medium:2, low:1}

tone_boost   = 5  if any escalation_signals
             + 3 * follow_up_count
             + 2  if worst_temperature in {frustrated, panicked}
             + 1.5 if worst_temperature == passive_aggressive
             + 3 * max(urgency_language over sources)        # 0..3

context_boost = 4  if any references_deliverable
              + 3  if any peer_progress_mentioned
              + 1.5 if a sibling task in the same project is done   # graph-derived peer proof

frustration = (mention_count*1.5 + days_overdue + tone_boost + context_boost) * priority_weight
```

Also returns `context_reasons` (human-readable "why this matters" strings:
"escalated to leadership", "asked 3x (2 follow-ups)", "feeds into upcoming
deliverable", "teammates are reporting progress", etc.) and a `tone_summary`.

### 5.3 Forgetting (anti-object-permanence)

Same scoring as §5.2 but **scoped to tasks assigned to "You"**, ranked by
frustration. This is the "what are you neglecting?" list. Feeds the nudge.

### 5.4 Relationship health

Per requester (via `REQUESTED_BY`): `health_pct = completed/total*100`,
`overdue_count`, and a `trend` label:
`declining` if `overdue>0 and health<50`, `stable` if `health>=80`, else
`improving`. Ordered worst-first.

### 5.5 Nudge (timeboxed, single task)

Returns the top forgetting result and renders an ADHD-friendly prompt:
one task only, who asked, how many times, due/overdue, estimated minutes vs a
small timebox, "why this matters" reasons, and a permission-to-stop message.
(UX copy extracted from `main.py: cmd_nudge`.)

### 5.6 Semantic search (fallback)

Anything not matched by the routes above → vector `search_context`.

### 5.7 Query routing table (CLI + frontend search box)

| Phrase contains | Route |
|---|---|
| "my tasks", "assigned to me" | tasks_by_assignee("You") |
| "due this week", "due today" | tasks_due_between |
| "overdue" | overdue_tasks |
| "frustrat", "annoyed", "stakeholder" | frustration_scores |
| "forget" | forgetting |
| "owe", "from <Name>" | tasks_from_sender |
| "waiting", "blocked", "hanging" | hanging_tasks (+ RAG) |
| "relationship", "health" | relationship_health |
| "project", "overview" | project_overview |
| "unanswered", "thread" | unanswered_threads |
| _else_ | semantic search |

---

## 6. Jira connector (v1 data source)

Replaces the prototype's Outlook/Slack connectors for v1. Goal: pull **real,
structured task data** so the graph/query/scoring stack can be validated
against something richer than hand-written `.txt` files.

### 6.1 Behavior

- Auth via Jira REST API v3 (Cloud) using an API token + email (basic auth) or
  a PAT (Server/DC). Config in `.env`:
  `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, optional `JIRA_JQL`.
- `fetch_issues(jql=None, since=None, max_results=...)` pages through issues.
- **Mapping Jira → domain:**

  | Jira field | Domain |
  |---|---|
  | issue key (e.g. `PHX-42`) | `SourceMetadata.source_id` |
  | `fields.summary` | `TaskEntity.description` |
  | `fields.assignee.displayName/emailAddress` | `TaskEntity.assignee` / Person |
  | `fields.duedate` | `TaskEntity.due_date` |
  | `fields.priority.name` | mapped to low/medium/high/critical |
  | `fields.project.name` | `ProjectEntity` + `TaskEntity.project` |
  | `fields.status.name` | mapped to pending/in_progress/done |
  | `fields.reporter` | `SourceMetadata.sender_*` + `REQUESTED_BY` |
  | `fields.created/updated` | `received_at` |
  | comments (optional) | additional Sources sharing `thread_id = issue key` |
  | `fields.description` | text body sent to vector store |

- Two modes:
  - **structured** (default): build `ExtractionResult` directly from Jira fields
    — no LLM needed, fully deterministic, great for tests.
  - **enriched** (optional): also run the description/comments through the
    Extractor to pick up tone + tasks mentioned in free text.

### 6.2 Connector interface (so Outlook/Slack slot back in later)

```
class Connector(Protocol):
    def authenticate(self) -> None
    def fetch(self, since: str | None = None, **kw) -> Iterable[tuple[str, SourceMetadata, ExtractionResult | None]]
```

The pipeline consumes `(text, meta, extraction_or_None)`; if `extraction` is
`None`, it runs the LLM extractor (enriched mode).

---

## 7. FastAPI service

A thin HTTP layer over the Pipeline + Store Protocol. Auto-generated OpenAPI;
tested with `TestClient`/`httpx`. Dependency-injected stores so tests inject
the in-memory implementations.

### 7.1 Endpoints (v1)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/ingest` | body `{text, platform, sender_name, sender_email, received_at?, thread_id?}` → runs pipeline, returns extraction. |
| `POST` | `/ingest/file` | multipart upload of a `.txt`. |
| `POST` | `/jira/sync` | trigger Jira fetch+ingest; body `{jql?, since?, mode}`. |
| `GET` | `/query` | `?q=<natural language>` → routed result (§5.7). |
| `GET` | `/tasks/mine` | tasks_by_assignee. |
| `GET` | `/tasks/due` | `?start=&end=`. |
| `GET` | `/tasks/overdue` | overdue_tasks. |
| `GET` | `/tasks/hanging` | blocked tasks + RAG context. |
| `GET` | `/projects` | project overview. |
| `GET` | `/frustration` | frustration scores. |
| `GET` | `/forgetting` | forgetting list. |
| `GET` | `/relationships` | relationship health. |
| `GET` | `/nudge` | `?timebox=15` → single-task nudge payload. |
| `GET` | `/search` | `?q=` semantic search. |
| `GET` | `/healthz` | liveness; reports DB connectivity. |

JSON responses are Pydantic response models (typed, documented). The same
service renders htmx partials (§8) for the same data.

---

## 8. htmx frontend

Server-rendered HTML with Jinja2 templates; htmx swaps partials. **No SPA, no
build step.** FastAPI serves both JSON (`Accept: application/json`) and HTML
partials (default) from the same handlers, or via parallel `/ui/*` routes —
decide in Phase 6 (recommend `/ui/*` HTML routes that call the same service
functions, keeping JSON API clean).

### 8.1 Views

| View | Content | htmx interactions |
|---|---|---|
| **Dashboard** (`/`) | The nudge card (one task) + the forgetting list + counts (overdue, blocked). | "Done" button POSTs mark-done, swaps the card for the next nudge. "Snooze/Next" cycles. |
| **Tasks** | My tasks, due-this-week, overdue (tabbed). | Tab clicks `hx-get` partials. Mark-done inline. |
| **Projects** | Project overview grouped, with blockers highlighted. | Expand/collapse per project. |
| **Relationships** | Per-person health bars + trend arrows. | — |
| **Frustration heatmap** | Tasks ranked by frustration with reason chips. | — |
| **Search** | A box that hits `/query` routing; renders whichever partial matches. | `hx-get` on input (debounced). |
| **Jira sync** | Button + status; shows last sync counts. | `hx-post /jira/sync`, polls status. |

### 8.2 Frontend testing

- Template/partial rendering unit-tested (assert key data present in HTML).
- A small **Playwright** smoke suite drives the real pages against a
  TestClient-backed server seeded with simulation data: load dashboard, click
  "Done," assert the nudge advances; run a search, assert results render.

---

## 9. Configuration (`.env`)

```
LLM_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5-coder:7b

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

CHROMA_HOST=localhost
CHROMA_PORT=8000

JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_EMAIL=you@org.com
JIRA_API_TOKEN=...
JIRA_JQL=assignee = currentUser() AND statusCategory != Done

# deferred: AZURE_*, BEDROCK_*, OUTLOOK_*, SLACK_*
```

---

## 10. Non-functional requirements

- **Python 3.11/3.12.** chromadb >= 1.5.
- **Determinism:** structured Jira mode and the in-memory store must produce
  identical output for identical input (no wall-clock leakage into logic — pass
  `today` in).
- **Idempotency:** see INV-6.
- **Separation:** the App package must not import the simulation package
  (CI-enforced import check).
- **Observability:** `/healthz`, structured logs on ingest (counts), and clear
  error surfaces when Ollama/Neo4j/Chroma are unreachable.
