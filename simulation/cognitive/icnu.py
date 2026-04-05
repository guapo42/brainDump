"""ICNU scoring engine — Interest, Challenge, Novelty, Urgency."""

from __future__ import annotations

from datetime import timedelta

from simulation.clock import SimWeek
from simulation.cognitive.state import CognitiveState, ICNUScore

# Keywords that indicate challenge/complexity
CHALLENGE_HIGH = {"architecture", "design", "debug", "investigate", "optimize", "refactor", "migrate"}
CHALLENGE_MED = {"review", "implement", "build", "integrate", "write", "fix"}
CHALLENGE_LOW = {"submit", "forward", "confirm", "complete", "send", "reply", "attend", "schedule"}

# Keywords that indicate admin/boring tasks
ADMIN_KEYWORDS = {"timesheet", "enrollment", "compliance", "training", "pto", "leave",
                  "budget", "self-assessment", "self-review", "check-in", "accomplishments"}


def score_task(
    task: dict,
    state: CognitiveState,
    week: SimWeek,
    seen_types: set[str],
) -> ICNUScore:
    """Score a task using the ICNU framework instead of standard priority.

    Frustration score (if present on the task dict) boosts urgency.
    This is how "someone asked 3 times and sounds frustrated" translates
    into the one ICNU dimension that can break through executive dysfunction.
    """
    desc = task.get("task", task.get("description", "")).lower()
    project = task.get("project") or ""
    due_date = task.get("due_date")
    words = set(desc.split())

    interest = _score_interest(desc, project, state)
    challenge = _score_challenge(words)
    novelty = _score_novelty(desc, seen_types)
    urgency = _score_urgency(due_date, week)

    # Frustration boost: convert stakeholder frustration into urgency
    frustration = task.get("frustration_score", 0)
    if frustration > 0:
        # Normalize frustration (typically 0-60) to a 0-0.5 boost
        frustration_boost = min(frustration / 40, 0.5)
        urgency = min(1.0, urgency + frustration_boost)

        # Context reasons provide additional urgency signals
        reasons = task.get("context_reasons", [])
        for reason in reasons:
            if "escalat" in reason:
                urgency = min(1.0, urgency + 0.15)
            if "teammate" in reason or "progress" in reason:
                # Social proof: peers are doing their part
                interest = min(1.0, interest + 0.1)
            if "follow-up" in reason:
                urgency = min(1.0, urgency + 0.1)

    return ICNUScore(
        interest=round(interest, 2),
        challenge=round(challenge, 2),
        novelty=round(novelty, 2),
        urgency=round(urgency, 2),
    )


def _score_interest(desc: str, project: str, state: CognitiveState) -> float:
    """High if matches hyperfocus topic, zero for admin."""
    # Admin tasks are never interesting
    if any(kw in desc for kw in ADMIN_KEYWORDS):
        return 0.0

    # Hyperfocus alignment
    if state.hyperfocus_topic:
        topic = state.hyperfocus_topic.lower()
        if topic in desc or topic in project.lower():
            return 0.9
        # Related to same project gets a boost
        if project and project.lower() == topic:
            return 0.8

    # Technical tasks have baseline interest
    words = set(desc.split())
    if words & CHALLENGE_HIGH:
        return 0.5
    if words & CHALLENGE_MED:
        return 0.3
    return 0.1


def _score_challenge(words: set[str]) -> float:
    """Keyword-based complexity assessment."""
    if words & CHALLENGE_HIGH:
        return 0.9
    if words & CHALLENGE_MED:
        return 0.5
    if words & CHALLENGE_LOW:
        return 0.1
    return 0.3  # unknown tasks get medium challenge


def _score_novelty(desc: str, seen_types: set[str]) -> float:
    """First encounter of a task pattern scores high, decays on repeats."""
    # Derive a "type" from the task description
    task_type = _classify_task_type(desc)

    count = sum(1 for s in seen_types if s == task_type)
    seen_types.add(task_type)

    if count == 0:
        return 1.0
    elif count == 1:
        return 0.5
    elif count == 2:
        return 0.2
    return 0.0


def _classify_task_type(desc: str) -> str:
    """Classify task into a type category for novelty tracking."""
    desc_lower = desc.lower()
    if "review" in desc_lower and "pr" in desc_lower:
        return "pr_review"
    if "review" in desc_lower:
        return "document_review"
    if any(w in desc_lower for w in ("architecture", "design")):
        return "architecture"
    if any(w in desc_lower for w in ("deploy", "provision", "staging")):
        return "deployment"
    if any(w in desc_lower for w in ("test", "testing")):
        return "testing"
    if any(w in desc_lower for w in ("submit", "send", "forward")):
        return "admin_submit"
    if any(w in desc_lower for w in ("write", "document", "prepare")):
        return "writing"
    if any(w in desc_lower for w in ("fix", "debug", "bug")):
        return "debugging"
    if any(w in desc_lower for w in ("implement", "build", "create")):
        return "implementation"
    return "other"


def _score_urgency(due_date: str | None, week: SimWeek) -> float:
    """Due within 2 weeks = high urgency. Overdue = shame-reduced urgency."""
    if not due_date:
        return 0.0

    today = week.monday.isoformat()

    if due_date < today:
        # Overdue: shame/avoidance reduces urgency below crisis level
        return 0.6

    # Days until due
    due_parts = due_date.split("-")
    from datetime import date
    try:
        due = date(int(due_parts[0]), int(due_parts[1]), int(due_parts[2]))
    except (ValueError, IndexError):
        return 0.0

    days_until = (due - week.monday).days

    if days_until <= 7:
        return 1.0
    elif days_until <= 14:
        return 0.7
    elif days_until <= 28:
        return 0.3
    return 0.0


def estimate_task_ticks(desc: str) -> int:
    """Estimate actual ticks needed for a task."""
    desc_lower = desc.lower()
    words = set(desc_lower.split())

    if words & CHALLENGE_LOW or any(kw in desc_lower for kw in ADMIN_KEYWORDS):
        return 1
    if "review" in desc_lower:
        return 2
    if words & CHALLENGE_HIGH:
        return 3
    return 2  # default
