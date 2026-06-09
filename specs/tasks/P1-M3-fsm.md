# Task P1-M3 — Focus-state finite state machine

**Files:** `app/engine/fsm.ts` (+ `app/engine/fsm.test.ts`)
**Read only:** this brief + `CLAUDE.md` Parts III, V, VII.
**Scope/commit:** `feat(anchor): add focus-state machine reducer`
**Model:** Sonnet 4.6.

## What this is
A **pure reducer** `(ctx, event) => ctx` for the user's focus lifecycle. No React,
no clock, no RNG.

> **Determinism reconciliation (important):** the source spec says the reducer may
> read `Date.now()`. We do **not** — `engine/**` forbids it (CLAUDE.md Part VII,
> ESLint-enforced). Instead **every event carries `at: number`** (the timestamp),
> and the reducer uses `event.at` as "now." Same behavior, fully deterministic.

## Types (co-locate in this file)
```ts
export type FSMState =
  | "IDLE" | "CAPTURE_MODE" | "TASK_INITIATION"
  | "DEEP_FOCUS" | "BREAK" | "REVIEW" | "BRAIN_DUMP";

export interface FSMContext {
  state: FSMState;
  activeTaskId: string | null;
  focusStartedAt: number | null;
  focusMinutes: number;
  initiationStartedAt: number | null;
  breakStartedAt: number | null;
  transitionHistory: { from: FSMState; to: FSMState; event: FSMEvent["type"]; at: number }[];
}

export type FSMEvent =
  | { type: "START_CAPTURE"; at: number }
  | { type: "BEGIN_TASK"; at: number; taskId: string }
  | { type: "START_REVIEW"; at: number }
  | { type: "AIRLOCK_TRIGGER"; at: number }
  | { type: "CAPTURE_COMPLETE"; at: number; taskId?: string }
  | { type: "RESET"; at: number }
  | { type: "FOCUS_ACHIEVED"; at: number }
  | { type: "ANTI_PARALYSIS"; at: number }
  | { type: "FOCUS_BROKEN"; at: number }
  | { type: "TAKE_BREAK"; at: number }
  | { type: "BREAK_OVER"; at: number }
  | { type: "REVIEW_COMPLETE"; at: number };

export function initialContext(): FSMContext;
export function transition(ctx: FSMContext, event: FSMEvent): FSMContext;
export function shouldTriggerAntiParalysis(ctx: FSMContext, now: number): boolean;
```

`initialContext()` → state `IDLE`, all task/timer fields `null`, `focusMinutes 0`,
`transitionHistory []`.

## Transition table (source → event → target)
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

## Reducer contract
- **Pure.** Returns a new context on a valid transition.
- **Invalid transition** (no table entry for `state × event.type`) → return the
  **same `ctx` reference unchanged** and `console.warn` once with the attempted
  `state`/`event.type`.
- **Context side-effects** (using `event.at` as `now`):
  - `BEGIN_TASK`: `activeTaskId = event.taskId`; `initiationStartedAt = at`;
    `focusStartedAt = null`.
  - `FOCUS_ACHIEVED`: `focusStartedAt = at`; `initiationStartedAt = null`.
  - `FOCUS_BROKEN`: if `focusStartedAt != null`, add
    `Math.floor((at - focusStartedAt) / 60000)` to `focusMinutes`; then
    `focusStartedAt = null`.
  - `TAKE_BREAK`: accrue focus minutes (same formula as FOCUS_BROKEN);
    `breakStartedAt = at`; `focusStartedAt = null`.
  - `BREAK_OVER`: `breakStartedAt = null`.
  - `CAPTURE_COMPLETE`: if `event.taskId` present, set `activeTaskId`.
  - `RESET`: clear `activeTaskId`, `focusStartedAt`, `initiationStartedAt`,
    `breakStartedAt` (leave `focusMinutes` as-is unless you have a test reason; the
    source clears task/timer fields — keep `focusMinutes` accumulated).
  - `ANTI_PARALYSIS`: self-transition; no field changes besides history.
- **History**: on every valid transition append `{from, to, event, at}`, **capped
  at 50** (slice to last 50 — slice before/after push, your choice, just cap).

`shouldTriggerAntiParalysis(ctx, now)` → `true` iff
`ctx.state === "TASK_INITIATION"` AND `ctx.initiationStartedAt != null` AND
`now - ctx.initiationStartedAt > 20 * 60_000`.

## Acceptance (write these tests first)
- `initialContext()` shape is correct.
- **Every** valid row in the table moves `state` as specified (drive with explicit
  `at` values).
- Invalid transition (e.g. `IDLE` + `FOCUS_ACHIEVED`) returns the **same
  reference** (`expect(next).toBe(ctx)`) and warns.
- `BEGIN_TASK` then `FOCUS_ACHIEVED` then `FOCUS_BROKEN` with `at` 0 →
  `at` 5·60000 accrues `focusMinutes === 5` and clears `focusStartedAt`.
- `TAKE_BREAK` accrues focus minutes and sets `breakStartedAt`.
- `RESET` from each non-IDLE state returns to `IDLE` and clears task/timer fields.
- History caps at 50 entries after >50 valid transitions.
- `shouldTriggerAntiParalysis`: false at 10 min, false unless in TASK_INITIATION,
  true at 21 min in TASK_INITIATION.

## Boundaries / out of scope
- No React, no real clock, no persistence, no other modules. Anti-paralysis only
  *detects*; surfacing the 3 micro-entries is a later (P3) component task.

## Done =
```
cd app && npx vitest run engine/fsm.test.ts && npm run typecheck && npm run lint
```
(Aim ~100% branch coverage — every transition + invalid path + accrual branch.)
