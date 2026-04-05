"""Behavioral rules: Wall of Awful, Object Permanence, Capture Friction."""

from __future__ import annotations

import math
import random as _random

from simulation.cognitive.state import AgentPhase, CognitiveState


def check_wall_of_awful(
    interest: float, challenge: float, urgency: float,
    dopamine: float, state: CognitiveState,
) -> bool:
    """Wall of Awful: can't start tasks with no intrinsic motivation.

    The key ADHD insight: a task can be urgent AND dreaded. But high enough
    external pressure (urgency >= 0.9, from frustration/deadline panic) can
    break through. This models the "I literally cannot put this off any longer"
    moment. The frustration score feeds into urgency via ICNU scoring.

    Returns True if the Wall was triggered.
    """
    # Panic override: extreme urgency (frustration-boosted) breaks through
    if urgency >= 0.9:
        return False

    engagement = interest + challenge  # intrinsic motivation
    if engagement <= 0.2 and dopamine < 0.5:
        state.distraction_ticks_remaining = 3
        state.phase = AgentPhase.DISTRACTION_LOOP
        return True
    if engagement <= 0.1:
        state.distraction_ticks_remaining = 2
        state.phase = AgentPhase.DISTRACTION_LOOP
        return True
    return False


def check_object_permanence(
    query_type: str,
    visible_topics: set[str],
    tick: int,
    rng: _random.Random,
) -> bool:
    """Decide if this query will be executed.

    Tick 0 (Monday) always executes all queries — the "morning scan."
    Ticks 1-4: invisible queries have 40% chance of being skipped.

    Returns True if the query SHOULD be executed.
    """
    if tick == 0:
        return True

    # Check if query is "visible" — related to something that arrived this week
    visible_map = {
        "hanging_tasks": {"blocked", "waiting", "stuck"},
        "overdue_tasks": {"overdue", "late", "past due", "deadline"},
        "tasks_by_assignee": {"your", "assigned", "you need"},
        "tasks_from_sender": set(),  # always invisible unless name matches
        "tasks_due_between": {"due", "deadline", "this week"},
        "project_overview": {"project", "phoenix", "epa"},
        "search_context": set(),
    }

    keywords = visible_map.get(query_type, set())
    if keywords & visible_topics:
        return True

    # 40% chance of forgetting invisible queries
    return rng.random() > 0.4


def check_capture_friction(
    steps_needed: int,
    friction_tolerance: int,
    rng: _random.Random,
) -> bool:
    """If steps exceed tolerance, 70% chance of abandoning.

    Returns True if the agent ABANDONS the task.
    """
    if steps_needed <= friction_tolerance:
        return False
    return rng.random() < 0.7


def check_executive_dysfunction(
    icnu_total: float,
    dopamine_level: float,
    state: CognitiveState,
) -> bool:
    """Low ICNU + low dopamine = executive dysfunction stall.

    Returns True if stalled.
    """
    if icnu_total < 0.5 and dopamine_level < 0.2:
        state.phase = AgentPhase.EXECUTIVE_DYSFUNCTION
        return True
    return False


def should_trigger_hyperfocus(
    interest: float,
    challenge: float,
    dopamine: float,
    rng: _random.Random,
) -> int:
    """Check if task triggers hyperfocus. Returns ticks (0 = no hyperfocus).

    Hyperfocus requires high interest AND challenge, and is less likely
    when dopamine is depleted (post-crash). ~20% base chance.
    """
    # Can't hyperfocus when dopamine-crashed
    if dopamine < 0.2:
        return 0

    if interest >= 0.8 and challenge >= 0.7:
        if rng.random() < 0.35:
            return rng.randint(2, 3)
    if interest >= 0.9:
        if rng.random() < 0.2:
            return 2
    return 0


def estimate_perceived_ticks(actual_ticks: int, skew: float) -> int:
    """Agent's perception of how long a task will take (always underestimates)."""
    return max(1, math.ceil(actual_ticks * skew))
