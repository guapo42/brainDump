# Brain Dump — Simulation Test Harness Specification

The simulation is **not part of the product**. It is a deterministic,
no-Docker, no-LLM validation harness with two jobs:

1. **Validate the App's logic** — exercise every query and scoring function
   against a rich, year-long stream of realistic task data, and assert
   correctness/coverage. (Passive `UserAgent` track.)
2. **Model realistic ADHD behavior** — simulate executive dysfunction,
   hyperfocus, object-permanence loss, and dopamine-driven task selection, to
   evaluate whether the App's nudges/scoring actually break through. (ADHD
   `ADHDUserAgent` track.)

It depends **only** on the shared domain models and the Store Protocol
(`02` ↔ `01` share that contract). It must never import Neo4j, Chroma, Ollama,
FastAPI, or any connector.

---

## 1. Time model — `SimClock`

- Iterates **52 weeks** of 2026 (Mon Jan 5 → Mon Dec 28), one `SimWeek` per
  week: `(week_number 1..52, monday: date, quarter 1..4)`.
- Each week is **5 ticks** (Mon–Fri) for the ADHD agent.
- `date_in_week(week, weekday, hour)` builds concrete timestamps for Sources.
- **All time-dependent logic takes `today` as a parameter** — no
  `datetime.now()` inside scoring — so runs are reproducible.

---

## 2. Cast — `registry.py`

Canonical `PersonRecord`s (name, email, role, preferred platform):

| Key | Name | Role | Platform |
|---|---|---|---|
| `linda` | Linda Torres | Manager | gmail |
| `robert` | Robert Kim | Project Director | gmail |
| `sarah` | Sarah Chen | Senior Engineer | slack |
| `marcus` | Marcus Webb | Junior Developer | slack |
| `priya` | Priya Patel | Mid-level Developer | slack |
| `you` | You | Tech Lead | gmail |

(In the rebuild, the Jira connector can also seed the graph from a real board;
the scripted office agents remain the deterministic baseline for CI.)

---

## 3. Office agents — scripted 12-month storylines

Each office agent extends `BaseAgent` and implements
`generate_messages(week, state) -> list[SimMessage]`. A `SimMessage` bundles
`text`, `SourceMetadata`, a **pre-built `ExtractionResult`** (no LLM), and
`resolves_tasks` (descriptions this message marks done).

`BaseAgent` provides builders (`_person`, `_project`, `_task`, `_tone`,
`_extraction`, `_make_message`) so storylines stay readable.

Storyline intent (extracted from the prototype; preserve the narrative arcs):

| Agent | Cadence & arc |
|---|---|
| **Linda (Manager)** | Quarterly admin: timesheets, self-assessments, **mandatory security training** that goes unanswered, gets a follow-up, then **escalates to HR/VP** (tone: urgency 1.0, escalation, frustrated, follow_up). Monthly check-ins. This is the canonical "boring but escalating" thread that tests frustration scoring + the wall of awful. |
| **Robert (Director)** | Project-level deliverables and milestones across Phoenix / EPA; references deliverables; sets hard deadlines. |
| **Sarah (Senior Eng)** | Peer technical work, PR reviews, design discussions; `peer_progress_mentioned` (social proof). |
| **Marcus (Junior)** | Asks for help/reviews; dependencies that make tasks `WAITING_ON` you. |
| **Priya (Mid)** | Mix of deliverables and dependencies; cross-project. |

These storylines deliberately produce: overdue tasks, escalations, follow-ups,
deliverable references, peer-progress signals, and multi-project tasks with the
same description — i.e. they exercise every branch of the scoring formula and
every identity invariant (INV-1..6).

---

## 4. In-memory stores — `InMemoryGraphStore` / `InMemoryVectorStore`

Implement the **same Store Protocol** as the Neo4j/Chroma adapters (see
`01-app-spec.md §4`). Built from plain dicts + an edge list; mirror MERGE
semantics and the identity invariants exactly:

- `tasks` keyed by composite `description||project` (INV-3).
- `_email_to_name` map for person identity (INV-4).
- `GENERATED` + `REQUESTED_BY` edges on every task (INV-1).
- `created_at`/`updated_at` (INV-2), `RESPONDS_TO` thread chaining (INV-5),
  edge-set dedup (INV-6).
- `mark_task_done(description)` flips status and drops `WAITING_ON` edges.
- Vector store = keyword overlap scoring (no embeddings) returning the same
  `{ids, documents, metadatas}` shape ChromaDB uses.

**Contract parity test (critical):** a shared test suite runs the *same*
ingest + query assertions against both `InMemoryGraphStore` and
`Neo4jGraphStore` (the latter behind the `integration` marker). If they
diverge, CI fails. This is what guarantees the simulation actually validates
production behavior.

---

## 5. The cognitive model (ADHD agent)

Lives in `simulation/cognitive/`. Three pieces: **state**, **ICNU scoring**,
**behavioral rules**.

### 5.1 `CognitiveState`

```
dopamine_level: float = 0.5
working_memory: list[str]; capacity = 3        # FIFO eviction
friction_tolerance: int = 3
time_perception_skew: float = 0.6              # <1 ⇒ underestimates effort
phase: SCANNING|EVALUATING|WORKING|HYPERFOCUSING|DISTRACTION_LOOP|RESPONDING|EXECUTIVE_DYSFUNCTION|IDLE
hyperfocus_topic / _ticks_remaining / _task_key
distraction_ticks_remaining
current_task_* (key, ticks_spent, ticks_needed)

boost_dopamine(+)/decay_dopamine(-)            # clamped [0,1]
```

### 5.2 ICNU scoring (replaces priority)

`score_task(task, state, week, seen_types) -> ICNUScore(interest, challenge,
novelty, urgency)`; `total = I+C+N+U`.

- **Interest** — 0 for admin keywords (timesheet, compliance, training, PTO,
  budget, self-assessment…); 0.9 if it matches the current hyperfocus topic;
  else 0.5/0.3/0.1 by technical keyword tier.
- **Challenge** — keyword tiers: HIGH {architecture, design, debug,
  investigate, optimize, refactor, migrate}=0.9; MED {review, implement, build,
  integrate, write, fix}=0.5; LOW {submit, forward, confirm, send, reply,
  attend, schedule}=0.1; unknown=0.3.
- **Novelty** — first time a task *type* is seen =1.0, then 0.5, 0.2, 0.0
  (decays). Type classifier buckets: pr_review, document_review, architecture,
  deployment, testing, admin_submit, writing, debugging, implementation, other.
- **Urgency** — due ≤7d=1.0, ≤14d=0.7, ≤28d=0.3, none=0.0; **overdue=0.6**
  (shame/avoidance *reduces* below crisis).
- **Frustration → urgency bridge (the key coupling):** if the task carries a
  `frustration_score`, add `min(frustration/40, 0.5)` to urgency; reasons add
  more (escalation +0.15 urgency; peer/progress +0.1 interest; follow-up +0.1
  urgency). This is how the App's frustration model is what lets a boring task
  finally break through executive dysfunction.

### 5.3 Behavioral rules

- **Wall of Awful** — if `urgency >= 0.9`, panic overrides (returns False).
  Else if `interest+challenge <= 0.2 and dopamine < 0.5` (or `<=0.1`
  unconditionally) → enter DISTRACTION_LOOP for 2–3 ticks. Can't *start*
  unmotivating tasks.
- **Object permanence** — Monday (tick 0) always runs all queries (morning
  scan). Ticks 1–4: queries about topics not "visible" this week have a **40%
  chance of being skipped** (forgotten). Visible = keyword overlap with this
  week's incoming messages.
- **Capture friction** — if a task needs more steps than `friction_tolerance`,
  **70% chance of abandoning** ("had the thought, lost it before I logged it").
- **Executive dysfunction** — if `ICNU.total < 0.5 and dopamine < 0.2` → stall.
- **Hyperfocus** — can't trigger if `dopamine < 0.2`; if `interest>=0.8 and
  challenge>=0.7` → 35% chance of 2–3 ticks locked; or `interest>=0.9` → 20%
  chance of 2 ticks. Completing during hyperfocus → dopamine crash (−0.15).
- **Time blindness** — `perceived = ceil(actual * skew)`; the offset
  (actual−perceived) accumulates as a metric.

### 5.4 Weekly tick loop (`ADHDUserAgent.run_weekly`)

Per tick: handle ongoing distraction/hyperfocus first; per-tick dopamine decay
(Monday partial reset); SCAN (object-permanence-filtered queries → task pool,
plus the Monday "forgetting" nudge injection); EVALUATE (ICNU-score the pool,
load top-N into working memory; Friday "guilt" surfaces a dreaded task); then
the gauntlet: Wall of Awful → Executive Dysfunction → Capture Friction →
WORKING (possible hyperfocus) → maybe complete → emit a response `SimMessage`.
Deterministic given a seed.

---

## 6. Reports

### 6.1 `GapAnalyzer` → `SimulationReport` (passive track)

Runs the passive `UserAgent`, which each week exercises **every production
query** (Tier A) and runs **data-integrity checks** (Tier B: person-name
collisions, task-description collisions, overdue detection). Report captures:
totals (messages, tasks, resolved, hanging, overdue, persons, projects, edges),
**per-query coverage with success rates** (assert 100%), integrity issues, and
a checklist of the implemented invariants/queries with validation notes.

### 6.2 `ADHDReportGenerator` → `ADHDSimulationReport` (cognitive track)

Captures task outcomes (seen / completed / abandoned-friction / never-seen /
in-progress / **completion_rate**), cognitive metrics (avg dopamine,
hyperfocus episodes + avg length, distraction ticks, wall-of-awful triggers,
exec-dysfunction stalls, thought-lost events, object-permanence misses), time
blindness offset, tool usage (queries executed/skipped, messages sent),
**ICNU completion drivers** (which dimension drove each completion), graph
stats, and a **weekly heatmap** (done/abandoned/hyperfocus/distraction/
queries/skipped per week).

---

## 7. What the simulation asserts (test gates)

These become the harness's pytest suite. They are the regression net for the
App's logic and the cognitive model.

**Passive (logic validation):**
- Simulation completes; >100 messages, >50 tasks ingested.
- **Every production query runs at 100% success** across all 52 weeks.
- Tasks resolve over time (>5).
- All identity invariants hold (no unexpected collisions in Tier B).
- Graph integrity: ≥5 persons, ≥2 projects, >100 edges.

**Cognitive (behavioral realism):**
- `0 < completion_rate < 1.0` (an ADHD agent neither finishes everything nor
  nothing).
- Hyperfocus occurs (>0 episodes).
- Distraction loops or wall-of-awful triggers occur (>0).
- Object-permanence misses occur (>0).
- Response messages are generated (>0).
- **Determinism:** same seed ⇒ identical `tasks_completed` and
  `hyperfocus_episodes`.
- **Frustration coupling (the headline result):** wiring frustration scores
  into ICNU urgency measurably increases completion of high-frustration admin
  tasks (e.g. the security-training escalation gets done). The prototype noted
  an ~8× completion-rate effect — re-establish a guarded assertion here.

---

## 8. Running it

```
pytest sim/ -v                 # whole harness, no Docker/LLM
python -m sim.run              # ADHD run, prints the formatted report
python -m sim.run --passive    # passive gap-analysis run
```

The harness is the **fast inner loop**: it runs in seconds, needs no services,
and is where each App feature is validated before (and after) it gets a real
Neo4j/Chroma adapter.
