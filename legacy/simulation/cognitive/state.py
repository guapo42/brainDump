"""Cognitive state model for the ADHD employee agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class AgentPhase(Enum):
    SCANNING = auto()
    EVALUATING = auto()
    WORKING = auto()
    HYPERFOCUSING = auto()
    DISTRACTION_LOOP = auto()
    RESPONDING = auto()
    EXECUTIVE_DYSFUNCTION = auto()
    IDLE = auto()


@dataclass
class ICNUScore:
    """Interest-Challenge-Novelty-Urgency score for a task."""
    interest: float = 0.0
    challenge: float = 0.0
    novelty: float = 0.0
    urgency: float = 0.0

    @property
    def total(self) -> float:
        return self.interest + self.challenge + self.novelty + self.urgency

    @property
    def max_component(self) -> str:
        components = {
            "interest": self.interest, "challenge": self.challenge,
            "novelty": self.novelty, "urgency": self.urgency,
        }
        return max(components, key=components.get)


@dataclass
class CognitiveState:
    """Internal cognitive variables updated each tick."""
    dopamine_level: float = 0.5
    working_memory: list[str] = field(default_factory=list)
    working_memory_capacity: int = 3
    friction_tolerance: int = 3
    time_perception_skew: float = 0.6
    phase: AgentPhase = AgentPhase.SCANNING

    hyperfocus_topic: Optional[str] = None
    hyperfocus_ticks_remaining: int = 0
    hyperfocus_task_key: Optional[str] = None
    distraction_ticks_remaining: int = 0

    current_tick: int = 0
    current_task_key: Optional[str] = None
    current_task_ticks_spent: int = 0
    current_task_ticks_needed: int = 0

    def snapshot(self) -> dict:
        return {
            "dopamine": round(self.dopamine_level, 2),
            "phase": self.phase.name,
            "working_memory": list(self.working_memory),
            "hyperfocus_topic": self.hyperfocus_topic,
            "hyperfocus_remaining": self.hyperfocus_ticks_remaining,
            "distraction_remaining": self.distraction_ticks_remaining,
        }

    def push_to_memory(self, task_key: str):
        """Add to working memory, evict oldest if full."""
        if task_key in self.working_memory:
            return
        if len(self.working_memory) >= self.working_memory_capacity:
            self.working_memory.pop(0)
        self.working_memory.append(task_key)

    def boost_dopamine(self, amount: float):
        self.dopamine_level = min(1.0, self.dopamine_level + amount)

    def decay_dopamine(self, amount: float = 0.05):
        self.dopamine_level = max(0.0, self.dopamine_level - amount)


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


@dataclass
class TickLog:
    """Log entry for a single tick (one workday)."""
    week: int
    tick: int
    weekday: str
    phase: str
    monologue: str
    tool_actions: list[str] = field(default_factory=list)
    cognitive_snapshot: dict = field(default_factory=dict)
    icnu_scores: dict[str, dict] = field(default_factory=dict)
    outcome: str = ""


@dataclass
class WeekLog:
    """Summary of one simulated work week."""
    week_number: int
    cognitive_start: dict = field(default_factory=dict)
    cognitive_end: dict = field(default_factory=dict)
    ticks: list[TickLog] = field(default_factory=list)
    tasks_completed: list[str] = field(default_factory=list)
    tasks_abandoned: list[str] = field(default_factory=list)
    tasks_in_progress: list[str] = field(default_factory=list)
    messages_sent: int = 0
    queries_executed: int = 0
    queries_skipped_object_permanence: int = 0
    thought_lost_events: int = 0
    distraction_loop_ticks: int = 0
    hyperfocus_ticks: int = 0
    time_blindness_offset: float = 0.0
