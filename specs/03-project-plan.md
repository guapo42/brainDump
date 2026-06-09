# Brain Dump — Project Plan (from-scratch rebuild)

> **Superseded by `05-iterative-plan.md`** for sequencing and scope. Retained
> because `05`'s source-plan mapping references these backend phases (P1–P5, P8,
> P9) for their implementation detail. Ignore the htmx frontend phases (P6 here)
> and any FastAPI-as-UI content — see ADR 0001 and `04-integrated-design.md`.

A phased plan optimized for **validating each feature as it lands** and
**co-developing the htmx frontend alongside the backend**. Three workstreams
run in parallel, synchronized at phase gates:

- **Track A — App backend** (domain, stores, queries, scoring, extraction,
  Jira, FastAPI).
- **Track B — Frontend** (htmx/Jinja pages).
- **Track C — Simulation harness** (in-memory stores, office agents, cognitive
  model, reports) — also the test net for Track A's logic.

The load-bearing idea (from `00-overview.md`): **scoring/query logic is written
once above the Store Protocol**, unit-tested against the in-memory store via the
simulation, and run unchanged against Neo4j. So Track C's value lands *before*
any database exists.

---

## Target structure

```
brain_dump/
  models/            # shared Pydantic domain models  (Track A+C contract)
  stores/
    protocol.py      # GraphStoreProtocol, VectorStoreProtocol
    memory.py        # InMemory* (Track C + unit tests)
    neo4j_store.py   # Neo4jGraphStore
    chroma_store.py  # ChromaVectorStore
  domain/
    scoring.py       # frustration, forgetting, relationship-health, nudge (pure fns)
    routing.py       # natural-language → query dispatch
  ingest/
    extractor.py     # LLM extraction (Ollama; azure/bedrock stubs)
    pipeline.py      # dual-write orchestration
  connectors/
    base.py          # Connector protocol
    jira.py          # v1 connector
  api/
    app.py           # FastAPI; DI of stores
    routes.py        # JSON endpoints
    ui.py            # htmx/Jinja HTML routes
    templates/       # Jinja templates + partials
  cli.py             # argparse CLI (parity with API)
sim/                 # SIMULATION HARNESS — never imported by brain_dump/*
  clock.py registry.py stores_check.py
  agents/  cognitive/  reports/  run.py
tests/
  unit/  contract/  integration/  api/  e2e/  frontend/
docker-compose.yml  pyproject.toml  .env.example  README.md
```

CI guard: an import-linter (or a simple test) asserts `brain_dump/` never
imports `sim/`, and `sim/` never imports `stores.neo4j_store`,
`stores.chroma_store`, `ingest.extractor`, `connectors`, or `api`.

---

## Phase 0 — Scaffold & guardrails

**Do:** `pyproject.toml` (ruff + pytest + mypy), package skeleton, `pytest.ini`
markers (`unit`, `contract`, `integration`, `e2e`, `frontend`), GitHub Actions
running `pytest -m "not integration and not e2e"` + lint + the import-separation
check. `docker-compose.yml` (Neo4j + Chroma). `.env.example`.

**Gate:** `pytest` runs green on an empty suite; CI passes; `docker-compose up`
starts both services; the separation check is active.

---

## Phase 1 — Shared domain model + Store Protocol + in-memory store

*Track A + C foundation. No DB, no LLM.*

**Do:** Port the Pydantic models (`models/`). Define `GraphStoreProtocol` /
`VectorStoreProtocol` (`stores/protocol.py`). Implement `InMemoryGraphStore` /
`InMemoryVectorStore` (`stores/memory.py`) with the identity invariants
INV-1..6. Write the **contract test suite** (`tests/contract/`) that any store
must pass — initially run against the in-memory store only.

**Gate:** `pytest -m "unit or contract"` green. Models validate; contract tests
prove MERGE/identity semantics. This is the first feature validated end-to-end
with zero infrastructure.

---

## Phase 2 — Query suite + scoring (the value surface)

*Track A logic, validated by Track C.*

**Do:** Implement the primitive reads on the in-memory store. Implement
`domain/scoring.py` (frustration formula §5.2, forgetting §5.3,
relationship-health trend §5.4, nudge selection §5.5) as **pure functions** over
store rows. Implement `domain/routing.py` (§5.7). Build the **simulation
skeleton**: `SimClock`, `registry`, `BaseAgent`, and the office agents'
storylines; the passive `UserAgent` + `GapAnalyzer`.

**Gate:** Run the **passive simulation** (`python -m sim.run --passive`):
every production query reports 100% success across 52 weeks; >100 messages,
>50 tasks; integrity checks clean. Unit tests pin each scoring formula on
crafted fixtures (e.g. escalation adds +5, a done sibling task adds peer-proof).
**Now every query and score is provably correct before any database exists.**

---

## Phase 3 — Real adapters behind the same contract

*Track A infra.*

**Do:** Implement `Neo4jGraphStore` (port the Cypher from the prototype) and
`ChromaVectorStore`. Run the **same contract test suite** from Phase 1 against
them under the `integration` marker. Reconcile any divergence so in-memory and
Neo4j are behaviorally identical (this catches the prototype's drift).

**Gate:** `pytest -m integration` green with Docker up. Contract parity:
identical query results from in-memory vs Neo4j on the same ingest sequence.

---

## Phase 4 — LLM extraction + ingestion pipeline

*Track A.*

**Do:** Port `Extractor` (Ollama, instructor JSON mode) + the extraction
prompt; `create_extractor_from_env()`. Build `ingest/pipeline.py` (dual-write).
Keep azure/bedrock branches as unexercised stubs.

**Gate:** Unit test extraction with a **mocked** instructor client (no network).
An `e2e` test (marker, opt-in) ingests a sample email via real Ollama and
asserts the graph/vector got populated. `cli.py ingest -f <file>` works against
live Docker+Ollama.

---

## Phase 5 — FastAPI service

*Track A; unblocks Track B.*

**Do:** `api/app.py` with DI'd stores (so tests inject in-memory). Implement the
JSON endpoints (§7). Pydantic response models → OpenAPI. `/healthz`.

**Gate:** `pytest -m api` (TestClient + in-memory store seeded with simulation
data) covers every endpoint incl. routing and nudge. OpenAPI served at
`/docs`. This is the contract the frontend builds against.

---

## Phase 6 — htmx frontend (co-developed)

*Track B. Can start against mocked endpoints as soon as Phase 5 routes are
stubbed.*

**Do:** Jinja base layout + `api/ui.py` HTML routes calling the same service
functions. Build views in value order: **Dashboard (nudge + forgetting)** →
Tasks → Projects → Relationships → Frustration heatmap → Search → Jira sync
panel (§8.1). htmx partial swaps; "Done" advances the nudge.

**Gate:** Template rendering unit tests (key data present in HTML). A
**Playwright** smoke suite drives a TestClient-backed server seeded with
simulation data: dashboard loads, "Done" advances the nudge, search renders the
right partial. Frontend is demoable end-to-end without real services.

---

## Phase 7 — Jira connector (real task data)

*Track A; the v1 differentiator.*

**Do:** `connectors/jira.py` implementing the `Connector` protocol; field
mapping (§6.1); structured (no-LLM) + enriched modes; `POST /jira/sync` +
the frontend sync panel. Pagination, priority/status normalization, comments →
threaded Sources.

**Gate:** Connector unit-tested against **recorded Jira JSON fixtures** (no live
API) asserting correct domain mapping + invariants. An opt-in live test syncs a
real board (env-gated) and the dashboard shows real tasks ranked by frustration.
**This is the milestone where you validate against your own task data.**

---

## Phase 8 — ADHD cognitive model + reports

*Track C. Independent of Tracks A/B after Phase 2 — schedule in parallel.*

**Do:** Port `cognitive/` (state, ICNU §5.2, behaviors §5.3), `ADHDUserAgent`
tick loop, and `ADHDReportGenerator`. Wire frustration→urgency coupling.

**Gate:** The cognitive test suite (`02-simulation-spec.md §7`) passes:
`0 < completion_rate < 1`, hyperfocus/distraction/object-permanence all >0,
deterministic by seed, and the **frustration-coupling result** (boring
escalated tasks get completed) holds. `python -m sim.run` prints the report +
weekly heatmap.

---

## Phase 9 — Hardening & docs

**Do:** README rewrite (quick-start: Docker, Ollama, Jira, run app, run sim).
Error handling for unreachable Ollama/Neo4j/Chroma. Structured ingest logging.
Final separation-lint + full-suite CI (unit/contract/api/frontend always;
integration/e2e gated).

**Gate:** Fresh clone → `docker-compose up` → `jira sync` → open dashboard →
nudge works. `pytest` (fast lanes) green. `pytest -m "integration or e2e"`
green with services up.

---

## Dependency / sequencing summary

```
P0 ──► P1 ──► P2 ──┬──► P3 ──► P4 ──► P5 ──► P6 ──► P7 ──► P9
                   └──► P8 (parallel, needs only P2)
```

- **Validate-as-you-go:** P1, P2, P5, P6, P7, P8 each end with a runnable gate.
- **Frontend co-development:** real from P6, mockable from end of P5.
- **App ↔ Sim separation:** enforced from P0; the sim is the inner-loop test
  net from P2 onward.

## Per-phase Definition of Done (applies to every phase)

1. New code has unit/contract tests in the fast lane (green in CI).
2. The relevant simulation gate still passes (no logic regression).
3. The app/sim import-separation check still passes.
4. A one-line "how to see it work" command is added to the README.
5. Lint + type checks clean.

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| In-memory vs Neo4j drift (the prototype's core flaw) | Single contract test suite run against both (P3); scoring lives above the store. |
| Local LLM extraction flakiness | Structured Jira mode needs no LLM; LLM tests mocked in fast lane, real only in opt-in `e2e`. |
| Frontend blocked on backend | Stub endpoints at end of P5; frontend builds against TestClient + seeded sim data. |
| Scope creep (Outlook/Slack/Azure/Bedrock) | Kept behind the Connector/Extractor protocols, explicitly deferred past v1. |
| Non-determinism leaking into tests | `today` passed in everywhere; sim seeded; no `datetime.now()` in logic. |
