# Working Pattern

The working rhythm for the Brain Dump × External Lobe build. It complements the
specs and `CLAUDE.md` by covering the *process* layer: how each phase connects to
the next, how bug patterns are tracked across phases, and how the system stays
stable as the two stacks (React frontend, Python backend) grow toward each other
at the `IntelligenceService` seam.

The goal: catch pattern bugs early, prevent foundation drift across phases, and
ensure each phase builds on a verified-stable base.

We work in **phases P0–P8** (`specs/05-iterative-plan.md`), each a hypothesis +
demo gate. The pattern has two per-phase components and one optional milestone
component.

> Cadence note: phases are larger than the NSDUH "day." Run the retrospective at
> **each phase boundary**, and additionally any time a single phase spans several
> sessions or surfaces 2+ bugs of one class mid-phase — don't wait for the gate
> to record a pattern you can already see.

---

## Per-Phase Components

### End-of-Phase Retrospective

Before considering a phase complete, write `docs/retrospectives/phase_NN.md`.
Concise and signal-dense (1–2 pages), focused on process and pattern data, not
features delivered. Before closing it:
- [ ] Update `docs/carry_forward.md`: remove completed items; add new deferrals
      with origin + acceptance criteria.

### Start-of-Phase Pre-Flight

Before writing code, run the pre-flight (three parts):

**Part A — Standard checklist**
- [ ] Frontend fast lane green: `npm run typecheck && npm run lint && npm test`.
- [ ] Backend fast lane green: `uv run ruff check && uv run mypy && uv run pytest -m "not integration and not e2e"`.
- [ ] **Separation checks pass**: `app/` ⊥ `backend/sim/`; `app/` reaches backend
      only via `BrainDumpIntelligence`; `backend/sim/` imports no
      neo4j/chroma/openai/instructor/fastapi/connectors.
- [ ] **Seam contract test green**: `LocalIntelligence` and `BrainDumpIntelligence`
      (recorded fixtures) both satisfy the `IntelligenceService` types/invariants.
- [ ] **Store parity** (once Neo4j exists): the contract suite passes against both
      `InMemoryGraphStore` and `Neo4jGraphStore`.
- [ ] App still demos the previous phase's hypothesis with the backend **off**.

**Part B — Phase-specific checks** — the items from the previous retrospective's
"Pre-Flight Items for Next Phase."

**Part C — Bug-class pattern review** — read the cumulative counts. Any class with
**2+ occurrences** gets a structural fix planned **above** this phase's feature
work. The cost of three occurrences exceeds the cost of fixing the design.

---

## Retrospective Format

Seven sections. If a section has nothing to record, say so explicitly rather than
omitting it.

1. **Bugs found and fixed** — table: symptom · root cause · found by (unit /
   component / contract / integration / e2e / manual / accident) · bug class ·
   severity (blocker/significant/minor) · time to fix · commit. If none: "No bugs
   found."
2. **Cumulative bug-class counts** — running tally across phases:
   `class: count (phases) — status`. Status blank (still occurring), "fixed
   structurally in P-X," or a note on why it persists. Don't add occurrences to a
   class after a structural fix — a new one means the fix was incomplete; flag it.
   **This is the most valuable section.**
3. **Tests added** — `test_name → catches: bug class (regression/preventive/new)`.
4. **Integration points introduced** — `X → Y: ✅/⚠️/❌ with notes`. Both a unit
   test (mocked) and a real-dependency test should exist. Don't end a phase with
   ❌ unless deliberate; resolve or carry forward ⚠️.
5. **Decisions made** — choices not in the spec, with reasoning (they're invisible
   in code but explain it later).
6. **Open questions / carry-forward** — each with a suggested resolution path.
7. **What would an independent reviewer find** — see prompt below.
8. **Pre-flight items for next phase** — specific verifications that this phase's
   work still functions.

### Section 7 prompt — "what would an independent reviewer find"

Answer as if a competent outside reviewer spent an hour reading the phase's
changes cold. Answer each briefly; "nothing" is valid and common — but say it
explicitly rather than skipping. Adapted to this project:

- **Vocabulary drift.** Did any concept get a new name/values/states in code that
  the specs glossary (`specs/00 §6`) or design docs don't reflect — or did a doc
  change describe something the code doesn't match yet?
- **Seam honesty.** For every `IntelligenceService` method touched: do the FE
  adapter's expected shape and the BE response actually agree, with a recorded
  fixture proving it? Does any component/store/hook reach the backend *outside*
  the adapter?
- **Separation integrity.** Any new import that crosses a forbidden boundary
  (app↔sim, app↔backend-internals, sim↔adapters)? Does the backend now hold any
  live cognitive state (FSM/energy/active-task) it must not own?
- **Determinism.** Any real clock, unseeded RNG, or live LLM/`fetch` leaking into
  pure logic or a test? Anything that would make the sim non-reproducible or a
  test flaky?
- **LLM-boundary trust.** Does every path that consumes model output pass through
  the schema validator + type guards (FE) / Pydantic (BE) before reaching state?
  Any `as unknown as` or `any` at the boundary?
- **rAF / effect hygiene.** Do animation/sim loops halt when settled/hidden/
  off-screen? Do hooks clean up timers/listeners on unmount?
- **Acceptance bar.** Did the phase's *hypothesis demo* actually run (backend off
  and on), or just "the code runs"? TODOs and placeholders in user-facing
  surfaces count against this.
- **Two-ICNU confusion.** Did the product (0–10) and sim (0–1) ICNU models stay
  separate, or did one leak into the other's territory?
- **What would embarrass the demo?** If someone with ADHD used the build
  tomorrow, what's the first friction or broken-trust moment they'd hit?

If a question surfaces something nontrivial, file it as a same-phase fix or a
production-hardening backlog entry before closing the retro.

---

## Bug-Class Reference (seed list — extend as classes emerge)

Use consistent class names so cumulative tracking works.

- **Determinism leak** — real clock/timer/unseeded RNG in logic or test → flaky
  tests, non-reproducible sim.
- **LLM-boundary trust** — unvalidated model output reaching state (missing schema
  check / type guard).
- **Type-cast escape** — `as unknown as` / `any` smuggling unsafe data past types.
- **Seam/contract drift** — FE adapter shape and BE response diverge; fixtures not
  updated in lockstep.
- **Store parity divergence** — `InMemoryGraphStore` and `Neo4jGraphStore` return
  different results for the same input.
- **Separation violation** — an import crosses a forbidden boundary
  (app↔sim, app↔backend-internals, sim↔adapters); or backend takes on live
  cognitive state.
- **Browser API absent (jsdom)** — Speech/AudioContext/IntersectionObserver/
  visibility not feature-detected → crash in test or unsupported browser.
- **rAF runaway** — animation/sim loop never halts (settled/hidden/off-screen).
- **Storage fragility** — direct localStorage access; SSR/quota/corrupt-JSON not
  handled via `safeStorage`.
- **Server/client boundary (Next)** — client-only code (`window`, stores, Framer
  Motion) leaking into a server component, or a missing `"use client"`.
- **Two-ICNU confusion** — product vs sim ICNU models conflated.

When a bug doesn't fit, add a new class with a one-line description.

---

## Counting Occurrences

Count **per surprise event**. The question: "Did I already know this was broken?"
If yes → expected fallout, don't count. If no → a surprise, count.
- Iterative fixes in one investigation: each *new* test-failure surprise of the
  same class counts.
- Same root cause found together in multiple spots: one occurrence.
- Same root cause found *separately* on different phases: separate occurrences.

Inflated counts trigger premature structural work; deflated counts let real
patterns hide.

---

## Verification anti-pattern: inspection-as-verification

"Structurally correct per code inspection," "tests pass" (without runtime
exercise), or "verified via an alternative path" is **not** verification. Require
exercised-and-observed evidence. Untrustworthy without runtime exercise:
- React hooks under fake timers (visibility, ember ramp, anti-paralysis cadence);
- component rendering with live store data (mocks hide shape bugs);
- the `BrainDumpIntelligence` adapter against the real FastAPI service;
- rAF halting behavior in the knowledge graph;
- offline→online sync transitions (`isAvailable()` flips).

---

## Milestone Synthesis (optional, ~every 2–3 phases)

`docs/retrospectives/synthesis_PNN.md`: bug-rate trajectory, recurring classes
(structural-fix candidates), classes fixed structurally (mark resolved),
seam/contract coverage, test-suite health, recurring pre-flight failures, and any
strategic shift the phase-level data suggests. Short — half a page. Read before
the next phase.

---

## What Not to Include / When to Skip

Signal-dense, not narrative. Don't include: long implementation descriptions
(the commits/PR cover that), self-congratulation, non-actionable speculation,
commentary on this pattern, or repetition of the deliverable summary. Over two
pages → trim.

**Don't skip retrospectives** — cumulative tracking depends on every phase being
recorded. A clean phase gets a short one ("No bugs found"); that still pins the
data point. A skipped retro breaks pattern recognition.

---

## Templates

### Phase Retrospective

```markdown
# Phase N Retrospective — <hypothesis>

## Bugs Found and Fixed
| Bug | Class | Severity | Found By | Time | Commit |
|-----|-------|----------|----------|------|--------|

## Cumulative Bug-Class Counts (through Phase N)
- Class A: count (phases) — status

## Tests Added
- test_name → catches: bug class (regression/preventive/new)

## Integration Points Introduced
- X → Y: ✅/⚠️/❌ notes

## Decisions Made
- Decision. Reason: ...

## Open Questions / Carry-Forward
- Item. Suggested resolution: ...

## Independent Reviewer (Section 7)
- Vocabulary drift: ...
- Seam honesty: ...
- Separation integrity: ...
- Determinism: ...
- LLM-boundary trust: ...
- rAF / effect hygiene: ...
- Acceptance bar: ...
- Two-ICNU confusion: ...
- Would embarrass the demo: ...

## Pre-Flight Items for Next Phase
- Item to verify next phase
```

### Milestone Synthesis

```markdown
# Synthesis through Phase N

## Bug Rate Trajectory
- P(k): N bugs ... Trend: [increasing|decreasing|flat]

## Recurring Bug Classes
- Class X (n occurrences): structural fix planned/done

## Seam & Store Contract Coverage
- IntelligenceService methods covered: M/total
- In-memory↔Neo4j parity: pass/gaps

## Test Suite Health
- Totals, slowest, flaky

## Strategic Observations / Adjustments
- ...
```

---

## Related

- `CLAUDE.md` — every-session project context (references this doc).
- `specs/00–05` — design source of truth.
- `docs/retrospectives/` — per-phase retros (chronological).
- `docs/carry_forward.md` — live deferral list.
