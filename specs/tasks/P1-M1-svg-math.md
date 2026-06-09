# Task P1-M1 — SVG math for the time dial

**Files:** `app/lib/svg-math.ts` (+ `app/lib/svg-math.test.ts`)
**Read only:** this brief + `CLAUDE.md` Parts III (layer boundaries), V (TS style),
VII (determinism).
**Scope/commit:** `feat(dial): add svg-math geometry helpers`
**Model:** Sonnet 4.6.

## What this is
Pure geometry helpers for the 24-hour radial time-dial. No React, no DOM, no time
source — just math. Lives in `lib/` (mixed-helpers home), but is fully pure.

## Dial convention (normative)
- The dial is a 24-hour clock. **0h is at the top**, time runs **clockwise**.
- In SVG screen coords (y grows downward), with the standard
  `x = cx + r·cos(rad), y = cy + r·sin(rad)`:
  - angle **−90° → top** (0h), **0° → right** (6h), **90° → bottom** (12h),
    **180° → left** (18h). Increasing angle = clockwise. This is consistent —
    derive `timeToAngle` to match.

## API (exact signatures)
```ts
export function degToRad(deg: number): number;
export function polarToCartesian(
  cx: number, cy: number, r: number, angleDeg: number
): { x: number; y: number };
export function timeToAngle(hours: number): number;   // hours in [0, 24), may be fractional
export function describeArc(
  cx: number, cy: number, r: number, startAngleDeg: number, endAngleDeg: number
): string;                                              // SVG path data
```

### Definitions
- `degToRad(deg)` = `deg * Math.PI / 180`.
- `polarToCartesian` = standard formula above (radians via `degToRad`).
- `timeToAngle(hours)` = `-90 + hours * 15` (15°/hour; 360°/24h). No wrapping
  required for inputs in `[0, 24)`.
- `describeArc` returns `"M <sx> <sy> A <r> <r> 0 <largeArc> <sweep> <ex> <ey>"`
  where start/end come from `polarToCartesian` at the two angles,
  `largeArc = (endAngleDeg - startAngleDeg) > 180 ? 1 : 0`, and `sweep = 1`
  (clockwise, matching the dial). Numeric rounding is your choice (full precision
  or a fixed decimals) — tests use approximate matching.

## Acceptance (write these tests first)
- `degToRad`: `0 → 0`; `180 ≈ π`; `90 ≈ π/2`.
- `polarToCartesian(0,0,10, …)`: `-90 → ≈{0,-10}` (top); `0 → ≈{10,0}` (right);
  `90 → ≈{0,10}` (bottom). Use `toBeCloseTo`.
- `timeToAngle`: `0 → -90`; `6 → 0`; `12 → 90`; `18 → 180`; `3 → -45`;
  fractional `6.5 → 7.5`.
- `describeArc`: result starts with `"M"` and contains `" A "`; parsed start/end
  endpoints ≈ `polarToCartesian` at the given angles; `largeArc = 0` for a 90°
  arc and `largeArc = 1` for a 200° arc; `sweep = 1`.

## Boundaries / out of scope
- No rendering, no React, no `Date`/`Math.random`. No other modules.

## Done =
```
cd app && npx vitest run lib/svg-math.test.ts && npm run typecheck && npm run lint
```
(Coverage on this file should be ~100%.)
