# Task briefs

Self-contained units of work, each sized for a single session with a **small
context window**. The point: a session's context = `CLAUDE.md` (auto-loaded) +
**one brief**. The implementer should **not** open `specs/00–05` or the full
External Lobe spec — everything normative is pasted into the brief.

## How to run one

1. **Read only**: `CLAUDE.md` (the parts the brief names) + this brief. Nothing else.
2. **Red**: write the tests from the brief's *Acceptance* list (exact values).
3. **Green**: implement the minimum to pass them.
4. **Verify** the brief's `Done =` command (tests + typecheck + lint).
5. **Commit** one slice: `feat(<scope>): <subject>` (CLAUDE.md Part IX).

## Which model

- **Sonnet 4.6** is the default driver for these — they're fully specified with
  fixed, verifiable targets, so it can loop red→green without drift.
- For a **Haiku** run, have **Opus** pre-write the test file first, then hand the
  "make these pass" task to Haiku.
- Keep **Opus** for design changes, the seam, and end-of-phase review.

## Conventions these briefs assume

- **Pure logic**: no React/DOM; time enters as a **parameter/event field**, never
  `Date.now()`/`Math.random()`/`setInterval` (CLAUDE.md Part VII; ESLint enforces
  this in `engine/**`).
- **Coverage**: pure-logic dirs are gated at ≥90% (aim ~100% branch).
- **No `any`, no `as unknown as`**; narrow with type guards at boundaries.
- Types are **co-located per task** for now (no cross-task imports) so M1–M3 can
  run in **parallel sessions**. The canonical `Task` type arrives with the stores
  (P2); these engines operate on minimal structural types.

## Phase 1 slices (independent; parallelizable)

| Brief | Module | Scope | Depends on |
|---|---|---|---|
| `P1-M1-svg-math.md` | `app/lib/svg-math.ts` | `dial` | — |
| `P1-M2-icnu-engine.md` | `app/engine/icnu-engine.ts` | `anchor` | — |
| `P1-M3-fsm.md` | `app/engine/fsm.ts` | `anchor` | — |
