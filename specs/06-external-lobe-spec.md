# The External Lobe — Specification

> **Status:** canonical frontend behavioral spec (referenced by `CLAUDE.md` Part
> II and the `specs/tasks/` briefs). Committed verbatim from the source document.
> **Amendments that override this text where they conflict:**
> - **Determinism (CLAUDE.md Part VII):** pure logic never calls `Date.now()` —
>   the FSM reducer takes `at` on every event (see `specs/tasks/P1-M3-fsm.md`).
> - **Persistence (ADR 0006):** localStorage first via `safeStorage`; IndexedDB
>   later behind the same adapter.
> - **N=1 scope (ADR 0007, CLAUDE.md Part XI):** build **one** of each UI
>   surface; the variation menus (§7.2, §8.2, multiple capture surfaces) are
>   deferred. Energy input is optional and never prompted (specs/04 §5). The
>   Airlock must have a skip affordance (docs/manual_acceptance.md).
> - **LLM provider (ADR 0005):** "ollama"/"llama3.1" reads as "any local
>   OpenAI-compatible server, config-selected."

> A productivity system for ADHD executive-function support, built as a
> **Triple-Engine** circuit: **Pilot** (human intent) → **Translator** (LLM
> structuring) → **Anchor** (deterministic code). This document is the
> source-of-truth behavioral specification, written so the system can be
> reimplemented test-first. Every numeric constant, formula, schema, and state
> transition below is normative — a conforming implementation must reproduce it.

---

## 1. Product Vision & Principles

The system replaces "list and checkbox" task management with a **cognitive
conveyor belt** that asks *"what can my brain handle right now?"* instead of
*"what do I have to do?"*

**Design principles (non-negotiable):**

| # | Principle | Implication |
|---|-----------|-------------|
| P1 | **Zero-friction input** | Capture must complete in < 3s; any path > 5s is logged as a UX defect. |
| P2 | **Local-first** | All state persists to `localStorage`/IndexedDB. UI never blocks on network/LLM. Target < 100 ms interaction latency. |
| P3 | **Deterministic gate** | The LLM may *suggest* but never *commit*. All LLM output passes schema validation before reaching state. |
| P4 | **State-of-mind over to-do** | Task surfacing is driven by an energy/dopamine model, not static priority. |
| P5 | **Graceful degradation** | Every LLM-backed feature has a deterministic fallback so the app is fully usable offline. |
| P6 | **Calm, peripheral cues** | Urgency is signalled by color/animation at the periphery, never by alarms or guilt. |

---

## 2. Architecture: The Triple Engine

```
┌─────────────── PILOT (human) ───────────────┐
│ Intent · divergence · creative spark         │
│ Voice / text / gesture  ──►  raw string      │
└───────────────────────┬──────────────────────┘
                        │ CAPTURE
                        ▼
┌─────────────── TRANSLATOR (LLM) ─────────────┐
│ Intent parsing · sub-tasking · RAG           │
│ raw string  ──►  candidate structured object │
│ Sub-modules: Scrubber, Intent Parser,        │
│ Micro-Action Generator, Thought Expander     │
└───────────────────────┬──────────────────────┘
                        │ TRANSFORM
                        ▼
┌─────────────── ANCHOR (deterministic) ───────┐
│ FSM · Schema Validator · Guardrails · Stores  │
│ candidate object ──► validated state + UI     │
└───────────────────────────────────────────────┘
                        │ LOCK
                        ▼
                  Persisted state → UI
```

**Layer boundaries (must be respected for testability):**

- **Pure logic** (no React, no DOM, no time except injected): ICNU engine, FSM
  reducer, schema validator, type guards, scrubber, SVG math. → unit-testable in
  isolation.
- **Stores** (Zustand + persist): hold state, expose actions that call pure
  logic. → testable with a mock storage.
- **Effects/hooks** (React + browser APIs): timers, visibility, speech, storage.
  → testable with fake timers + jsdom.
- **Components** (presentational + container): render state, dispatch actions.

---

## 3. Core Data Model

```ts
interface ICNUScore {
  interest: number;   // 0–10, hyper-focus magnet
  challenge: number;  // 0–10, problem-solving complexity
  novelty: number;    // 0–10, new project / tech stack
  urgency: number;    // 0–10, deadline proximity
}

interface Task {
  id: string;                       // uuid
  title: string;
  icnu_score: ICNUScore;
  dopamine_rating: 1 | 2 | 3 | 4 | 5;
  status: 'todo' | 'active' | 'done';
  start_time?: string;              // ISO 8601
  duration?: number;                // minutes
  color_hex?: string;               // optional; else derived from urgency
}

interface CapturedThought {
  id: string;
  text: string;
  captured_at: string;              // ISO 8601
  time_to_capture_ms: number;       // friction metric
}

interface MentalSnapshot {
  id: string;
  text: string;                     // "Working on: <title>"
  taskId: string | null;
  at: number;                       // epoch ms
}

interface ReviewFlag {
  id: string;
  source: 'llm_output' | 'schema_violation' | 'unknown_tool';
  message: string;
  data: Record<string, unknown>;
  at: number;
  resolved: boolean;
}
```

> **Rebuild amendment (ADR 0007 / specs/05):** `Task` additionally carries
> optional commitment fields — `requester?: string` and a promised/due date — so
> the responsiveness loop (forgetting/nudge) works offline from P3. The seam
> bridge fields are specified in specs/04 §4.1.

---

## 4. ANCHOR Engine (deterministic core)

### 4.1 ICNU Weighting Engine

**Focus Score formula:**

```
FocusScore(icnu, energy) = clamp01( (wI·I + wC·C + wN·N + wU·U) / 10 )
```

where weights depend on the **energy level** (1–5) and `clamp01(x) = min(1, max(0, x))`.

**Energy weight profiles** (each row sums to 1.0):

| Energy | wI (Interest) | wC (Challenge) | wN (Novelty) | wU (Urgency) | Mode |
|:------:|:----:|:----:|:----:|:----:|------|
| 1 | 0.10 | 0.05 | 0.05 | **0.80** | Survival |
| 2 | 0.15 | 0.10 | 0.10 | **0.65** | Low battery |
| 3 | 0.25 | 0.25 | 0.20 | 0.30 | Balanced |
| 4 | **0.35** | 0.30 | 0.20 | 0.15 | High gear |
| 5 | **0.35** | 0.30 | 0.25 | 0.10 | Hyperfocus |

**`rankTasks(tasks, energy)`** → returns tasks with `focusScore` attached, sorted
**descending**. Stable for equal scores is not required.

**`filterByEnergy(tasks, energy)`:**
- Energy ≤ 2: keep tasks where `urgency ≥ 5 AND challenge ≤ 6`.
- Energy == 3: keep all.
- Energy ≥ 4: keep tasks where `interest ≥ 5 OR challenge ≥ 5`.

**`wedgeExpansion(focusScore)`** → `0.5 + focusScore² · 1.5`, range **[0.5, 2.0]**.
Ease-in (quadratic): score 0 → 0.5×, score 0.5 → 0.875×, score 1 → 2.0×.

**Acceptance tests:**
- All-zero ICNU → score 0 at every energy.
- All-ten ICNU → score 1 (±1e-9) at every energy.
- Energy 1: urgency-only task outranks interest-only task; ≈ 0.8.
- Energy 5: interest-only task outranks urgency-only task.
- Score always within [0, 1] for the full 0–10 grid.
- Each weight profile sums to 1.0 (±1e-5).

### 4.2 Finite State Machine

**States:** `IDLE`, `CAPTURE_MODE`, `TASK_INITIATION`, `DEEP_FOCUS`, `BREAK`,
`REVIEW`, `BRAIN_DUMP`.

**Context:**

```ts
interface FSMContext {
  state: FSMState;
  activeTaskId: string | null;
  focusStartedAt: number | null;
  focusMinutes: number;
  initiationStartedAt: number | null;
  breakStartedAt: number | null;
  transitionHistory: { from; to; event; at }[]; // capped at 50
}
```

**Transition table** (source state → event → target):

| From | Event | To |
|------|-------|----|
| IDLE | START_CAPTURE | CAPTURE_MODE |
| IDLE | BEGIN_TASK | TASK_INITIATION |
| IDLE | START_REVIEW | REVIEW |
| IDLE | AIRLOCK_TRIGGER | BRAIN_DUMP |
| CAPTURE_MODE | CAPTURE_COMPLETE | IDLE |
| CAPTURE_MODE | RESET | IDLE |
| TASK_INITIATION | FOCUS_ACHIEVED | DEEP_FOCUS |
| TASK_INITIATION | ANTI_PARALYSIS | TASK_INITIATION (self) |
| TASK_INITIATION | START_CAPTURE | CAPTURE_MODE |
| TASK_INITIATION | RESET | IDLE |
| DEEP_FOCUS | FOCUS_BROKEN | IDLE |
| DEEP_FOCUS | TAKE_BREAK | BREAK |
| DEEP_FOCUS | START_CAPTURE | CAPTURE_MODE |
| DEEP_FOCUS | RESET | IDLE |
| BREAK | BREAK_OVER | IDLE |
| BREAK | START_CAPTURE | CAPTURE_MODE |
| BREAK | RESET | IDLE |
| REVIEW | REVIEW_COMPLETE | IDLE |
| REVIEW | START_CAPTURE | CAPTURE_MODE |
| REVIEW | RESET | IDLE |
| BRAIN_DUMP | CAPTURE_COMPLETE | IDLE |
| BRAIN_DUMP | RESET | IDLE |

**Reducer contract (`transition(ctx, event)`):**
- Pure function. ~~Must not read wall-clock except via `Date.now()`~~ →
  **amended:** every event carries `at: number`; the reducer never reads a clock
  (see header note + `specs/tasks/P1-M3-fsm.md`).
- Invalid transition → return the **same reference** unchanged + `console.warn`.
- Side-effect context updates:
  - `BEGIN_TASK`: set `activeTaskId`, `initiationStartedAt = now`, `focusStartedAt = null`.
  - `FOCUS_ACHIEVED`: `focusStartedAt = now`, `initiationStartedAt = null`.
  - `FOCUS_BROKEN`: if focusing, add `floor((now − focusStartedAt)/60000)` to `focusMinutes`; clear `focusStartedAt`.
  - `TAKE_BREAK`: accrue focus minutes as above; `breakStartedAt = now`.
  - `BREAK_OVER`: clear `breakStartedAt`.
  - `CAPTURE_COMPLETE`: if `event.taskId`, set `activeTaskId`.
  - `RESET`: clear all task/timer fields.
- `transitionHistory` keeps the last 50 entries (slice before push).

**`shouldTriggerAntiParalysis(ctx)`** → true iff `state == TASK_INITIATION` AND
`initiationStartedAt` set AND `now − initiationStartedAt > 20 min`.

### 4.3 Schema Validator ("Hallucination Filter")

`validateLLMOutput(schemaName, data) → { valid, errors[], flaggedForReview, sanitized? }`

**Schemas:**

*task*
| field | type | constraints |
|-------|------|-------------|
| title | string | **required** |
| project_id | string | — |
| priority_weight | number | 0–100 |
| estimated_minutes | number | 1–480 |
| icnu_interest/challenge/novelty/urgency | number | 0–10 each |
| dopamine_rating | number | 1–5, enum {1,2,3,4,5} |
| status | string | enum {todo, active, done} |
| suggested_tools | array | each must be a **Known Tool** |

*micro_action*: `text`(string,req), `estimated_minutes`(1–30), `order`(≥0).
*rag_result*: `summary`(string,req), `confidence`(0–1), `source_ids`(array), `reasoning`(string).

**Known Tools registry** (case-insensitive): vscode, terminal, browser, figma,
notion, slack, github, linear, calendar, email, obsidian, arc, iterm, cursor,
postman, docker, postgres, sqlite. Extensible via `registerTool`.

**Rules:**
- Missing required, wrong type, out-of-range, enum miss → `valid=false` with a descriptive error.
- **Unknown field** present → error + `flaggedForReview=true` (hallucination signal).
- **Unknown tool** in `suggested_tools` → error + `flaggedForReview=true`.
- Unknown schema name → `valid=false`, `flaggedForReview=true`.
- `sanitized` is returned only when `valid` — contains known fields, numbers clamped to range.

### 4.4 Behavioral Guardrails

| Guardrail | Trigger | Behavior | Constant |
|-----------|---------|----------|----------|
| **Body Double** | Tab hidden during DEEP_FOCUS, away > 3s | Gentle "welcome back" nudge on return | away threshold 3 s |
| **Anti-Paralysis** | > 20 min in TASK_INITIATION | Surface 3 trivial micro-entry actions | 20 min; checked every 30 s |
| **Visual Decay** | Task completed | Opacity fades `exp(−hoursAgo/8)`, floor 0.15, hidden after 48 h | floor 0.15; 24 h to floor; 48 h cutoff |
| **Mental Snapshot** | Every 15 min during DEEP_FOCUS/TASK_INITIATION | Append breadcrumb snapshot | 15 min |
| **Break Suggestion** | Every 25 min of continuous focus | Suggest a break | 25 min (Pomodoro) |

`completedTaskOpacity(completedAt)`: `≤0h → 1`; `≥24h → 0.15`; else `max(0.15, exp(−h/8))`.
`generateAntiParalysisEntries(title)` → exactly 3 entries (1, 2, 5 min estimates), deterministic, no LLM.

### 4.5 Type Guards

`isParsedIntent`, `isMicroAction`, `isExpandedThought` — runtime narrowing applied
to LLM output **after** schema validation, **before** typed use. Reject
null/undefined/primitives and malformed arrays. No `as unknown as` casts permitted.

---

## 5. TRANSLATOR Engine (LLM orchestration)

### 5.1 LLM Client

Default config: provider `ollama`, `http://localhost:11434`, model `llama3.1`,
`maxRetries: 2`, `timeoutMs: 30000`. Cloud provider optional.
*(Amended by ADR 0005: any local OpenAI-compatible server, config-selected.)*

**Contract:**
- For **cloud** provider, scrub PII from prompt first (§5.2).
- Attempt → parse JSON (extract first `{...}` block) → schema-validate if requested.
- On local-server failure (first attempt), fall back to cloud if configured.
- Exponential backoff between retries: `1000 · 2^attempt` ms.
- `isOllamaAvailable()` pings `/api/tags` with 3 s timeout. *(Amended: an
  availability probe appropriate to the configured server.)*

### 5.2 PII Scrubber (deterministic, no LLM)

`scrub(input) → { scrubbed, redactions[], containedPII }`

| Pattern | Replacement |
|---------|-------------|
| email `\b[A-Za-z0-9._%+-]+@…\b` | `[EMAIL_REDACTED]` |
| phone `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b` | `[PHONE_REDACTED]` |
| SSN `\b\d{3}-\d{2}-\d{4}\b` | `[SSN_REDACTED]` |
| IP `\b\d{1,3}(\.\d{1,3}){3}\b` | `[IP_REDACTED]` |
| credit card (Visa/MC/Amex) | `[CARD_REDACTED]` |
| API key `(sk|pk|api|token|key|secret|bearer)[-_][A-Za-z0-9]{20,}` | `[API_KEY_REDACTED]` |

Plus a configurable **forbidden-terms** map (case-insensitive), set via
`setForbiddenTerms` / `addForbiddenTerm` (auto-replacement `[TERM_REDACTED]`).
`containsPII(input)` checks without mutating.

> Known gap to fix in reimplementation: card pattern misses spaced digits
> (`4532 1488 …`). Add `[-\s]?` separators.

### 5.3 Intent Parser

`parseIntent(raw)` → `{ intent, fromLLM, validationErrors }`.
- LLM path: prompt the model for the *task* schema → validate → **type-guard** → return.
- Fallback `heuristicParse(raw)`: extract `project_id` from `project:x`/`#x`;
  urgency from keyword count (`urgent/asap/deadline/...`); interest from
  (`cool/interesting/love/...`); `estimated_minutes = clamp(wordCount·3, 15, 120)`;
  title = first sentence truncated to 60 chars.
  *(Rebuild amendment: also extract commitment cues — `for <name>`, `by <date>` —
  into the requester/promised fields; specs/05 P2.)*

`generateMicroActions(title, ctx?)` → 3–7 sub-steps (each ≤ 5 min). Fallback to a
deterministic 6-step template.

`expandThought(fragment, recentContext?)` → `{ expanded_text, likely_project,
related_topics[], suggested_next_action }`. Fallback echoes the fragment.

---

## 6. PILOT-facing Capture (Friction-Graded Input)

| Level | Surface | Behavior |
|-------|---------|----------|
| L1 (low friction) | **Lightning Capture** overlay | Auto-focus + Web Speech API voice-to-text; pulsing SVG scales with mic volume; Enter / DONE saves with `captured_at`; logs `time_to_capture_ms`; warns if > 5000 ms. |
| L1 alt | **Capture Modal** (Cmd/Ctrl-K) | Minimal overlay, auto-focus, instant dismiss. |
| L1 alt | **Command Line** | Persistent bar; `/task /note /idea /bug /q` prefixes auto-categorize. |
| L1 alt | **Gesture Canvas** | Click anywhere on invisible canvas → type in place. |
| L2 (planning) | **Micro-Action List** | LLM/heuristic sub-steps; checklist gates Deep Focus. |
| L3 (review) | **End-of-day Brain Cache** | Review/clear captures. |

*(N=1 amendment: build Lightning Capture + Cmd-K modal; Command Line and Gesture
Canvas are deferred variations — CLAUDE.md Part XI.)*

**Airlock Gatekeeper:** between **07:00–09:00** local, the app collapses to a
single Brain Dump field; all other navigation is hidden until ≥ 1 capture is made.
*(Amended: must include a skip affordance — nudge, never trap.)*

**Capture → Transform → Lock pipeline** (`executePipeline(input)`):
1. **Capture**: `{ raw, source, captured_at }`.
2. **Transform**: `parseIntent` → candidate + latency log.
3. **Lock**: final `validateLLMOutput('task', …)`; build `Task`; flag for review if
   needed. `quickCapture(raw)` is the < 3 s LLM-free path.

---

## 7. Time Visualization

### 7.1 Radial Time-Dial (primary)

24-hour SVG dial. Geometry helpers (`timeToAngle`, `polarToCartesian`,
`describeArc`) — 0h at top (−90°), clockwise.
- **Past** region (midnight → now): low-opacity 45° hatch.
- **Task wedges**: arc per task; **angular width = baseDuration × wedgeExpansion(focusScore)**;
  opacity `0.4 + 0.5·focusScore`; color = `color_hex` else `urgencyColor(urgency)`.
- **"Now" indicator**: glowing dot at the current angle, **breathing at 60 bpm**
  (1 s sine cycle) + secondary expanding ring.
- **Ambient urgency ring**: outer ring color shifts with the most-urgent upcoming
  task (within 2 h); intensity rises with urgency.
- **Interaction**: click selects (Focus Card); double-click → Activation Bridge.

### 7.2 Variations (for A/B exploration)
*(Deferred — N=1 amendment, CLAUDE.md Part XI.)*
- **Linear Flow**: horizontal scroll timeline; tasks as variable-width islands.
- **Stacked Blocks**: vertical blocks "melting" top-down as time passes.

---

## 8. Second Brain (Knowledge Graph)

*(N=1 amendment: this whole surface is the prime cut candidate — ADR 0007; gate
at the P6 pre-flight on actual daily use.)*

### 8.1 Force-Directed Graph (primary)
- Nodes sized by **recency/frequency**: `importance = 0.4·min(1, accessCount/20) + 0.6·recency`,
  where `recency = max(0, 1 − minutesSinceAccess/720)` (12 h decay). Radius `14 + importance·18`.
- **Gravity simulation** (per frame): repulsion `2000/d²`, link attraction
  `(d−100)·0.005`, center gravity `0.01`, damping `0.85`.
- **Performance contract (must):** halt the rAF loop when total velocity² <
  `0.01`, when `document.hidden`, or when off-screen (IntersectionObserver); wake
  on interaction. No continuous render when settled or unmounted/hidden.
- Clicking a node bumps `accessCount` and `lastAccessed`.

### 8.2 Variations
*(Deferred — N=1 amendment.)*
- **Split Screen**: editor + node-link diagram.
- **Infinite Notebook**: zoom/pan canvas with arrows.
- **Terminal**: NL + SQL-like queries (`show snippets linked to project:omega`).

---

## 9. Engagement & Retention Layer

| Feature | Spec |
|---------|------|
| **Focus Ember** | Corner widget; tracks continuous focus via Visibility API; brightness ramps 0→1 over 30 min; pauses when tab hidden; shows after ≥ 1 focus minute. |
| **Focus Lens** | Press **Z** (ignored while typing in input/textarea/select); dims everything except focused content to ~5%/8% opacity; Z or Esc exits. |
| **Undo Timeline** | Scrubbable history of last hour; click an entry to undo to that point; persisted; capped at 200 entries. |
| **Object Permanence** | After 30 min inactivity, the Focus Card of an *active* task pulses. |
| **Resumption Card** | On return after ≥ 10 min absence, show last 50 chars typed, active task title, and open loops. Save on tab hidden via **safe storage**. |
| **Breadcrumb Sidebar** | Timeline feed of mental snapshots (last 8 shown). |
| **Review Flag Banner** | Lists unresolved schema/hallucination flags; dismiss/resolve. |

---

## 10. Interaction / Visual System

**Spring physics (Framer Motion):**

| Name | stiffness | damping | mass | Use |
|------|:--:|:--:|:--:|-----|
| snap | 500 | 30 | 1 | button/complete |
| medium | 300 | 25 | 1 | card/node select |
| smooth | 200 | 28 | 1.2 | panel/overlay |
| breathe | 30 | 10 | 2 | pulsing |
| bounce | 400 | 12 | 0.8 | completion |

**Breath cycle:** 1 s, sine ease `[0.45, 0, 0.55, 1]`, infinite (= 60 bpm anchor).

**Urgency color scale** `urgencyColor(u)`:
`≤3 #3b82f6` (blue) · `≤5 #6366f1` (indigo) · `≤7 #f59e0b` (amber) · `≤8 #f97316`
(orange) · else `#ef4444` (crimson).

**Variable font weights (Inter):** active **600**, normal **400**, background **300**.

**Performance logging:** `render_time`, `interaction_latency`, capture click count
to console (gate behind a debug flag in the reimplementation).

---

## 11. Persistence & Safe Storage

- Stores persist via Zustand `persist` middleware (keys: `external-lobe-storage`,
  `external-lobe-anchor`, `external-lobe-explore`, `external-lobe-undo`).
- **All direct `localStorage` access must go through a `safeStorage` wrapper** that
  guards against: SSR (no window), disabled storage, `QuotaExceededError`,
  `SecurityError`, and corrupt JSON (auto-remove). Warn once per failure mode.
- *(ADR 0006: localStorage v1; IndexedDB later behind the same adapter.)*

---

## 12. Non-Functional Requirements

- **Latency:** UI interactions < 100 ms; never block on LLM or network.
- **Offline:** fully functional with LLM unavailable (heuristic fallbacks).
- **Privacy:** prefer local LLM; scrub PII before any cloud call.
- **Accessibility:** keyboard-operable; ARIA labels on interactive SVG nodes and
  controls; never rely on color alone for urgency (pair with text/weight).
- **Browser support:** graceful when Web Speech / AudioContext / IntersectionObserver
  are absent.

---

## 13. Global Acceptance Scenarios (end-to-end)

1. **Morning Airlock:** at 08:00 with no captures, only the Brain Dump is shown;
   after one capture, full UI unlocks. *(+ skip affordance.)*
2. **Energy match:** setting energy to 1 hides interesting-but-complex tasks and
   ranks the urgent-simple task first; setting to 5 reverses it.
3. **Activation Bridge:** starting a task locks the UI to 3 micro-entries; completing
   all three transitions `TASK_INITIATION → DEEP_FOCUS`.
4. **Anti-Paralysis:** stuck > 20 min in initiation surfaces 3 micro-entries.
5. **Body Double:** switching tabs > 3 s during Deep Focus shows a nudge on return.
6. **Resumption:** leaving > 10 min then returning shows the context snapshot.
7. **Hallucination filter:** an LLM task suggesting tool `"magic-ide"` is flagged
   for review and not written to state.
8. **Offline:** with the LLM server down, capture still produces a heuristic task
   in < 3 s.
