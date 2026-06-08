# Phase 0 Retrospective — "a test-first repo where the frontend is fully decoupled from the backend"

## Bugs Found and Fixed

| Bug | Class | Severity | Found By | Time | Commit |
|-----|-------|----------|----------|------|--------|
| import-linter errored on external forbidden modules | (tooling config) | minor | `make`/manual | 2m | backend scaffold |
| Next scaffold emitted unused-param lint warnings in stub | (lint config) | minor | `npm run lint` | 3m | app scaffold |

Both were config gaps, not logic bugs. No new bug *class* warrants tracking yet.

## Cumulative Bug-Class Counts (through Phase 0)
- (none of the tracked classes have occurred) — clean baseline.

## Tests Added
- `safe-storage.test.ts` → catches: Storage fragility (preventive: SSR/quota/corrupt-JSON).
- `local.test.ts` → catches: Seam/contract drift (preventive: offline default holds).
- `test_config.py` → catches: LLM-provider lock-in (preventive: config-selected provider).

## Integration Points Introduced
- app → `IntelligenceService` (via `getIntelligence()` factory): ✅ unit (stub).
  Real adapter (`BrainDumpIntelligence`) deferred to P4 — carry-forward.
- No app↔backend or app↔sim runtime edges yet (by design).

## Decisions Made
- Used `create-next-app` for a guaranteed-buildable Next 16 baseline, then layered
  Vitest + boundary/determinism ESLint on top. Reason: predictable framework
  baseline; we control the test/lint setup.
- Determinism ESLint rules scoped to `engine/**` + `domain/**` only (the
  unambiguously-pure homes); `lib/**` holds mixed helpers like `safe-storage`.
- Coverage thresholds scoped to pure-logic dirs only (no UI-coverage noise).
- Recorded ADRs 0001–0005 (incl. LLM provider deferred) to pin the why.

## Open Questions / Carry-Forward
- See `docs/carry_forward.md`. Notably: `make dev` not exercised in this container
  (build verified, dev-server boot not) → verify in P1 pre-flight.

## Manual Verification & Sign-off — Phase 0
- Build/commit: P0 branch   Date: 2026-06-08   Backend: n/a   LLM: n/a
- Standing items run (phase ≤ 0):
  - A `[P0]` fresh install + `npm run build` succeeds: **PASS** — `make check`
    + `npm run build` green; `tsc --noEmit` clean.
  - A `[P0]` `npm run dev` boots with no console errors: **NOT RUN** — deferred to
    P1 pre-flight (build-only container); carry-forward filed.
- Boundary/determinism guardrails: **PASS** — verified they *bite* on planted
  violations (Date.now/Math.random/as-unknown/cross-boundary import; sim→fastapi).
- Phase-0 hypothesis demo: **PASS** — `make check` green on both stacks; frontend
  test suite runs entirely on `LocalIntelligence` (no backend).
- Approved by: (pending human sign-off)

## Independent Reviewer (Section 7)
- **Vocabulary drift:** none — code matches specs glossary; "Ollama" de-locked to
  "OpenAI-compatible (Ollama/llama.cpp)" across CLAUDE + specs/00 + ADR 0005.
- **Seam honesty:** app imports only `getIntelligence()` + port types; ESLint
  forbids concrete adapters/backend imports (verified).
- **Separation integrity:** import-linter contracts kept; backend holds no live
  cognitive state.
- **Determinism:** no clock/RNG in logic; rules dormant-but-armed for engine/domain.
- **LLM-boundary trust:** n/a yet (no model calls in P0).
- **Acceptance bar:** hypothesis met — decoupled, test-first, green both stacks.
- **Would embarrass the demo:** nothing user-facing yet (no UI beyond Next default
  page); that's expected at P0.

## Pre-Flight Items for Next Phase (P1)
- Run `make dev`; confirm the page renders with no console errors.
- Confirm determinism ESLint rules fire as engine/ files appear (ICNU, FSM).
- Keep coverage ≥ thresholds as the first pure-logic modules land.
