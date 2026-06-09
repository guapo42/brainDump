# Integrated Iterative Plan — testing ideas early

> Re-sequences *The External Lobe — TDD Reimplementation Plan* (M0–M16) and the
> Brain Dump backend plan (`specs/03-project-plan.md`) into one idea-driven
> roadmap. Optimized for **testing ideas cheaply**: every phase is a runnable
> demo that validates a hypothesis, the frontend is built **stub-first** behind
> the `IntelligenceService` port (`04 §3`), and the backend plugs in later
> without reshaping the client.

## Methodology

- **TDD spine (from the External Lobe plan):** pure logic → stores → hooks →
  components → integration. Red before green. Pure-logic milestones target ~100%
  branch coverage; every spec constant gets a pinning test.
- **Stub-first seam:** the client always runs on `LocalIntelligence`. The
  `BrainDumpIntelligence` adapter and the Python backend are a parallel track
  that only has to satisfy the port's recorded fixtures.
- **Vertical, demoable slices:** each phase states a **hypothesis to test** and
  ends with a **demo + green gate**, so you can feel whether an idea works before
  investing further.
- **Inject time/IO:** no `Date.now()`/`setInterval`/`fetch` in pure logic without
  a seam; fake timers + stubbed clients in tests.

## Tracks (run in parallel, sync at gates)

- **A — Anchor** (client pure logic): ICNU+energy, FSM, schema validator,
  scrubber, guardrails.
- **B — Translator** (client LLM + heuristic fallback, injected fetch).
- **C — Shell** (client): tooling, `safeStorage`, Zustand stores, the
  `IntelligenceService` port + `LocalIntelligence`.
- **D — Experience** (client UI): capture, time dial, focus/retention, graph,
  dashboard.
- **E — Backend** (Python): Store Protocol, in-memory + Neo4j, Extractor, Jira,
  FastAPI JSON API, the `BrainDumpIntelligence` it serves.
- **F — Seam/Sync**: the adapter, enrichment merge, offline queue, contract tests.

---

## Success definition & cut lines

The biggest risk to this project is not a wrong abstraction — it is building a
large, two-stack system that never becomes something its builder actually uses.
So success is defined behaviorally, and the plan has explicit cut lines:

- **Success (v1):** the builder uses the app **daily** as their real capture +
  task-surfacing tool, and prefers it to whatever they used before. Everything
  else (graph, RAG, relationship health) is judged by whether it deepens that.
- **Daily-driver gate:** from **P3** onward, every phase's Definition of Done
  includes **≥3 days of real personal use** of the build, with friction notes
  filed to `docs/carry_forward.md`. A phase whose feature went unused in those
  days gets questioned before the next phase starts.
- **MVP cut line = P0–P3.** If the project stopped after P3 it should still be a
  win: an offline, zero-friction capture + energy-ranked cockpit. **P4 (Jira)
  earns its place only if external tasks are part of daily reality.**
- **Value ladder, not a contract:** P5–P7 each re-justify themselves against
  actual usage at their pre-flight. Skipping or reordering them is allowed; the
  gates travel with the phase.
- **P8 is split:** the **passive simulation** (P2) and the **seed-fixture
  export** are required regression/demo infrastructure. The **ADHD cognitive
  agent** is explicitly **stretch** — it validates backend scoring realism, not
  the product (the canonical ICNU is client-side; ADR 0004). Build it last, or
  not at all if daily use says the time is better spent elsewhere.

## Phase 0 — Foundations & the seam *(blocks all)*

**Hypothesis:** we can stand up a test-first repo where the frontend is fully
decoupled from the backend.

- Monorepo: `/app` (Next App Router, TS, Tailwind, Zustand, Framer Motion,
  Vitest + jsdom + Testing Library), `/backend` (Python, pytest, ruff, mypy),
  `/specs`, `/fixtures` (shared recorded JSON).
- `safeStorage` wrapper first (SSR/quota/corrupt-JSON). [External Lobe M0]
- Define the `IntelligenceService` **types + port** and a no-op
  `LocalIntelligence` skeleton.
- CI: `app` lane (typecheck+lint+test+build) and `backend` lane
  (lint+unit/contract), plus the app↔sim and app↔backend import-separation
  checks.

**Gate/Demo:** `npm test` + `pytest` both run green-empty; `safeStorage` tests
pass; CI green.

---

## Phase 1 — Anchor core: does energy-driven surfacing feel right? *(Track A)*

**Hypothesis:** ranking tasks by an energy-weighted FocusScore surfaces the
"right" task better than priority lists.

- ICNU engine (spec §4.1): weight profiles, `FocusScore`, `filterByEnergy`,
  `wedgeExpansion`, `rankTasks`. [M2]
- FSM reducer (spec §4.2): full transition table, focus-minute accrual,
  anti-paralysis trigger. [M3]
- SVG math (spec §7) [M1] — needed soon for the dial.

**Gate/Demo:** a tiny harness page seeded with fixture tasks + an energy slider;
flipping energy 1↔5 visibly re-ranks. Unit tests pin every weight/threshold.
**This is the first idea you can feel, with zero backend and zero real UI.**

---

## Phase 2 — Zero-friction capture + Translator offline *(Tracks B, C, D)*

**Hypothesis:** capture completes < 3s and works fully offline.

- LLM client with **injected fetch** (Ollama happy path, JSON extraction,
  timeout, backoff, fallback). [M6]
- Intent parser + pipeline + heuristic fallback + micro-actions; `quickCapture`
  LLM-free path. [M7]
- Schema validator + type guards + scrubber (fix spaced-card regex). [M4, M5]
- Stores (`useStore`, `useAnchorStore`, undo) through `safeStorage`. [M8]
- Lightning Capture + Capture Modal (Cmd-K). [M11 subset]

**Gate/Demo:** with Ollama **off**, type a thought → a valid `Task` appears on
the belt in < 3s (heuristic); with Ollama **on**, it's structured. Friction > 5s
logged. Tests stub the client (no real model).

---

## Phase 3 — The cognitive cockpit: does it reduce initiation paralysis? *(Tracks A, D)*

**Hypothesis:** the time dial + activation bridge + guardrails get the user
*started*.

- Radial Time-Dial (wedge ∝ `wedgeExpansion`, now-indicator breathing 60bpm,
  urgency ring). [M10]
- Activation Bridge (UI lock → 3 micro-entries → DEEP_FOCUS) + Anti-Paralysis
  overlay. [M13]
- Guardrails + hooks: body double, mental snapshots, break suggestion, visual
  decay, focus ember, focus lens, resumption, object-permanence pulse. [M9, M12]

**Gate/Demo:** §13 scenarios 3–6 (Activation Bridge, Anti-Paralysis, Body
Double, Resumption) pass as component/integration tests; demo the full
focus loop locally.

---

## Phase 4 — Real task data on the belt *(Tracks E, F)* — backend enters

**Hypothesis:** real Jira tasks flow onto the belt and feel native.

- Backend (from `specs/03` P1–P5, scoped to the port's needs): domain models,
  Store Protocol + `InMemoryGraphStore`, primitive reads, **Jira connector
  (structured mode)**, minimal FastAPI (`/jira/sync`, `/tasks/mine`,
  `/search`).
- `BrainDumpIntelligence` adapter implementing `fetchInbox`/`search`; map
  backend tasks → client `Task` (`04 §4.2`).
- Offline queue + merge-by-`source_ref` (client fields win).

**Gate/Demo:** point at a real Jira board → `fetchInbox` populates the belt;
energy ranking applies to real tasks. Adapter tested against **recorded Jira
fixtures**; backend Jira mapping tested against recorded issue JSON. App still
fully works with backend **off** (`LocalIntelligence`).

---

## Phase 5 — Stakeholder pressure surfaces the boring stuff *(Tracks E, F, A)*

**Hypothesis:** the frustration→urgency bridge makes neglected/escalated tasks
rise — even at low energy.

- Backend scoring (`specs/01 §5.2–5.5`): frustration, forgetting,
  relationship-health, nudge; endpoints `/frustration`, `/forgetting`,
  `/relationships`, `/nudge`.
- Port `enrich`/`forgetting`/`relationshipHealth`; merge `frustration`/
  `context_reasons`/`requesters` into tasks; apply the urgency bridge (`04 §5`).
- Surfaces: object-permanence feed = backend `forgetting`; Relationships view;
  reason chips on tasks.

**Gate/Demo:** **the headline test** — a high-frustration backend task (e.g. an
escalated admin item) outranks an interesting-but-non-urgent task at Energy 1.
Relationship health renders from real REQUESTED_BY rollups. `LocalIntelligence`
provides a heuristic frustration stub so this surface exists offline too.

---

## Phase 6 — Second Brain graph from real data *(Tracks E, F, D)*

**Hypothesis:** a knowledge graph of people/projects/tasks adds orientation
without tanking performance.

- Backend Neo4j store + `graphNeighborhood` endpoint (port from `specs/03` P3).
- Client force-directed graph [M14]: importance/radius, gravity sim, and the
  **halt-when-settled/hidden/off-screen** contract (assert rAF stops). Cache last
  slice for offline.

**Gate/Demo:** click a project → real neighborhood expands; sim provably pauses
when settled/hidden. Backend contract tests confirm in-memory vs Neo4j parity
(`specs/02 §4`).

---

## Phase 7 — Sync, airlock, resilience *(Tracks F, D)*

**Hypothesis:** the morning ritual and offline/online transitions feel seamless.

- Airlock Gatekeeper (07:00–09:00) seeded by an overnight backend sync
  (new/overdue/escalated). [M11 subset + `04 §7`]
- Robust offline queue flush, conflict policy, tombstones; degrade cleanly when
  `isAvailable()` flips.
- Engagement layer finish: Undo Timeline, Breadcrumb Sidebar, Review Flag
  Banner. [M12]
- Backend `push` ingestion (captures → durable graph + enrichment back).

**Gate/Demo:** kill the backend mid-session → app keeps working, queues pushes,
reconciles on reconnect. Airlock at 08:00 shows reality-seeded dump.

---

## Phase 8 — End-to-end & regression nets *(all)*

**Hypothesis:** the whole experience holds together and stays correct.

- Playwright over the 8 global acceptance scenarios (spec §13) with a **stubbed
  LLM + stubbed backend** for determinism. [M16]
- Backend regression nets stay green: contract tests (in-memory↔Neo4j), the
  52-week passive simulation (query coverage 100%), the ADHD cognitive sim
  (backend scoring realism + frustration coupling) — `specs/02 §7`.
- Optional: export a **seed fixture** from the backend sim so the frontend has
  instant rich demo data offline (`04 §12.5`).

**Gate/Demo:** all 8 scenarios pass; both test spines green; a fresh clone demos
end-to-end with services off (stubs) and on (real Jira/Neo4j/Ollama).

---

## Dependency graph

```
P0 ─┬─► P1 (Anchor) ─────────────► P3 (cockpit) ─┐
    ├─► P2 (capture+translator) ──────────────────┼─► P7 (sync/airlock) ─► P8 (e2e)
    └─► P4 (Jira on belt) ─► P5 (frustration) ─► P6 (graph) ─┘
```

- **Frontend-first:** P1–P3 deliver the whole felt experience on `LocalIntelligence`
  with no backend.
- **Backend enters at P4** behind the port and only deepens the data.
- **Headline idea (frustration→surfacing) is testable at P5.**

## Source-plan mapping

| This plan | External Lobe milestones | Brain Dump backend (`specs/03`) |
|---|---|---|
| P0 | M0 | P0 |
| P1 | M1, M2, M3 | — |
| P2 | M4, M5, M6, M7, M8, M11(subset) | — |
| P3 | M9, M10, M12, M13 | — |
| P4 | (adapter) | P1, P2, P4(Jira), P5(subset) |
| P5 | (urgency bridge) | P2 scoring |
| P6 | M14 | P3 |
| P7 | M11(airlock), M12(rest) | P4 push |
| P8 | M15, M16 | P8(sim), P9 |

## Definition of Done (per phase)

1. Each spec acceptance criterion in scope has a test.
2. `typecheck`/`lint` clean; **no `any`, no `as unknown as`** at the LLM boundary.
3. Pure-logic near 100% branch coverage; the relevant simulation/contract gate
   still green (no regression).
4. The app runs and demos the phase's hypothesis with the **backend off**
   (where applicable) and **on**.
5. Import-separation checks (app↔sim, app↔backend) still pass.
6. One commit per coherent green slice, referencing the phase.

## Risks (additions to the source registers)

| Risk | Mitigation |
|---|---|
| Two systems drift at the seam | One `IntelligenceService` port + shared recorded fixtures both impls must satisfy. |
| Enrichment merge clobbers user intent | Explicit merge policy (`04 §7`): client-owned fields win. |
| Backend pulled in too early, slows idea-testing | Hard rule: P1–P3 ship on `LocalIntelligence`; backend is P4+. |
| Two ICNU models confuse contributors | `04 §5`: product 0–10 canonical; sim ICNU is backend-validation only, never shipped. |
| Local LLM nondeterminism in tests | All Translator + adapter tests use stubs; real model only in opt-in e2e. |
| Offline/online edge cases | P7 dedicated to queue/conflict/degradation; tested with `isAvailable` toggles. |
```
