# Brain Dump × The External Lobe — Integrated Design Spec

> **Status:** for review. This document reconciles two source specs into one
> product and supersedes the frontend decisions in `00-overview.md` (htmx) and
> `01/03` (htmx views, FastAPI-as-primary-UI). The Brain Dump backend specs
> (`01-app-spec.md` §1–6, `02-simulation-spec.md`) remain valid as **backend
> internals**; this doc defines the **integration contract** between them.
>
> Canonical sources of truth:
> - **Frontend behavior** → *The External Lobe — Specification* (Triple-Engine).
> - **Backend internals** → `specs/01-app-spec.md`, `specs/02-simulation-spec.md`.
> - **The seam between them** → this document.

---

## 1. The product, in one sentence

**The External Lobe** is a local-first Vite + React cognitive cockpit (Tauri
desktop shell; ADR 0008) (Pilot →
Translator → Anchor) that runs fully offline; **Brain Dump** is an optional
Python intelligence service behind it that ingests external sources (Jira,
email), maintains a Neo4j/Chroma knowledge graph, and pushes back enrichment
(frustration/forgetting scores, stakeholder graph, RAG). The client is always
usable without the backend; the backend makes it *smarter*, not *functional*.

```
        ┌──────────────────────── THE EXTERNAL LOBE (browser) ────────────────────────┐
        │  PILOT (human)                                                               │
        │     │ capture (voice/text/gesture)                                           │
        │     ▼                                                                        │
        │  TRANSLATOR (client LLM)   ──► local Ollama (localhost:11434)                │
        │     │  scrub · parse intent · micro-actions · expand                         │
        │     ▼                                                                        │
        │  ANCHOR (pure deterministic core)                                            │
        │     ICNU+energy · FSM · schema validator · guardrails · safeStorage          │
        │     │                                                                        │
        │     ▼                                                                        │
        │  STORES (Zustand + persist → IndexedDB)  ◄── source of truth for live state  │
        │     │                                                                        │
        │     ▼                                                                        │
        │  IntelligenceService PORT  ───────────────┐                                  │
        └───────────────────────────────────────────┼──────────────────────────────────┘
                                                     │  (optional, async, never blocks UI)
                          ┌──────────────────────────▼──────────────────────────┐
                          │   BRAIN DUMP backend (FastAPI, Python)                │
                          │   ingest (Jira/email) · Extractor (Ollama) ·          │
                          │   Neo4j graph · Chroma RAG · frustration/forgetting   │
                          │   · relationship health · graph neighborhoods         │
                          └───────────────────────────────────────────────────────┘
```

---

## 2. Layer ownership (who owns what)

| Concern | Owner | Notes |
|---|---|---|
| Capture surfaces, friction metrics | **Client** | P1 zero-friction; backend irrelevant. |
| Translator (intent parse, micro-actions, expand) | **Client** | Talks to local Ollama; heuristic fallback (P5). |
| Anchor: ICNU+energy, FSM, schema validator, guardrails, scrubber | **Client** | Pure logic; the normative heart; no backend. |
| Live cognitive state (energy, focus FSM, snapshots, undo) | **Client** | Local-first authoritative (P2). |
| Persistence of live state | **Client** | IndexedDB via Zustand persist + `safeStorage`. |
| Time dial, knowledge-graph rendering, animations | **Client** | rAF physics, SVG, Framer Motion. |
| External source ingestion (Jira, email) | **Backend** | Client can't reach Jira/IMAP directly. |
| Durable knowledge graph (people/projects/tasks/sources) | **Backend** | Bigger than browser memory; cross-session. |
| Frustration / forgetting / relationship-health scoring | **Backend** | Cross-stakeholder, graph-derived. |
| RAG over a large corpus | **Backend** | Chroma; client only caches results. |
| Heavy/bulk LLM extraction | **Backend** | Server-side `instructor`+Pydantic. |

**Hard rule:** the backend is **stateless about the user's current focus**. It
never owns FSM state, energy level, or which task is "active." It supplies data
and intelligence; the client decides what the brain handles right now.

---

## 3. The seam: `IntelligenceService` port

The single integration boundary. The client depends only on this interface;
implementations are swappable. This is what makes ideas cheap to test.

```ts
interface IntelligenceService {
  // pull external/structured tasks as belt candidates
  fetchInbox(opts?: { since?: string }): Promise<CandidateTask[]>;

  // enrich a set of tasks with backend intelligence (frustration, requesters, etc.)
  enrich(taskRefs: SourceRef[]): Promise<Enrichment[]>;

  // "what is the user neglecting?" — frustration-ranked, the object-permanence feed
  forgetting(): Promise<ForgettingItem[]>;

  // per-stakeholder health for the relationships view
  relationshipHealth(): Promise<RelationshipHealth[]>;

  // a graph neighborhood around a node, for the Second Brain force graph
  graphNeighborhood(nodeId: string, depth?: number): Promise<GraphSlice>;

  // semantic search over the corpus (RAG)
  search(query: string, n?: number): Promise<SearchHit[]>;

  // push a locally-captured task/thought up for durable storage + enrichment
  push(items: PushItem[]): Promise<PushResult>;

  // connectivity probe; UI degrades gracefully if false
  isAvailable(): Promise<boolean>;
}
```

Two implementations:

- **`LocalIntelligence` (default, ships first):** pure client. `fetchInbox`
  returns local captures; `enrich`/`forgetting` use a **client-side port of the
  frustration heuristic** over local tasks (no graph, but functional);
  `graphNeighborhood` builds a graph from local tasks; `search` is keyword over
  IndexedDB. `isAvailable()` → false. **The app is fully usable on this alone.**
- **`BrainDumpIntelligence` (adapter):** hits the FastAPI endpoints from
  `01-app-spec.md §7`, mapping responses to the port's types. Adds Jira/email
  sources, the real Neo4j graph, cross-stakeholder scoring, and Chroma RAG.

Selection is runtime/config: if the backend is reachable, prefer it for
`fetchInbox/enrich/forgetting/graph/search`; **always** keep live FSM/energy/
capture local. Enrichment is **merged into** local tasks, never replaces them.

---

## 4. Data model reconciliation

The two task models differ in purpose: the client `Task` is a single-user
*cognitive item*; the backend `TaskEntity` is a *multi-stakeholder work record*.
Bridge them with an explicit mapping and a few carry-through fields.

### 4.1 Client `Task` — extended

```ts
interface Task {
  id: string;
  title: string;
  icnu_score: ICNUScore;          // 0–10 each (product canonical)
  dopamine_rating: 1|2|3|4|5;
  status: 'todo'|'active'|'done';
  start_time?: string; duration?: number; color_hex?: string;

  // --- bridge fields (present when sourced from / enriched by backend) ---
  source_ref?: SourceRef;         // { platform, source_id }  e.g. {jira, "PHX-42"}
  project?: string;
  due_date?: string;
  requesters?: string[];          // who asked (REQUESTED_BY)
  frustration?: number;           // backend stakeholder-frustration score
  context_reasons?: string[];     // "escalated to HR", "asked 3x", ...
}
```

### 4.2 Backend `TaskEntity` ↔ client `Task` mapping

| Backend (`TaskEntity`/graph) | Client `Task` | Transform |
|---|---|---|
| `description` | `title` | direct |
| `priority` (low..critical) | seeds `icnu_score.urgency` | low→2, medium→4, high→7, critical→9 (hint only) |
| `due_date` | `due_date` + urgency hint | ≤7d→+urgency per FocusScore inputs |
| `estimated_minutes` | `duration` | direct |
| `project` | `project` | direct |
| `status` (pending/in_progress/done) | `status` (todo/active/done) | pending→todo, in_progress→active, done→done |
| `assignee` | — | only `assignee=="You"` tasks become belt items |
| `frustration_score` | `frustration` + urgency boost | `urgency += min(frustration/40·10, 5)` (0–10 scale) |
| `context_reasons` | `context_reasons` | direct; some bump interest/urgency (see §5) |
| `requesters` | `requesters` | direct |
| `source_id`/`platform` | `source_ref` | direct |

**Note:** backend tasks become **candidates**; the Pilot's energy model and the
client ICNU decide surfacing. The backend never sets `dopamine_rating` (that's
the human's felt sense) and never forces `status:active`.

---

## 5. ICNU reconciliation (two definitions, one canonical)

There are deliberately two ICNU notions; keep them separate and mapped:

| | Product ICNU (client) | Backend sim ICNU |
|---|---|---|
| Scale | 0–10 per dimension | 0–1 per dimension |
| Source | Pilot input + LLM suggestion | keyword/due-date derived |
| Purpose | **runtime task surfacing** (canonical) | **validating backend logic** in the sim harness |
| Weighting | energy-profile `FocusScore` (spec §4.1) | flat sum |

- **Canonical runtime model = the External Lobe's energy-weighted FocusScore.**
  All surfacing/ranking uses it. The backend never computes the product ICNU.
- **Backend → product hints:** when a task arrives from the backend, seed its
  `icnu_score` from extracted signals (priority→urgency, tone/escalation→urgency,
  technical keywords→challenge, novel project→novelty, deliverable refs→urgency).
  These are *defaults the Pilot can override*.
- **The frustration→urgency bridge (the headline synthesis):** the backend's
  `frustration_score` and `context_reasons` map into the client's urgency (and a
  little interest), exactly the coupling proven in the simulation
  (`02-simulation-spec.md §5.2/§7`). This is what lets a boring-but-escalating
  task (Linda's security training) rise on the belt even at low energy — the
  Energy-1 profile is 80% urgency-weighted, so backend frustration directly
  governs survival-mode surfacing. **This coupling is a first-class acceptance
  test.**
- The backend sim ICNU stays where it is: a regression net for backend scoring,
  not shipped to the client.
- **Energy input must never become friction (P1 guard):** the app never *asks*
  for an energy level. It defaults to **3 (balanced)**, surfacing works without
  any input, and the slider is a one-gesture optional adjustment. An ADHD tool
  that interrogates its user about their dopamine state before helping them has
  failed its own premise.

---

## 6. Translator / LLM routing

| Use | Path | Fallback |
|---|---|---|
| Quick capture → task, micro-actions, thought expansion | **Browser → local Ollama** (`localhost:11434`) | heuristic parse (spec §5.3); always < 3s |
| Bulk source extraction (Jira description/comments, emails) | **Backend → Ollama** (`instructor` JSON mode) | structured Jira mode needs no LLM |

- **Two deterministic gates, both kept:** the client schema validator +
  type-guards (spec §4.3/4.5) gate any LLM output the *browser* consumes; the
  backend's `instructor`+Pydantic gates server-side extraction. Neither trusts
  the model.
- **PII scrubber (client, spec §5.2)** runs before any *cloud* call from the
  browser. Local Ollama calls don't strictly need it but run it anyway for
  uniformity. (Fix the spaced-card-number regex gap noted in the spec.)
- Because Ollama is localhost in this deployment, the browser and backend can
  share the same model; no cloud needed for v1.

---

## 7. Sync & enrichment contract

Local-first means the client never waits on the backend. Sync is async and
additive.

**Client → backend (`push`):**
- New/updated captures and tasks the user wants durably stored / enriched.
- Scrubbed before transit. Queued offline; flushed when `isAvailable()`.
- Backend ingests them as Sources (platform `external_lobe`), runs extraction
  (enriched mode), returns assigned `source_ref` + initial enrichment.

**Backend → client (`fetchInbox`, `enrich`, `forgetting`, etc.):**
- `fetchInbox`: Jira/email-derived tasks assigned to "You", due-soon, or
  overdue → belt candidates.
- `enrich`: per-task `frustration`, `requesters`, `context_reasons`,
  `days_overdue`, project/people neighbors.
- `forgetting`: the frustration-ranked neglected list → drives the client's
  **object-permanence** surfacing and the morning **Airlock** seed.
- `graphNeighborhood`: nodes/edges for the Second Brain graph.

**Merge policy:** backend data is merged into local tasks by `source_ref`;
client-owned fields (`dopamine_rating`, FSM state, manual ICNU edits) **win** on
conflict. Backend-owned fields (`frustration`, `requesters`) are last-writer
from the backend. Deletions are tombstoned client-side.

**Convergent concepts to unify (don't build twice):**
- **Object permanence:** backend `forgetting` (frustration-ranked) *is* the data
  feed for the client's "what are you neglecting" surfacing and the pulsing
  active-task guardrail. One concept, two layers.
- **Airlock / morning brain dump (07:00–09:00):** seed it with an overnight
  backend Jira sync (new/overdue/escalated) so the morning dump reflects reality.
- **Nudge:** backend nudge selection (`forgetting[0]`) and the client's
  energy-aware top task should agree at Energy 1–2 (both urgency-dominant); the
  client reconciles them and shows one task.

---

## 8. Second Brain graph: client render, backend substance

- The External Lobe's force-directed graph (spec §8.1) keeps its full client
  contract: importance/radius formula, gravity sim, and the **halt-when-settled/
  hidden/off-screen** performance rule.
- Data source: `LocalIntelligence` builds the graph from local tasks/projects;
  `BrainDumpIntelligence.graphNeighborhood` returns a real Neo4j slice (Person/
  Project/Task/Source nodes + ASSIGNED_TO/PART_OF/WAITING_ON/REQUESTED_BY edges).
- The client caches the last slice for offline rendering. Node click bumps local
  access counters *and* can lazy-expand via the backend when online.

---

## 9. Pragmatic backend capability review

What the existing/spec'd backend can actually do for this frontend — and where
the seams are.

### 9.1 Feature × backend relevance

| External Lobe feature | Backend role | Verdict |
|---|---|---|
| Capture (lightning/voice/cmd/gesture), friction metrics | none | **client-only** |
| ICNU+energy surfacing, FocusScore, wedge expansion | none (provides hints) | **client-only** (hints from backend) |
| FSM, guardrails (body double, anti-paralysis, ember, lens, resumption, snapshots, decay) | none | **client-only** |
| Schema validator / type guards / scrubber | mirrored server-side via Pydantic | **client-only** (BE has its own) |
| Time dial rendering | none | **client-only** |
| Quick-capture Translator | local Ollama (shared) | **client-only** |
| Inbox of real tasks (Jira) | ingest + map | **backend-enhanced** (stub locally) |
| Frustration / "what you're forgetting" | graph-derived scoring | **backend-enhanced** (heuristic stub) |
| Relationship health | REQUESTED_BY rollups | **backend-enhanced** |
| Second Brain graph substance | Neo4j neighborhoods | **backend-enhanced** (local graph stub) |
| RAG search over corpus | Chroma | **backend-enhanced** (keyword stub) |
| Bulk/source LLM extraction + tone | server Extractor | **backend-required** for external sources |

**Takeaway:** ~everything the *experience* needs is client-only or
stub-able. The backend adds **breadth of data** and **cross-stakeholder
intelligence** — exactly what a single browser can't synthesize. Nothing in the
backend blocks building and demoing the full cockpit first.

### 9.2 Mismatches to resolve

| Mismatch | Resolution |
|---|---|
| Backend task = multi-person work record; client task = single-user cognitive item | Adapter in §4.2; only `assignee==You` + due/overdue/forgetting become belt items. |
| Two ICNU scales/definitions | §5: product 0–10 energy-weighted is canonical; backend gives hints + frustration bridge; sim ICNU is validation-only. |
| Backend assumes Neo4j/Chroma/Docker; client is local-first/offline | Backend is *optional*; `LocalIntelligence` covers offline; backend merged additively. |
| Backend `today` passed in for determinism; client uses real clock | Client injects `now` in pure logic (already required by spec); sync passes explicit dates. |
| **Frustration scoring leans on tone signals (escalation, follow-ups, temperature) that Jira *structured* mode doesn't carry** — only the sim's scripted agents and (later) email provide them | At P5, run Jira **comments** through enriched mode to recover follow-ups/tone, *or* accept that real-data scores rest on mentions + days_overdue + priority and calibrate the headline demo accordingly. Decide at P5 pre-flight (carry-forward filed). The sim remains the full-signal validation of the formula either way. |
| Backend has no "energy"/"focus state" | Stays that way — client-only; optionally logged as a signal, never as logic. |
| Earlier htmx/FastAPI-as-UI assumption | FastAPI is now a **JSON intelligence API only**; no server-rendered UI. Drop `api/ui.py`, templates, Playwright-against-htmx from `01/03`. |

### 9.3 What the backend must NOT do
Own focus/energy/FSM state; render UI; block the client; require connectivity
for core use; or be the source of truth for live cognitive state.

---

## 10. Privacy, offline, accessibility (carried from both specs)

- **Local-first (P2/P5):** full function offline via `LocalIntelligence` +
  heuristic Translator. Backend strictly additive.
- **Privacy (P3):** local Ollama preferred; client PII scrubber gates any cloud
  call; `push` payloads scrubbed; backend keeps data local in Neo4j/Chroma.
- **Accessibility:** keyboard-operable; ARIA on interactive SVG; never
  color-only urgency (pair with text/weight) — per External Lobe §12.

---

## 11. Testability of the integration

- The **port boundary** lets the entire frontend be built and tested against
  `LocalIntelligence` and a **stubbed `BrainDumpIntelligence`** (recorded JSON
  fixtures) — no live backend needed (Vitest/jsdom).
- The **backend** keeps its own test spine (`02-simulation-spec.md`): in-memory
  store contract tests, the 52-week passive simulation (query coverage), and the
  ADHD cognitive sim (now reframed as *backend scoring* validation, distinct from
  the product runtime).
- **Contract tests on the seam:** a shared fixture set asserts both
  `LocalIntelligence` and `BrainDumpIntelligence` satisfy the `IntelligenceService`
  types and invariants (e.g. `forgetting` is frustration-descending).
- **The frustration→urgency coupling** gets an end-to-end test: a high-frustration
  backend task surfaces at Energy 1 above an interesting-but-non-urgent task.

---

## 12. Open decisions for your review

1. **Repo layout:** one monorepo (`/app` React, `/backend` Python, `/specs`) vs
   two repos. Monorepo recommended for co-development + shared fixtures.
2. **Sync transport:** simple REST polling (recommended v1) vs SSE/websocket push
   for live enrichment.
3. **Auth/multi-device:** out of scope for v1 (single local user)? The
   local-first model assumes one user; multi-device sync is a later concern.
4. **Energy as a backend signal:** log energy/focus telemetry to the backend for
   future analytics, or keep it strictly client? (Default: client-only.)
5. **Backend ADHD sim:** keep as backend-logic regression only, or also mine it
   for seeded demo data the frontend can load offline? (Recommended: also export
   a seed fixture — instant rich demo data with no services.)
