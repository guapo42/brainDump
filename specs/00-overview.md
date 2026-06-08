# Brain Dump — Rebuild Overview

> **Update (frontend pivot):** the product frontend is now *The External Lobe*,
> a React/Next local-first cognitive cockpit, with Brain Dump (Python) as an
> optional intelligence service behind an `IntelligenceService` port. This
> **supersedes the htmx decision** in §5 below and the htmx/FastAPI-as-UI parts
> of `01`/`03`. See **`04-integrated-design.md`** (the seam) and
> **`05-iterative-plan.md`** (the re-sequenced roadmap). The backend internals
> in `01`/`02` remain valid.

> This is the foundation document for a clean, test-driven reimplementation of
> Brain Dump. It is extracted from the existing prototype (see "Provenance"
> below) and reorganized around two hard rules: **every feature must be
> independently testable as it lands**, and **the App and the Simulation Test
> Harness are separate concerns that share only a domain contract**.

## 1. What Brain Dump is

A "Second Brain" ingestion engine that turns fragmented communication
(email, Slack, Teams, and — in this rebuild — Jira issues) into a structured
knowledge graph. It extracts people, projects, tasks, deadlines,
dependencies, and tone from raw text, stores them in a graph DB (Neo4j) and a
vector DB (ChromaDB), and surfaces *what matters right now* through a query
suite, a stakeholder-frustration model, and an ADHD-aware "nudge."

It ships with a **Simulation Test Harness**: a deterministic, no-Docker,
no-LLM 12-month office scenario that exercises the query/scoring logic and
models realistic executive-dysfunction behavior. The simulation is how we
validate the app's logic cheaply and repeatably.

## 2. The two halves (and why they stay separate)

```
                ┌─────────────────────────────────────────────┐
                │            SHARED DOMAIN CONTRACT             │
                │  models/  (Pydantic entities) + Store Protocol │
                └───────────────┬───────────────────┬───────────┘
                                │                   │
              depends on        │                   │   depends on
                                ▼                   ▼
        ┌───────────────────────────────┐   ┌──────────────────────────────┐
        │            THE APP            │   │   THE SIMULATION TEST HARNESS │
        │  (real product, runs live)    │   │  (validation, runs in-memory) │
        │                               │   │                               │
        │ • LLM extraction (Ollama)     │   │ • Office agents (scripted)    │
        │ • Neo4j + Chroma adapters     │   │ • In-memory graph/vector      │
        │ • Query suite + scoring       │   │ • ICNU / ADHD cognitive model │
        │ • Jira connector              │   │ • Gap + ADHD reports          │
        │ • FastAPI REST API            │   │ • Deterministic 52-week clock │
        │ • htmx frontend               │   │                               │
        └───────────────────────────────┘   └──────────────────────────────┘
```

**The separation rule (enforced in CI):**

- **Shared** — only the Pydantic domain models (`ExtractionResult`,
  `TaskEntity`, `PersonEntity`, `ProjectEntity`, `SourceMetadata`,
  `MessageTone`) and the **Store Protocol** (the query/upsert interface).
- **The App may NOT import from the simulation package.**
- **The simulation may NOT import App adapters** (no `neo4j`, `chromadb`,
  `openai`, `instructor`, FastAPI, or connector code). It depends only on the
  shared contract and its own in-memory implementations.
- Both the in-memory store and the Neo4j store implement the **same Store
  Protocol**. This is the load-bearing design decision: the query suite and
  scoring logic are written once, unit-tested against the fast in-memory store
  via simulation data, and run unchanged against the real database.

Why this matters: in the prototype, query/scoring logic was effectively
duplicated between `core/graph_engine.py` (Cypher) and
`simulation/stores.py` (Python). They drifted. In the rebuild, the
**scoring/ranking logic lives in one place** above the store, and only the
raw data-access primitives differ per backend.

## 3. Provenance — what we extracted this from

The prototype lives in the repository root (`main.py`, `core/`, `models/`,
`connectors/`, `simulation/`, `docs/`). It is a working but organically-grown
codebase. The rebuild keeps every good idea and discards the duplication. Key
source material:

| Concept | Extracted from |
|---|---|
| Ontology + Pydantic models | `models/schemas.py` |
| Cypher upsert + 11 queries | `core/graph_engine.py` |
| Frustration / forgetting scoring | `core/graph_engine.py`, `simulation/stores.py` (`_compute_frustration`) |
| LLM extraction (Ollama/instructor) | `core/nlp_processor.py` |
| Query routing + nudge UX | `main.py` |
| ICNU + cognitive model | `simulation/cognitive/` |
| Office agents + 12-month storylines | `simulation/agents/`, `simulation/registry.py` |
| Reports | `simulation/reports/` |
| Original phase docs | `docs/phase1..4_*.md`, `docs/system_overview.md` |

## 4. Documents in this spec set

1. **`00-overview.md`** (this file) — vision, the app/sim separation, glossary.
2. **`01-app-spec.md`** — the product: domain model, ingestion, storage,
   query suite + scoring formulas, Jira connector, FastAPI API, htmx frontend.
3. **`02-simulation-spec.md`** — the test harness: clock, office agents,
   in-memory stores, ICNU + behavioral cognitive model, reports.
4. **`03-project-plan.md`** — phased build plan; each phase ends with a
   concrete, runnable validation gate. App backend, frontend, and simulation
   are tracked as parallel-but-synchronized workstreams.

## 5. Decisions locked for v1

| Decision | Choice | Notes |
|---|---|---|
| Frontend | ~~Plain HTML + htmx~~ → **React/Next local-first** (*The External Lobe*) | Superseded by `04`. Rich client (rAF graph, SVG dial, client FSM, offline capture); Zustand + Framer Motion + Vitest. |
| Backend API | **FastAPI + OpenAPI** (JSON intelligence API only) | No server-rendered UI; serves the `IntelligenceService` adapter. Typed; tested with `httpx`/`TestClient`. |
| Data authority | **Local-first; backend syncs** | Client (IndexedDB/Zustand) owns live cognitive state; backend adds sources + enrichment additively (`04 §7`). |
| Scope | **Core-first** | Ingest, graph/vector, query suite, scoring, nudge. |
| Connector | **Jira** (new) | Replaces Outlook/Slack for v1 — gives real structured task data to validate against. |
| LLM backend | **Ollama only** | Azure/Bedrock abstraction preserved but deferred. |
| Deferred | Outlook, Slack, Azure, Bedrock | Re-add behind the same connector/extractor interfaces post-v1. |

## 6. Glossary

- **Source** — one ingested communication (email, Slack/Teams msg, Jira issue).
  Carries provenance (PROV-O).
- **Extraction** — the structured `ExtractionResult` an LLM (or an agent, in
  the sim) produces from a Source.
- **Dual-write** — every ingest writes structured entities to the graph and
  raw text to the vector store.
- **ICNU** — Interest / Challenge / Novelty / Urgency; the dopamine-driven
  task-selection score the ADHD agent uses instead of priority.
- **Frustration score** — how annoyed the requester(s) of a task likely are,
  derived from mentions, overdue days, tone, and context.
- **Object permanence (loss)** — the modeled tendency to forget to check the
  system for things not currently visible.
- **Store Protocol** — the shared interface both the in-memory store and the
  Neo4j store implement.
