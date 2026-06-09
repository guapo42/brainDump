# The External Lobe — TDD Reimplementation Plan (milestone reference)

> **Status:** absorbed into `specs/05-iterative-plan.md`, which re-sequences these
> milestones into phases P0–P8 (see 05's source-plan mapping table). **Where they
> conflict, 05 wins.** This file is retained because 05 and the `specs/tasks/`
> briefs reference milestone numbers (M0–M16) defined here. Committed verbatim
> from the source document; the same amendments as `06-external-lobe-spec.md`'s
> header apply (determinism via `event.at`, ADR 0005/0006/0007).

> A dependency-ordered, test-first plan to rebuild the system described in
> `06-external-lobe-spec.md`. The ordering follows the testability gradient:
> **pure logic → stores → hooks → components → integration**. Each milestone is
> shippable and gated by a green test suite.

---

## 0. Methodology

**The loop (per unit of behavior):**
1. Write a failing test that encodes one acceptance criterion from the spec.
2. Write the minimum code to pass it.
3. Refactor; keep the suite green.
4. Commit when a coherent slice is green.

**Rules:**
- **Red before green.** No production code without a failing test that demands it.
- **Pure logic targets 100% branch coverage.** It is cheap and high-value.
- Each spec constant (weights, thresholds, colors, schema bounds) gets at least one
  test asserting the exact value — these are the regression anchors.
- Inject time: never call `Date.now()`/`setInterval` in pure logic without a seam
  (fake timers in tests).
- A milestone is **Done** only when: tests pass, types check, `build` succeeds,
  and lint is clean.

**Test taxonomy:**
- **Unit** (Vitest, node env): pure logic, stores, formulas.
- **Hook/integration** (Vitest + jsdom + Testing Library): hooks, timers, storage.
- **Component** (Testing Library): render + interaction + accessibility.
- **E2E** (Playwright, optional final phase): the §13 global scenarios.

---

## 1. Tooling & Foundations (Milestone 0)

**Goal:** a repo that can run a failing test on day one.

- Scaffold Next.js (App Router, TS, Tailwind), Zustand, Framer Motion.
- Add **Vitest** + `@testing-library/react` + `jsdom` + `@testing-library/jest-dom`.
- Scripts: `test`, `test:watch`, `test:ui`, `lint`, `build`, `typecheck`.
- `vitest.config.ts` with `@` alias, node default env, jsdom per-file opt-in.
- CI: run `typecheck && lint && test && build` on every push.
- Add `safeStorage` wrapper **first** (everything persists through it).

**DoD:** `npm test` runs and reports zero tests; CI is green; a sample
`safe-storage.test.ts` passes (SSR, quota, corrupt-JSON paths).

---

## 2. Pure Logic Core (Milestones 1–5) — *no React*

These have **no dependencies on each other** except where noted, so they can be
parallelized. They are the spec's normative heart.

### M1 — SVG Math (`lib/svg-math.ts`)
- Tests: `degToRad`, `polarToCartesian` (0°/90°/offset), `timeToAngle`
  (0h→−90°, 6h→0°, 12h→90°, fractional minutes), `describeArc` (path shape,
  largeArc flag < 180° vs > 180°).

### M2 — ICNU Engine (`engine/icnu-engine.ts`)
- Tests encode spec §4.1 exactly: weight-profile sums, boundary scores (0 and 1),
  energy-dependent dominance, `filterByEnergy` cohorts, `wedgeExpansion` curve,
  `rankTasks` ordering.

### M3 — FSM (`engine/fsm.ts`)
- Tests: initial context; **every** valid transition in the table; invalid
  transitions return same reference + warn; focus-minute accrual under fake
  timers; `RESET` from each state; history cap at 50; `shouldTriggerAntiParalysis`
  at 10 min (false) and 21 min (true).
- This is a pure reducer — model it as `(ctx, event) => ctx`.

### M4 — Schema Validator + Type Guards (`engine/schema-validator.ts`, `engine/type-guards.ts`)
- Tests: each schema's required/type/range/enum failures; unknown-field flag;
  unknown-tool flag; case-insensitive Known Tools; `registerTool`; sanitized output
  shape. Type guards reject null/primitive/malformed arrays.

### M5 — PII Scrubber (`engine/scrubber.ts`)
- Tests: each PII pattern (incl. **spaced** card numbers — fix the known gap),
  clean pass-through, `containsPII`, forbidden terms (case-insensitive, custom &
  auto replacement). Reset forbidden terms between tests.

**Milestone gate:** Phase-2 suite is the regression backbone; target ~100% branch
coverage here. Nothing else proceeds until green.

---

## 3. Translator (Milestones 6–7) — *logic with injected I/O*

### M6 — LLM Client (`engine/llm-client.ts`)
- Inject `fetch` (or wrap it) so tests need no network.
- Tests: local-server happy path; JSON extraction from markdown-wrapped responses;
  timeout via `AbortController`; retry with exponential backoff (assert delays via
  fake timers); local→cloud fallback; **cloud path scrubs PII first**;
  availability probe true/false.

### M7 — Intent Parser & Pipeline (`engine/intent-parser.ts`, `engine/pipeline.ts`)
- Tests: LLM path validates + type-guards before returning; **fallback to
  heuristic** when LLM down/invalid; `heuristicParse` extracts project/urgency/
  interest/duration/title per spec (+ commitment cues per specs/05 P2);
  `generateMicroActions` length 3–7 + template fallback; `executePipeline`
  produces a valid `Task`, logs latency, flags review when needed; `quickCapture`
  is LLM-free and fast.

---

## 4. Stores (Milestone 8) — *Zustand + safe persist*

### M8 — Stores (`store/*`, `engine/anchor/store.ts`)
- `useStore` (tasks, captures, selection, overlay), `useAnchorStore` (FSM,
  snapshots, review flags, body-double nudge counter), `useExploreStore`,
  `useUndoHistory` (1-hour window, cap 200).
- Tests (via `store.getState()` outside React): `dispatch` delegates to the FSM
  reducer; `addCapture` sets `hasCapturedToday`; snapshot cap at 100; review-flag
  add/resolve; undo push/undo-to-timestamp; persistence round-trips through a
  mocked `safeStorage`.
- **Decision to make explicit:** define clear store boundaries (UI-ephemeral vs
  deterministic cognitive vs exploration vs undo) to avoid the original's overlap.

---

## 5. Hooks (Milestone 9) — *jsdom + fake timers*

### M9 — Effect hooks (`hooks/*`)
- `useObjectPermanence` (30 min inactivity → pulse), `useFocusEmber` (visibility
  tracking, 30-min ramp, pause on hide), `useResumption` (10-min absence, safe
  storage), `useVoiceCapture` (Web Speech + AudioContext **feature detection** +
  graceful absence), `useDashboardEffects` (body-double, snapshot timer,
  anti-paralysis cadence, resumption save).
- Tests: mock `document.visibilityState`/`hidden`, `navigator.mediaDevices`,
  `SpeechRecognition`; drive `setInterval`/timeouts with fake timers; assert
  cleanup on unmount (no leaked listeners/timers).
- **Guardrails module** (`engine/guardrails.ts`) tested here too:
  `completedTaskOpacity` curve, `generateAntiParalysisEntries` (exactly 3),
  `shouldSuggestBreak`, snapshot timer start/stop.

---

## 6. Components (Milestones 10–13) — *render + interaction + a11y*

Build presentational pieces before containers. Each component test asserts:
renders expected content, dispatches expected action on interaction, and meets a
basic **accessibility** check (role/label/keyboard).

### M10 — Visual primitives & system
- Spring config + `urgencyColor` + font-weight tokens (unit-test the color scale
  thresholds and weight constants).
- `RadialTimeDial`: wedge width ∝ `wedgeExpansion(focusScore)`, opacity formula,
  now-indicator present, click selects / double-click starts. Add ARIA labels.

### M11 — Capture surfaces
- `LightningCapture` (auto-focus, friction log > 5 s warning, save with timestamp),
  `CaptureModal` (Cmd-K). *(Command Line + Gesture Canvas deferred — N=1.)*
- `AirlockGatekeeper`: time-gated render (inject "now"); hidden nav until first
  capture *(+ skip affordance)*.

### M12 — Focus & retention
- `FocusCard`, `MicroActionList` (checklist gates focus), `FocusEmber`, `FocusLens`
  (Z toggle, ignore while typing), `ResumptionCard`, `BreadcrumbSidebar`,
  `UndoTimeline`, `ReviewFlagBanner`, `VisualDecayTask` (opacity binding).

### M13 — State-of-mind controls
- `EnergySlider` (1–5, re-rank on change, optional input — defaults to 3),
  `ActivationBridge` (UI lock, sequential gating, momentum unlock → DEEP_FOCUS),
  `DetailScentsHUD` (blurred-by-default, click-to-reveal), `EngineStatus`,
  `BodyDoubleNudge` (subscribes to nudge counter), `AntiParalysisOverlay`.

### M14 — Knowledge Graph *(prime cut candidate — ADR 0007; gate at P6 pre-flight)*
- `KnowledgeGraph`: importance/radius formula, simulation **halt-when-settled /
  hidden / off-screen** contract (assert rAF stops), click bumps access + wakes.
- Second-brain variations (Split/Notebook/Terminal) — deferred (N=1).

---

## 7. Integration & Dashboard (Milestone 15)

- Compose `DashboardHeader`, `SidebarPanel`, `OverlayManager`, and the
  `useDashboardEffects` hook into the page. Keep the page component thin
  (data flow + layout only; target < ~200 lines).
- Component-integration tests for the wiring (selecting a task shows the Focus
  Card; Start opens the Bridge; energy change re-orders the list).

---

## 8. End-to-End (Milestone 16, optional)

- Playwright covering the 8 **Global Acceptance Scenarios** (spec §13):
  Airlock, energy match, Activation Bridge, Anti-Paralysis, Body Double,
  Resumption, hallucination filter, offline capture.
- Use a stubbed LLM endpoint to make runs deterministic.

---

## 9. Suggested Sequence & Parallelization

```
M0  Tooling + safeStorage            ─┐ (blocks everything)
M1  SVG math        ┐                 │
M2  ICNU engine     ├ parallel (pure) │
M3  FSM             │                 │
M4  Schema+guards   │                 │
M5  Scrubber        ┘                 │
M6  LLM client  ─── depends on M4/M5  │
M7  Intent+pipeline ─ depends on M2,M4,M6
M8  Stores ──────── depends on M3,M4
M9  Hooks+guardrails ─ depends on M8, safeStorage
M10–M14 Components ─ depend on stores/hooks/logic
M15 Integration ─── depends on components
M16 E2E (optional) ─ depends on integration
```

**Critical path:** M0 → M4 → M6 → M7 → M8 → M9 → components → M15.
The five pure-logic milestones (M1–M5) are the highest-leverage early work and
should be fully green before any UI is written.

---

## 10. Definition of Done (per milestone)

- [ ] Each spec acceptance criterion for the milestone has a corresponding test.
- [ ] `npm run typecheck` clean (no `any`, no `as unknown as` in committed code).
- [ ] `npm run lint` clean.
- [ ] `npm test` green; pure-logic milestones near 100% branch coverage.
- [ ] `npm run build` succeeds.
- [ ] One commit per coherent green slice, message references the milestone.

---

## 11. Risk Register & Mitigations

| Risk | Mitigation |
|------|------------|
| Time-dependent logic flaky | Inject `now`; use fake timers everywhere. |
| Browser APIs absent in jsdom (Speech, AudioContext, IntersectionObserver) | Feature-detect in code; mock in tests; assert graceful fallback. |
| LLM nondeterminism leaks into tests | All Translator tests use a stubbed client; never hit a real model. |
| rAF simulation never settles → CPU burn | Test the halt conditions explicitly (velocity threshold, hidden, off-screen). |
| Store overlap (original had 4 stores) | Document boundaries up front (M8); one owner per concern. |
| Hallucinated LLM data reaching state | Schema validator + type guards are a hard gate; test the reject paths. |
| localStorage quota/disabled | All access via `safeStorage`; tested failure modes. |

---

## 12. Carry-Over Fixes (do these correctly the second time)

1. Replace all `as unknown as` casts with runtime **type guards** at the LLM boundary.
2. No `window.__global` callbacks — use store actions/subscriptions.
3. Wrap **all** `localStorage` in `safeStorage`.
4. Knowledge Graph must **pause** when settled/hidden/off-screen.
5. Centralize SVG math and demo fixtures (no duplication across components).
6. Keep the page component thin via `Sidebar`/`Overlay`/`Header` extraction + a
   `useDashboardEffects` hook.
7. Gate `console.log` perf/debug behind a debug flag.
8. Add ARIA labels + keyboard handlers to interactive SVG nodes; never color-only.
9. Fix the credit-card regex to catch spaced/dashed digit groups.
