# CLAUDE.md

Loaded as context for every Claude Code session in this project. Read it at the
start of every session. It captures the decisions, conventions, and constraints
that persist across the entire build.

For the full design: `specs/00-overview.md` → `05`. For the daily/phase rhythm:
`docs/working_pattern.md`.

---

## Part I — Behavioral Guidelines

These bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think before coding
**Don't assume. Don't hide confusion. Surface tradeoffs.**
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what's confusing, ask.

### 2. Simplicity first
**Minimum code that solves the problem. Nothing speculative.**
- No features beyond what was asked. No abstractions for single-use code.
- No "flexibility"/"configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you wrote 200 lines and it could be 50, rewrite it. Ask: "Would a senior
  engineer call this overcomplicated?" If yes, simplify.

### 3. Surgical changes
**Touch only what you must. Clean up only your own mess.**
- Don't "improve" adjacent code, comments, or formatting; match existing style.
- Don't refactor what isn't broken. Notice unrelated dead code → mention it,
  don't delete it.
- Remove imports/vars/functions **your** changes orphaned; leave pre-existing
  dead code alone unless asked.
- Test: every changed line traces directly to the request.

### 4. Goal-driven execution
**Define success criteria. Loop until verified.**
- "Add validation" → "write tests for invalid inputs, then make them pass."
- "Fix the bug" → "write a test reproducing it, then make it pass."
- "Refactor X" → "tests pass before and after."
- For multi-step work, state a brief plan with a `verify:` check per step. Strong
  criteria let you loop independently; weak criteria ("make it work") force
  churn.

**Working if:** fewer unnecessary diff lines, fewer rewrites from
overcomplication, clarifying questions *before* implementation not after.

---

## Part II — Project at a Glance

**Brain Dump × The External Lobe** — a local-first ADHD executive-function
cockpit. One product, two halves joined at a single seam:

- **The External Lobe** (frontend) — a Vite + React local-first **Triple-Engine**
  app (Tauri desktop shell; ADR 0008): **Pilot** (human capture) → **Translator**
  (LLM structuring) → **Anchor**
  (deterministic core: ICNU+energy, FSM, schema validation, guardrails). Fully
  usable offline.
- **Brain Dump** (backend) — an *optional* Python intelligence service: ingests
  external sources (Jira first), maintains a Neo4j/Chroma knowledge graph, and
  pushes back enrichment (frustration/forgetting scores, stakeholder graph, RAG).

The seam is the **`IntelligenceService` port** (`specs/04 §3`). The client always
runs on a local stub; the backend is a drop-in adapter that deepens the data. The
backend makes the app *smarter*, never *functional*.

Source-of-truth docs:
- Frontend behavior → *The External Lobe — Specification* (the Triple-Engine spec).
- Backend internals → `specs/01-app-spec.md`, `specs/02-simulation-spec.md`.
- The seam → `specs/04-integrated-design.md`.
- The roadmap → `specs/05-iterative-plan.md` (phases **P0–P8**).

The legacy Python prototype (root `main.py`, `core/`, `simulation/`, …) is
**reference only** until P0 scaffolds the monorepo; don't extend it.

## How this project uses Claude Code

The build is structured as **phases P0–P8** (`specs/05`). Each phase is a
*hypothesis + a runnable demo gate*, not a feature dump. A session typically:
1. ingests the relevant specs + this CLAUDE.md + the current phase;
2. works the TDD loop (red → green → refactor → commit per coherent slice);
3. ends the phase with a retrospective (`docs/working_pattern.md`).

Phases assume earlier phases are complete. Don't redo prior work; don't skip
ahead. If a phase seems wrong given earlier ones, **ask before improvising**
(Part I §1).

**Exploration is cheap by design:** untested ideas go through the **spike lane**
(`docs/working_pattern.md`) — a timeboxed `spike/<topic>` branch exempt from the
gates, whose output is knowledge + a task brief, never merged code. Hand-off
sized work units live in `specs/tasks/` (one brief = one small-context session).

---

## Part III — Architecture

### The Triple Engine + layer boundaries (frontend)

Respect these boundaries — they are the testability gradient:

- **Pure logic** (no React, no DOM, time only via injected `now`): ICNU engine,
  FSM reducer, schema validator, type guards, scrubber, SVG math, scoring. →
  unit-testable in isolation; target ~100% branch coverage.
- **Stores** (Zustand + persist): hold state, expose actions that call pure
  logic. → tested via `store.getState()` with mocked `safeStorage`.
- **Effects/hooks** (React + browser APIs): timers, visibility, speech, storage.
  → tested with fake timers + jsdom + feature-detect mocks.
- **Components** (presentational + container): render state, dispatch actions.

### The seam (the one integration boundary)

The client depends only on the **`IntelligenceService`** interface. Two impls:
`LocalIntelligence` (default, offline, heuristic) and `BrainDumpIntelligence`
(adapter over the FastAPI JSON API). Enrichment is **merged into** local tasks,
never replaces them; client-owned fields win on conflict (`specs/04 §7`).

### Separation rules — **enforced in CI**

1. `app/` must **not** import the backend simulation (`backend/sim/`).
2. `app/` reaches the backend **only** through `BrainDumpIntelligence`.
   Components/stores/hooks never `fetch` the backend directly.
3. `backend/brain_dump/` must not import `backend/sim/`.
4. `backend/sim/` must not import `neo4j`, `chromadb`, `openai`, `instructor`,
   FastAPI, or any connector — only the shared domain models + Store Protocol.
5. The backend is **stateless about live cognitive state** — it never owns the
   FSM, energy level, or which task is "active."

If a phase spec implies crossing one of these, that's a bug in the spec; flag it.

---

## Part IV — Stack (non-negotiable)

If a phase spec implies a different choice, flag it rather than switching.

### Frontend (`/app`)
- **Framework**: Vite + React + TypeScript (local-first SPA). Not Next, not Vue,
  not CRA — host-agnostic so it runs in a browser (dev) or a Tauri webview.
- **Shell (ADR 0008)**: packaged as a **Tauri desktop app** — always-on-top
  corner widget + global hotkey capture + system tray + a full-view window. The
  app renders **two surfaces** (compact widget / full view); capture is
  *summoned*, never navigated to. Tauri lands ~P3.5; build host-agnostic until.
- **Styling**: Tailwind. Custom CSS only when unavoidable.
- **State**: Zustand + `persist` middleware → localStorage (v1; IndexedDB later
  behind the same adapter — ADR 0006) **via the `safeStorage` wrapper only**.
- **Animation**: Framer Motion (spring configs per the spec §10).
- **Unit/component tests**: Vitest + jsdom + `@testing-library/react` +
  `jest-dom`. **E2E**: Playwright (stubbed LLM + stubbed backend).
- **LLM**: a **local OpenAI-compatible server** (Ollama *or* llama.cpp — chosen
  by config, never hardcoded; see ADR 0005) reached from the browser Translator;
  heuristic fallback always present.
- **Scripts**: `npm run test | test:watch | lint | typecheck | build`.

### Backend (`/backend`)
- **API**: FastAPI + Pydantic v2 — **JSON intelligence API only** (no
  server-rendered UI; the earlier htmx plan is superseded by `specs/04`).
- **LLM extraction**: `instructor` over a **local OpenAI-compatible server**
  (Ollama/llama.cpp, config-selected — ADR 0005) in **JSON mode**
  (`instructor.Mode.JSON`). Provider chosen via `LLM_BASE_URL`/`LLM_MODEL`, never
  hardcoded. Azure/Bedrock branches kept as deferred stubs.
- **Graph**: Neo4j. **Vector**: ChromaDB. Both via Docker Compose.
- **Source connector (v1)**: Jira (structured + enriched modes). Outlook/Slack
  deferred behind the `Connector` protocol.
- **Deps**: `uv`. **Lint/format**: ruff. **Types**: mypy. **Tests**: pytest.

### Shared
- **Monorepo**: `/app`, `/backend`, `/specs`, `/fixtures` (recorded JSON the FE
  adapter tests and BE share).
- **Stores both sides implement a contract**: backend `GraphStoreProtocol` has an
  `InMemoryGraphStore` (sim/tests) + `Neo4jGraphStore` (prod), kept in lockstep
  by one contract-test suite.

---

## Part V — Code style

### TypeScript (frontend)
- Strict mode. **No `any`. No `as unknown as`.** Narrow LLM/backend output with
  runtime **type guards** at the boundary (`specs` §4.5) before typed use.
- Pure logic takes `now: number` as a parameter; never call `Date.now()` /
  `setInterval` inside it. Effects own the clock.
- Prefer pure functions; isolate side effects (storage, fetch, speech) in
  hooks/stores. Components stay thin (render + dispatch).
- Functional components + hooks. Named exports. Co-locate tests as
  `*.test.ts(x)`.

### Python (backend)
- Python 3.11+ syntax: `match`, `|` unions, `StrEnum`, `pathlib.Path`,
  timezone-aware `datetime` (UTC; never naive).
- Type hints on all signatures incl. private helpers. Docstrings on public
  functions/classes. Line length 100. f-strings only.
- Scoring/query ranking lives **above** the Store Protocol as pure functions over
  store rows — written once, run against in-memory (tests) and Neo4j (prod).
- All time-dependent logic takes `today`/timestamps as parameters (determinism).

---

## Part VI — Naming

- React components `PascalCase`; hooks `useThing`; pure-logic modules
  `kebab-case.ts` (`icnu-engine.ts`, `svg-math.ts`).
- Zustand stores `useXStore`; persist keys namespaced
  (`external-lobe-anchor`, `-explore`, `-undo`).
- Python: modules/functions `lower_snake_case`; classes `PascalCase`; constants
  `UPPER_SNAKE_CASE`. Test files `test_<thing>.py` / `<thing>.test.ts`.
- Domain terms come from the specs glossary (`specs/00 §6`): Source, Extraction,
  dual-write, ICNU, frustration score, object permanence, Store Protocol,
  Pilot/Translator/Anchor. Don't invent synonyms.

---

## Part VII — Determinism & the LLM boundary (project-critical)

These are the recurring failure modes for this stack. Treat them as hard rules.

- **Inject time.** No real clock/timer in pure logic. Tests use fake timers.
- **Stub the model.** No Translator/adapter test hits a real LLM or the live
  backend; use recorded fixtures. Real models only in opt-in `e2e`.
- **Trust nothing from the LLM.** Frontend: schema validator + type guards gate
  any model output before it reaches state. Backend: `instructor`+Pydantic gate
  extraction. Unknown tool / unknown field → flag for review, don't write.
- **Two ICNU models, kept apart.** The product's **0–10 energy-weighted
  FocusScore is canonical** (client). The backend's 0–1 sim ICNU is
  *backend-logic validation only* and is **never shipped to the client**. The
  backend contributes *hints* + the **frustration→urgency bridge** (`specs/04 §5`).
- **safeStorage always.** Every localStorage/IndexedDB access goes through the
  wrapper (SSR, quota, disabled, corrupt JSON).
- **rAF must halt.** Any animation/simulation loop pauses when settled, hidden,
  or off-screen, and wakes on interaction. Assert the halt in tests.

---

## Part VIII — Tests & Definition of Done

### Test taxonomy
- **Frontend**: unit (Vitest, node) → component (Testing Library, jsdom, incl. a
  basic a11y check) → e2e (Playwright, stubbed).
- **Backend**: `unit` → `contract` (in-memory store; same suite later runs vs
  Neo4j under `integration`) → `integration` (Docker) → `e2e` (real Ollama, opt-in).
- Markers separate fast lanes from gated lanes; CI runs fast lanes on every push.

### A phase is **Done** when
1. Every in-scope acceptance criterion has a test.
2. The phase's **demo hypothesis runs** — backend **off** (where applicable) and
   **on** — and the standing **Manual Acceptance** checklist
   (`docs/manual_acceptance.md`) passes with recorded evidence in the retro.
3. `typecheck` + `lint` clean; pure-logic near 100% branch coverage; the relevant
   simulation/contract gate still green (no regression).
4. Separation checks (app↔sim, app↔backend, sim↔adapters) pass.
5. Discrete commits per logical slice, capped by a `chore: Phase N complete`
   marker.
6. The phase retrospective is written (`docs/working_pattern.md`).

Don't move to P(N+1) until P(N) is fully done. Don't ship "mostly working"
phases — they compound.

---

## Part IX — Commits

- **Conventional Commits**: `type(scope): subject`. Types: `feat fix refactor
  docs test chore build ci perf`. Scopes (examples): `anchor translator capture
  dial graph stores hooks ui api jira adapter sim specs build ci`.
- Subject: imperative, lowercase, no trailing period, ≤72 chars. Good:
  `feat(anchor): add energy-weighted FocusScore`. Bad: `Updated stuff.`
- One commit = one logical change. If the subject needs "and," split it. Don't
  bundle unrelated changes; don't `git add .` blindly — stage so each diff
  matches its message.
- **Never commit broken code** on the working branch. `wip:` is fine on feature
  branches only.
- Branch per phase (`phase-NN-<descriptor>`) merged to `main` at phase
  boundaries; `chore: Phase N complete` is what `git log --grep="Phase"`
  surfaces. (Within a managed remote session, follow that session's branch
  instructions.)
- **No Claude/AI attribution** in commit messages. Don't amend/force-push without
  confirming.

---

## Part X — Common pitfalls (will trip you up)

- **Tauri webview differences.** macOS uses WKWebView (no Web Speech API → voice
  capture degrades to text; feature-detect). It's a static SPA — no SSR, no
  server components. Always-on-top, global hotkey, tray, and multi-window live in
  the **Tauri shell**, not the React app; the app just renders the compact/full
  surfaces. From the webview, reach the local LLM/backend via Tauri's HTTP
  capability to sidestep CORS.
- **jsdom lacks browser APIs.** `SpeechRecognition`, `AudioContext`,
  `IntersectionObserver`, `visibilityState` aren't in jsdom — feature-detect in
  code, mock in tests, assert graceful absence.
- **rAF runaway.** Force-directed graph must stop when velocity² < threshold /
  hidden / off-screen. Test the stop conditions explicitly.
- **In-memory ↔ Neo4j drift.** The backend's two stores must pass the *same*
  contract suite. If a query result differs, that's a bug, not a backend quirk.
- **JSON mode, not tool-calling.** Local model tool-call support is inconsistent
  across servers; use `instructor.Mode.JSON` (works on Ollama and llama.cpp alike).
  The structured Jira mode needs no LLM at all — prefer it for deterministic tests.
- **Port-shape drift.** When the backend response changes, update the recorded
  fixtures *and* the `IntelligenceService` types together, or the FE/BE silently
  diverge. The seam contract test is the guard.
- **localStorage quota/SSR/corrupt JSON.** Only reproducible through
  `safeStorage`; never touch storage directly.
- **PII regex gap.** The card-number pattern misses spaced groups
  (`4532 1488 …`) — use `[-\s]?` separators (carry-over fix from the spec).
- **Determinism leaks.** A real clock or unseeded RNG in logic makes tests flaky
  and the sim non-reproducible. Inject both.

---

## Part XI — Out of scope for v1 (don't build it even if it seems easy)

- Outlook / Slack connectors; Azure / Bedrock LLM backends (interfaces preserved,
  implementations deferred).
- Server-rendered UI / htmx (superseded — FastAPI is JSON-only).
- Multi-user auth, RBAC, multi-device sync (single local user assumed).
- Cloud LLM by default (local OpenAI-compatible server first; cloud only behind
  the PII scrubber if ever enabled).
- Real-time webs/SSE push (REST polling for v1 unless a phase says otherwise).

- **Generalizing for hypothetical other users.** No configurability, theming, or
  abstraction whose only justification is "someone else might want it." Build the
  one thing *you* want; selling it later is downstream of it being great for you.
- **The spec's UI variation menus.** The External Lobe spec lists alternatives
  (Radial/Linear/Stacked time-dial; Split/Notebook/Terminal second brain; four
  capture surfaces). Build **one** of each that earns daily use; the others are
  A/B research luxuries, not N=1 needs. Add a variation only if daily use demands
  it.

If a feature seems useful but isn't in the current phase, it's out of scope.

---

## Part XII — When you're uncertain

If a phase spec is ambiguous, contradicts an earlier phase, or implies a stack
choice not listed here:
1. Don't improvise.
2. Surface the ambiguity in clear terms.
3. Propose 1–2 specific resolutions with tradeoffs.
4. Wait for direction.

This costs less than discovering at P7 that P2 made a wrong choice.

---

## Part XIII — The north star & what we value

**Primary success criterion (the one that matters):** the builder uses this
**day to day** and it measurably improves their **responsiveness** (not dropping
balls with colleagues/stakeholders) and **productivity** (starting and finishing
real work). It is a tool for **one user — you**. If it later helps others or
becomes sellable, that is a *welcome side effect of being genuinely good for the
builder*, never a design input now. Build for N=1 (ADR 0007).

Every feature is judged by one question: **"will I open this and does it make me
better at my job this week?"** A beautiful feature that goes unused is a failure,
not a partial win.

The two halves of the goal map to different parts of the system — keep both in
view:
- **Productivity / initiation** → capture + energy-ranked surfacing + the focus
  loop (the Anchor cockpit). Lands P1–P3, no backend.
- **Responsiveness / not dropping balls** → surfacing what you owe people and
  when (forgetting, nudge, relationship health). This needs *commitments* in the
  system — capture them locally from P2 (see specs/05) so this value arrives
  before the Jira backend does.

**Value:** clarity; <100ms interactions that never block on network/LLM; full
offline function; honest separation between deterministic Anchor logic and
LLM suggestion; the frustration→surfacing coupling actually working.

**Don't value:** cleverness, novel UI for its own sake, abstractions without a
second caller, generalizing for hypothetical *other* users, anything that makes
the app depend on the backend to function.

---

## Part XIV — Working pattern (phase retrospectives + pre-flight)

This project uses an end-of-phase retrospective + start-of-phase pre-flight to
catch pattern bugs early and prevent foundation drift. Full discipline,
templates, bug-class reference, and the "independent reviewer" prompt are in
**`docs/working_pattern.md`** — read it before your first retrospective.

In brief:
- **End of each phase**: write `docs/retrospectives/phase_NN.md` (bugs +
  *cumulative bug-class counts* + tests added + new integration points +
  decisions + carry-forward + the independent-reviewer questions). Update
  `docs/carry_forward.md`.
- **Start of each phase**: run the pre-flight — fast test lanes green, separation
  checks pass, review cumulative bug-class counts (any class with 2+ occurrences
  gets a structural fix *before* new feature work), and read carry-forward items
  targeting this phase.
- **Before approving a phase**: run the standing **Manual Acceptance** checklist
  (`docs/manual_acceptance.md`) and paste the sign-off (with observed evidence)
  into the retro. A phase isn't approved without it.
- A bug class with three occurrences is a signal to fix the design, not patch
  again. "Tests pass / looks right per inspection" is **not** verification for
  runtime behavior (hooks under fake timers, components with live data, the live
  backend adapter, rAF halting) — require exercised-and-observed evidence.
