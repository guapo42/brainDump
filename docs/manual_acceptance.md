# Manual Acceptance Checklist

The list a human runs — **exercising and observing the running app** — before
approving a phase (`specs/05`). This is the operational form of the rule
*"inspection is not verification"* (`docs/working_pattern.md`): the surfaces below
are runtime-only and lie to code inspection and to "tests pass."

**How to use it**
- At the **approval gate** (phase Definition of Done), run every **standing** item
  whose phase tag `[Pk]` is ≤ the current phase. Skip items for phases not yet built.
- During a phase / per session, you only need the subset for surfaces you changed
  (regression spot-check).
- Record results in the phase retrospective's **Manual Verification & Sign-off**
  block: PASS/FAIL + one line of *what you observed* (the evidence), not a bare ✓.
  Any FAIL becomes a bug entry (Section 1) with a class.
- "Backend OFF" means the FastAPI service stopped; "Ollama OFF" means the local
  model unreachable. The app must stay fully usable with both off.

> We work in phases, not calendar days — run the full gate at each phase boundary.
> If a phase spans multiple sessions, re-run the changed-surface subset each session.

---

## Standing checklist

### A. Cold boot & persistence
- [ ] **[P0]** Fresh clone → install → `npm run dev` boots with **no console
      errors**; `npm run build` succeeds.
- [ ] **[P2]** Create some tasks/captures, **reload** → state restored from
      IndexedDB (tasks, captures, FSM state, undo history).
- [ ] **[P2]** Clear IndexedDB → app boots to a clean empty state, no crash.
- [ ] **[P2]** (DevTools) deny storage / force `QuotaExceededError` → app **warns
      once** and stays usable; no white screen (`safeStorage` path).

### B. Offline-first core (the non-negotiable)
- [ ] **[P2]** Backend OFF **and** Ollama OFF: capture a thought → a valid task
      appears on the belt in **< 3s** via the heuristic path; nothing blocks on a
      spinner.
- [ ] **[P2]** Ollama ON: the same capture is richer/structured, still feels < 3s.
- [ ] **[P1]** Move the energy slider **1 ↔ 5**: the belt visibly re-ranks —
      urgent-simple on top at 1, interesting/challenging on top at 5.
- [ ] **[P3]** Energy input is **optional**: with no energy ever set, the app
      surfaces sensibly (defaults to 3) and never prompts for it.
- [ ] **[P3]** Responsiveness loop, offline (ADR 0007): capture "owe Dana the
      draft by Friday" → it carries requester + date → it surfaces in the
      forgetting/nudge view as the date nears, with no backend running.
- [ ] **[P3]** Capture/select/complete interactions feel **< 100ms**; no jank.

### C. The cockpit / focus loop
- [ ] **[P3]** Activation Bridge: starting a task locks the UI to 3 micro-entries;
      completing all 3 transitions `TASK_INITIATION → DEEP_FOCUS`.
- [ ] **[P3]** Anti-paralysis: sit > 20 min in `TASK_INITIATION` (advance the
      clock) → 3 trivial micro-entries surface.
- [ ] **[P3]** Body double: switch tabs > 3s during `DEEP_FOCUS` → gentle
      "welcome back" nudge on return.
- [ ] **[P3]** Resumption: leave > 10 min, return → context snapshot (last text
      typed, active task title, open loops).
- [ ] **[P3]** Time dial: now-indicator **breathes ~60bpm**; wedge width scales
      with focus score; urgency color matches the scale **and** has a non-color
      cue (text/weight).

### D. Trust boundary (LLM never commits)
- [ ] **[P2]** Stub the Translator to return an unknown tool (`"magic-ide"`) →
      it is **flagged for review and NOT written to state**.
- [ ] **[P3]** The Review Flag banner shows the flag; resolving it clears it.

### E. Backend enrichment (additive, never blocking)
- [ ] **[P4]** Backend ON: real Jira tasks appear on the belt; mapped fields look
      right (title, due date, project, assignee==You only).
- [ ] **[P4]** Edit a task locally (dopamine rating / manual ICNU), then sync →
      **local edit survives**; backend fields (frustration, requesters) merge in.
- [ ] **[P4]** Kill the backend mid-session → app keeps working and **queues**
      pushes; restart backend → reconciles with **no duplicates**.
- [ ] **[P5]** **The headline coupling:** a high-frustration backend task surfaces
      **above** an interesting-but-non-urgent task **at energy 1**; reason chips
      show ("asked 3×", "escalated to HR").
- [ ] **[P5]** Relationship-health view renders from real REQUESTED_BY data.
- [ ] **[P7]** Morning Airlock (07:00–09:00, inject the clock) collapses to the
      Brain Dump, seeded by the overnight sync; unlocks after one capture **and**
      has a visible skip affordance — the gate nudges, it never traps (a
      one-character capture or "skip" always releases it; no data is hidden
      behind it, only navigation).

### F. Performance / resource
- [ ] **[P6]** Open the knowledge graph, let it settle → the render loop **halts**
      (CPU drops to idle in the perf panel); switch tab → it pauses; return or
      interact → it wakes. Click a node → real neighborhood expands.

### G. Accessibility quick pass
- [ ] **[P3]** Keyboard-only: capture → navigate the belt → start + complete a
      task → toggle Focus Lens (Z).
- [ ] **[P3]** Urgency is never conveyed by color alone (text/weight present);
      interactive SVG nodes have ARIA labels.

---

## Phase-specific demo

In addition to the standing items, the current phase's **hypothesis demo**
(`specs/05`) must be observed working, backend **off** and **on** where
applicable. State the exact observation that proves the hypothesis. Example
(P5): *"At energy 1, the escalated security-training task sits at belt position 1
above the architecture task; removing the frustration enrichment drops it below."*

---

## Sign-off block (paste into the retro)

```markdown
## Manual Verification & Sign-off — Phase N
- Build/commit: <hash>   Date: <date>   Backend: off/on   Ollama: off/on
- Standing items run (phase ≤ N): A ✓ · B ✓ · C ✓ · ...
  - Any FAIL: <item> → observed <what happened> → bug #<class>
- Phase-N hypothesis demo: PASS — observed: <one line of evidence>
- Approved by: <name>
```
