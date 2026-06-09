# Task P1-M2 — ICNU + energy-weighted FocusScore engine

**Files:** `app/engine/icnu-engine.ts` (+ `app/engine/icnu-engine.test.ts`)
**Read only:** this brief + `CLAUDE.md` Parts III, V, VII.
**Scope/commit:** `feat(anchor): add energy-weighted FocusScore engine`
**Model:** Sonnet 4.6.

## What this is
The deterministic core of task surfacing: score a task's ICNU against the user's
energy level. **Pure logic** — no React, no clock, no RNG. This is the product's
**canonical** ICNU model (0–10, energy-weighted); it is unrelated to the backend
simulation's 0–1 ICNU (see CLAUDE.md Part VII — do not conflate them).

> Note: `engine/**` is covered by the determinism ESLint rules — no `Date.now`,
> `Math.random`, `setInterval`, `new Date()`, or `as unknown as`.

## Types (co-locate in this file)
```ts
export interface ICNUScore {
  interest: number;   // 0–10
  challenge: number;  // 0–10
  novelty: number;    // 0–10
  urgency: number;    // 0–10
}
export type EnergyLevel = 1 | 2 | 3 | 4 | 5;
```
Functions operate on a minimal structural shape `T extends { icnu_score: ICNUScore }`
(don't import the product `Task` type — it doesn't exist yet).

## Normative constants & formulas

`clamp01(x) = Math.min(1, Math.max(0, x))`

**FocusScore:**
```
FocusScore(icnu, energy) = clamp01( (wI·I + wC·C + wN·N + wU·U) / 10 )
```

**Energy weight profiles** (each row sums to 1.0):

| Energy | wI | wC | wN | wU |
|:--:|:--:|:--:|:--:|:--:|
| 1 | 0.10 | 0.05 | 0.05 | 0.80 |
| 2 | 0.15 | 0.10 | 0.10 | 0.65 |
| 3 | 0.25 | 0.25 | 0.20 | 0.30 |
| 4 | 0.35 | 0.30 | 0.20 | 0.15 |
| 5 | 0.35 | 0.30 | 0.25 | 0.10 |

**`wedgeExpansion(focusScore)`** = `0.5 + focusScore² · 1.5` → range **[0.5, 2.0]**
(0 → 0.5, 0.5 → 0.875, 1 → 2.0).

## API (exact signatures)
```ts
export function focusScore(icnu: ICNUScore, energy: EnergyLevel): number;
export function rankTasks<T extends { icnu_score: ICNUScore }>(
  tasks: T[], energy: EnergyLevel
): (T & { focusScore: number })[];                 // sorted DESC; stability not required
export function filterByEnergy<T extends { icnu_score: ICNUScore }>(
  tasks: T[], energy: EnergyLevel
): T[];
export function wedgeExpansion(focusScore: number): number;
```

**`filterByEnergy` rules:**
- Energy ≤ 2: keep where `urgency ≥ 5 AND challenge ≤ 6`.
- Energy = 3: keep all.
- Energy ≥ 4: keep where `interest ≥ 5 OR challenge ≥ 5`.

## Acceptance (write these tests first)
- All-zero ICNU → `focusScore` is `0` at every energy 1–5.
- All-ten ICNU → `focusScore` is `1` (±1e-9) at every energy.
- `focusScore` is within `[0, 1]` across the full 0–10 grid (spot-check a range).
- Each weight profile sums to `1.0` (±1e-5).
- Energy 1: an urgency-only task (`U=10`, rest 0) scores `≈ 0.8` and **outranks**
  an interest-only task (`I=10`, rest 0).
- Energy 5: an interest-only task **outranks** an urgency-only task.
- `filterByEnergy`: at energy 2 a `{U:8,C:7}` task is dropped (challenge>6) but
  `{U:8,C:3}` kept; at energy 3 all kept; at energy 4 a `{I:6}` task kept and a
  `{I:2,C:2}` task dropped.
- `wedgeExpansion`: `0 → 0.5`, `0.5 → 0.875`, `1 → 2.0`.
- `rankTasks` attaches `focusScore` and returns descending order.

## Boundaries / out of scope
- No React, no rendering, no persistence, no clock/RNG. No other modules.

## Done =
```
cd app && npx vitest run engine/icnu-engine.test.ts && npm run typecheck && npm run lint
```
(Aim ~100% branch coverage — every energy branch + every filter cohort.)
