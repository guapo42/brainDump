"""ADHDUserAgent — cognitively-modeled employee using ICNU instead of priority."""

from __future__ import annotations

import random as _random
from datetime import timedelta

from models.schemas import (
    ExtractionResult,
    PersonEntity,
    Platform,
    SourceMetadata,
    TaskEntity,
)
from simulation.agents.base import SimMessage, SimState
from simulation.clock import SimClock, SimWeek
from simulation.cognitive.behaviors import (
    check_capture_friction,
    check_executive_dysfunction,
    check_object_permanence,
    check_wall_of_awful,
    estimate_perceived_ticks,
    should_trigger_hyperfocus,
)
from simulation.cognitive.icnu import estimate_task_ticks, score_task
from simulation.cognitive.state import (
    WEEKDAYS,
    AgentPhase,
    CognitiveState,
    ICNUScore,
    TickLog,
    WeekLog,
)
from simulation.stores import InMemoryGraphStore, InMemoryVectorStore

# Internal monologue templates keyed on phase/outcome
MONOLOGUES = {
    "distraction_loop": [
        "I know I should be doing that, but... let me just check Slack first.",
        "Ugh, I'll get to it in a minute. Let me see what's new on the team channel.",
        "I really don't want to do that right now. Maybe after coffee.",
    ],
    "wall_of_awful": [
        "I literally cannot make myself start this. It's not hard, I just... can't.",
        "This task has been sitting there for days. Why can't I just DO it?",
        "I know the security training takes 20 minutes. Why does it feel like climbing Everest?",
    ],
    "hyperfocus_start": [
        "Oh wait, this is actually interesting. Let me just look at this for a minute...",
        "This architecture problem is fascinating — let me dig in.",
        "OK I'm going to figure this out right now. Everything else can wait.",
    ],
    "hyperfocus_continue": [
        "Still locked in. Don't interrupt me.",
        "Wait, what time is it? ...doesn't matter, I'm almost done.",
        "I know I have other things to do but this is more important right now.",
    ],
    "task_complete": [
        "Done! That felt good. What's next?",
        "Finally finished that. The dopamine hit is real.",
        "Shipped it. OK what was I supposed to do after this?",
    ],
    "friction_abandon": [
        "Too many steps to even start this. I'll come back to it later.",
        "I need to query three different things just to understand this task? Nope.",
        "I had the thought but by the time I found the right place to log it, it was gone.",
    ],
    "executive_dysfunction": [
        "I know this is important. I'm staring at it. I still can't start.",
        "Low battery. Critical tasks are piling up but nothing is happening.",
        "Everything feels urgent and nothing feels possible.",
    ],
    "object_permanence_miss": [
        "(doesn't even think about checking for overdue tasks)",
        "(forgot to look at the project overview this morning)",
        "(that task Linda sent? what task?)",
    ],
    "scanning": [
        "OK, Monday. Let me see what's on fire.",
        "What came in today? Let me check the inbox.",
        "Alright, scanning for what needs attention...",
    ],
    "working": [
        "Working on this. Focused. For now.",
        "Making progress. Trying not to get distracted.",
        "Heads down on this one.",
    ],
}


class ADHDUserAgent:
    """Simulates an ADHD employee interacting with the brain-dump system.

    Uses ICNU scoring instead of priority. Models dopamine, working memory,
    friction tolerance, and time blindness.
    """

    def __init__(
        self,
        graph: InMemoryGraphStore,
        vector: InMemoryVectorStore,
        seed: int = 42,
    ):
        self.graph = graph
        self.vector = vector
        self.rng = _random.Random(seed)
        self.state = CognitiveState()
        self.seen_types: set[str] = set()
        self.weekly_logs: list[WeekLog] = []
        self._msg_counter = 0

        # Accumulator stats
        self.total_queries_executed = 0
        self.total_queries_skipped = 0
        self.total_thought_lost = 0
        self.total_tasks_completed: list[str] = []
        self.total_tasks_abandoned: list[str] = []
        self.total_hyperfocus_episodes = 0
        self.total_distraction_ticks = 0
        self.total_hyperfocus_ticks = 0
        self.total_time_blindness_offset = 0.0
        self.icnu_completion_drivers: dict[str, int] = {
            "interest": 0, "challenge": 0, "novelty": 0, "urgency": 0,
        }

    def run_weekly(
        self,
        week: SimWeek,
        sim_state: SimState,
        incoming: list[SimMessage],
    ) -> list[SimMessage]:
        """Process one week: 5 ticks (Mon-Fri). Returns response messages."""
        week_log = WeekLog(
            week_number=week.week_number,
            cognitive_start=self.state.snapshot(),
        )
        response_messages: list[SimMessage] = []

        # Extract visible topics from this week's incoming messages
        visible_topics = self._extract_visible_topics(incoming)

        # Shift hyperfocus topic occasionally (novelty seeking)
        if week.week_number % 6 == 0 and self.state.hyperfocus_ticks_remaining == 0:
            self._shift_hyperfocus(week)

        for tick in range(5):
            self.state.current_tick = tick
            tick_log = TickLog(
                week=week.week_number,
                tick=tick,
                weekday=WEEKDAYS[tick],
                phase=self.state.phase.name,
                monologue="",
            )

            # --- Distraction loop ---
            if self.state.distraction_ticks_remaining > 0:
                self.state.distraction_ticks_remaining -= 1
                self.state.decay_dopamine(0.1)
                tick_log.phase = AgentPhase.DISTRACTION_LOOP.name
                tick_log.monologue = self.rng.choice(MONOLOGUES["distraction_loop"])
                tick_log.outcome = "distraction_loop"
                week_log.distraction_loop_ticks += 1
                self.total_distraction_ticks += 1
                week_log.ticks.append(tick_log)
                continue

            # --- Hyperfocus continuation ---
            if self.state.hyperfocus_ticks_remaining > 0:
                self.state.hyperfocus_ticks_remaining -= 1
                self.state.current_task_ticks_spent += 1
                tick_log.phase = AgentPhase.HYPERFOCUSING.name
                tick_log.monologue = self.rng.choice(MONOLOGUES["hyperfocus_continue"])
                tick_log.outcome = "hyperfocus_continue"
                week_log.hyperfocus_ticks += 1
                self.total_hyperfocus_ticks += 1

                # Check if task completes during hyperfocus
                if self.state.current_task_ticks_spent >= self.state.current_task_ticks_needed:
                    msg = self._complete_current_task(week, tick, tick_log)
                    if msg:
                        response_messages.append(msg)
                    week_log.tasks_completed.append(self.state.current_task_key or "?")
                    # Post-hyperfocus dopamine crash
                    self.state.decay_dopamine(0.15)

                tick_log.cognitive_snapshot = self.state.snapshot()
                week_log.ticks.append(tick_log)
                continue

            # --- Per-tick dopamine decay ---
            self.state.decay_dopamine(0.03)
            # Monday morning: partial dopamine reset (weekend recharge)
            if tick == 0:
                if self.state.dopamine_level < 0.4:
                    self.state.dopamine_level = 0.4

            # --- SCANNING phase ---
            self.state.phase = AgentPhase.SCANNING
            tick_log.phase = AgentPhase.SCANNING.name
            tick_log.monologue = self.rng.choice(MONOLOGUES["scanning"])

            task_pool = self._scan_queries(tick, visible_topics, week, tick_log, week_log)

            # Monday nudge: anti-object-permanence — query what you're forgetting
            if tick == 0:
                forgetting = self.graph.query_forgetting("You", week.monday.isoformat())
                tick_log.tool_actions.append(f"query:forgetting({len(forgetting)} results)")
                self.total_queries_executed += 1
                week_log.queries_executed += 1
                # Inject high-frustration tasks into the pool
                seen_descs = {t.get("task") for t in task_pool}
                for f in forgetting[:3]:  # top 3 most frustrating
                    if f.get("task") and f["task"] not in seen_descs:
                        seen_descs.add(f["task"])
                        task_pool.append(f)

            if not task_pool:
                self.state.phase = AgentPhase.IDLE
                self.state.decay_dopamine()
                tick_log.outcome = "idle_no_tasks"
                tick_log.cognitive_snapshot = self.state.snapshot()
                week_log.ticks.append(tick_log)
                continue

            # --- EVALUATING phase ---
            self.state.phase = AgentPhase.EVALUATING
            scored = []
            for t in task_pool:
                icnu = score_task(t, self.state, week, self.seen_types)
                scored.append((icnu, t))
                tk = t.get("task", "?")
                tick_log.icnu_scores[tk] = {
                    "I": icnu.interest, "C": icnu.challenge,
                    "N": icnu.novelty, "U": icnu.urgency,
                    "total": round(icnu.total, 2),
                }

            scored.sort(key=lambda x: x[0].total, reverse=True)

            # Load top tasks into working memory
            for icnu, t in scored[:self.state.working_memory_capacity]:
                self.state.push_to_memory(t.get("task", "?"))

            # Friday guilt: confront a dreaded task
            # (simulates "oh god I've been avoiding this all week")
            if tick == 4 and self.state.dopamine_level < 0.5:
                dreaded = [(s, t) for s, t in scored if s.interest == 0.0 and s.challenge <= 0.2]
                if dreaded:
                    worst_icnu, worst_task = dreaded[0]
                    scored = [(worst_icnu, worst_task)] + [x for x in scored if x[1] is not worst_task]
                    tick_log.monologue = "It's Friday. I've been avoiding this all week. I have to at least try..."

            best_icnu, best_task = scored[0]

            # --- Wall of Awful check ---
            # Triggers based on interest+challenge (intrinsic motivation),
            # NOT urgency. A task can be urgent and still dreaded.
            wall_trigger = check_wall_of_awful(
                best_icnu.interest, best_icnu.challenge,
                self.state.dopamine_level, self.state,
            )
            if wall_trigger:
                tick_log.monologue = self.rng.choice(MONOLOGUES["wall_of_awful"])
                tick_log.outcome = "wall_of_awful"
                week_log.distraction_loop_ticks += 1
                self.total_distraction_ticks += 1
                tick_log.cognitive_snapshot = self.state.snapshot()
                week_log.ticks.append(tick_log)
                continue

            # --- Executive dysfunction check ---
            if check_executive_dysfunction(best_icnu.total, self.state.dopamine_level, self.state):
                tick_log.monologue = self.rng.choice(MONOLOGUES["executive_dysfunction"])
                tick_log.outcome = "executive_dysfunction"
                self.state.decay_dopamine(0.05)
                tick_log.cognitive_snapshot = self.state.snapshot()
                week_log.ticks.append(tick_log)
                continue

            # --- Capture friction check ---
            desc = best_task.get("task", "")
            steps_needed = 2 + (1 if best_task.get("project") else 0)  # query + context + project
            if check_capture_friction(steps_needed, self.state.friction_tolerance, self.rng):
                tick_log.monologue = self.rng.choice(MONOLOGUES["friction_abandon"])
                tick_log.outcome = "friction_abandon"
                week_log.thought_lost_events += 1
                self.total_thought_lost += 1
                self.total_tasks_abandoned.append(desc)
                week_log.tasks_abandoned.append(desc)
                tick_log.cognitive_snapshot = self.state.snapshot()
                week_log.ticks.append(tick_log)
                continue

            # --- WORKING phase ---
            actual_ticks = estimate_task_ticks(desc)
            perceived = estimate_perceived_ticks(actual_ticks, self.state.time_perception_skew)
            week_log.time_blindness_offset += (actual_ticks - perceived)
            self.total_time_blindness_offset += (actual_ticks - perceived)

            self.state.current_task_key = desc
            self.state.current_task_ticks_needed = actual_ticks
            self.state.current_task_ticks_spent = 1
            self.state.phase = AgentPhase.WORKING

            # Check for hyperfocus trigger
            hf_ticks = should_trigger_hyperfocus(
                best_icnu.interest, best_icnu.challenge,
                self.state.dopamine_level, self.rng,
            )
            if hf_ticks > 0:
                self.state.hyperfocus_ticks_remaining = hf_ticks
                self.state.hyperfocus_topic = best_task.get("project") or self.state.hyperfocus_topic
                self.state.hyperfocus_task_key = desc
                self.state.phase = AgentPhase.HYPERFOCUSING
                tick_log.monologue = self.rng.choice(MONOLOGUES["hyperfocus_start"])
                tick_log.outcome = "hyperfocus_start"
                self.total_hyperfocus_episodes += 1
                week_log.hyperfocus_ticks += 1
                self.total_hyperfocus_ticks += 1
            else:
                tick_log.monologue = self.rng.choice(MONOLOGUES["working"])
                tick_log.outcome = "working"

            # Check if single-tick task completes immediately
            if self.state.current_task_ticks_spent >= self.state.current_task_ticks_needed:
                msg = self._complete_current_task(week, tick, tick_log)
                if msg:
                    response_messages.append(msg)
                week_log.tasks_completed.append(desc)
                self.icnu_completion_drivers[best_icnu.max_component] += 1

            tick_log.cognitive_snapshot = self.state.snapshot()
            week_log.ticks.append(tick_log)

        # End of week: track in-progress tasks
        if self.state.current_task_key and self.state.current_task_ticks_spent < self.state.current_task_ticks_needed:
            week_log.tasks_in_progress.append(self.state.current_task_key)

        week_log.messages_sent = len(response_messages)
        week_log.cognitive_end = self.state.snapshot()
        self.weekly_logs.append(week_log)

        return response_messages

    # --- Internal methods ---

    def _extract_visible_topics(self, incoming: list[SimMessage]) -> set[str]:
        """Extract keywords from this week's messages for Object Permanence."""
        topics: set[str] = set()
        for msg in incoming:
            text = msg.text.lower()
            for word in text.split():
                if len(word) > 3:
                    topics.add(word)
            # Add project names and sender names
            for proj in msg.extraction.projects:
                topics.add(proj.name.lower())
            topics.add(msg.source_meta.sender_name.lower())
        return topics

    def _shift_hyperfocus(self, week: SimWeek):
        """Periodically shift hyperfocus to a different project (novelty seeking)."""
        projects = list(self.graph.projects.keys())
        if projects:
            self.state.hyperfocus_topic = self.rng.choice(projects)

    def _scan_queries(
        self,
        tick: int,
        visible_topics: set[str],
        week: SimWeek,
        tick_log: TickLog,
        week_log: WeekLog,
    ) -> list[dict]:
        """Run queries filtered by Object Permanence. Return task pool."""
        task_pool: list[dict] = []
        seen_descs: set[str] = set()

        query_methods = [
            ("tasks_by_assignee", lambda: self.graph.query_tasks_by_assignee("You")),
            ("hanging_tasks", lambda: self.graph.query_hanging_tasks()),
            ("overdue_tasks", lambda: self.graph.query_overdue_tasks(week.monday.isoformat())),
            ("tasks_due_between", lambda: self.graph.query_tasks_due_between(
                week.monday.isoformat(),
                (week.monday + timedelta(days=6)).isoformat(),
            )),
            ("project_overview", lambda: self.graph.query_project_overview()),
        ]

        for query_type, query_fn in query_methods:
            if check_object_permanence(query_type, visible_topics, tick, self.rng):
                results = query_fn()
                tick_log.tool_actions.append(f"query:{query_type}({len(results)} results)")
                self.total_queries_executed += 1
                week_log.queries_executed += 1
                for r in results:
                    desc = r.get("task", "")
                    if desc and desc not in seen_descs:
                        seen_descs.add(desc)
                        task_pool.append(r)
            else:
                tick_log.tool_actions.append(f"skipped:{query_type} (object permanence)")
                self.total_queries_skipped += 1
                week_log.queries_skipped_object_permanence += 1

        # Also do a vector search for context
        if check_object_permanence("search_context", visible_topics, tick, self.rng):
            search_terms = {1: "phoenix design", 2: "milestone blocked", 3: "deployment", 4: "review"}
            q = search_terms.get(week.quarter, "tasks")
            self.vector.search_context(q, n_results=3)
            tick_log.tool_actions.append(f"query:search_context('{q}')")
            self.total_queries_executed += 1
            week_log.queries_executed += 1

        return task_pool

    def _complete_current_task(
        self, week: SimWeek, tick: int, tick_log: TickLog,
    ) -> SimMessage | None:
        """Mark current task done and generate a response message."""
        desc = self.state.current_task_key
        if not desc:
            return None

        # Mark done in graph
        self.graph.mark_task_done(desc)
        self.total_tasks_completed.append(desc)
        self.state.boost_dopamine(0.2)
        tick_log.monologue = self.rng.choice(MONOLOGUES["task_complete"])
        tick_log.outcome = "task_complete"
        tick_log.tool_actions.append(f"mark_done:{desc}")

        # Reset working state
        self.state.current_task_key = None
        self.state.current_task_ticks_spent = 0
        self.state.current_task_ticks_needed = 0
        if self.state.hyperfocus_ticks_remaining <= 0:
            self.state.phase = AgentPhase.SCANNING

        # Generate response message
        return self._make_response(week, tick, desc)

    def _make_response(self, week: SimWeek, tick: int, task_desc: str) -> SimMessage:
        """Create a response SimMessage for a completed task."""
        self._msg_counter += 1
        msg_id = f"you_w{week.week_number}_t{tick}_{self._msg_counter}"
        ts = SimClock.date_in_week(week, weekday=tick, hour=14)

        source_meta = SourceMetadata(
            source_id=msg_id,
            platform=Platform.SLACK,
            sender_name="You",
            sender_email="you@company.com",
            received_at=ts,
        )

        # Determine response text based on task type
        desc_lower = task_desc.lower()
        if "review" in desc_lower:
            text = f"Reviewed and approved. {task_desc} is done. Let me know if there are follow-ups."
        elif "submit" in desc_lower or "send" in desc_lower:
            text = f"Done — submitted. {task_desc}"
        else:
            text = f"Finished: {task_desc}. Moving on to the next thing."

        extraction = ExtractionResult(
            people=[PersonEntity(name="You", email="you@company.com")],
            tasks=[TaskEntity(description=task_desc, status="done")],
            summary=f"You completed: {task_desc}",
        )

        return SimMessage(
            text=text,
            source_meta=source_meta,
            extraction=extraction,
            resolves_tasks=[task_desc],
        )
