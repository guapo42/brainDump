"""ADHD Agent report generator — cognitive metrics, friction analysis, ICNU breakdown."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from simulation.agents.adhd_user import ADHDUserAgent
from simulation.agents.base import SimState
from simulation.stores import InMemoryGraphStore, InMemoryVectorStore


@dataclass
class ADHDSimulationReport:
    """Structured report from the ADHD agent simulation."""
    # Task outcomes
    total_tasks_seen: int = 0
    tasks_completed: int = 0
    tasks_abandoned_friction: int = 0
    tasks_never_seen: int = 0
    tasks_left_in_progress: int = 0
    completion_rate: float = 0.0

    # Cognitive metrics
    avg_dopamine: float = 0.0
    hyperfocus_episodes: int = 0
    total_hyperfocus_ticks: int = 0
    avg_hyperfocus_length: float = 0.0
    distraction_loop_ticks: int = 0
    wall_of_awful_triggers: int = 0
    executive_dysfunction_stalls: int = 0
    thought_lost_events: int = 0
    object_permanence_misses: int = 0

    # Time blindness
    total_time_blindness_offset: float = 0.0

    # Tool usage
    total_queries_executed: int = 0
    total_queries_skipped: int = 0
    messages_sent: int = 0

    # ICNU analysis
    icnu_completion_drivers: dict[str, int] = field(default_factory=dict)

    # Graph stats
    total_messages_ingested: int = 0
    total_tasks_in_graph: int = 0
    total_persons: int = 0
    total_projects: int = 0
    total_edges: int = 0

    # Weekly heatmap data
    weekly_heatmap: list[dict] = field(default_factory=list)


class ADHDReportGenerator:
    """Generates the ADHD simulation report from agent logs."""

    def __init__(
        self,
        agent: ADHDUserAgent,
        state: SimState,
        graph: InMemoryGraphStore,
        vector: InMemoryVectorStore,
    ):
        self.agent = agent
        self.state = state
        self.graph = graph
        self.vector = vector

    def generate_report(self) -> ADHDSimulationReport:
        report = ADHDSimulationReport()

        # Task outcomes
        all_tasks_in_state = set(self.state.tasks_created.keys())
        completed = set(self.agent.total_tasks_completed)
        abandoned = set(self.agent.total_tasks_abandoned)

        report.total_tasks_seen = len(all_tasks_in_state)
        report.tasks_completed = len(completed)
        report.tasks_abandoned_friction = len(abandoned - completed)
        report.tasks_left_in_progress = sum(
            1 for wl in self.agent.weekly_logs for t in wl.tasks_in_progress
        )
        report.tasks_never_seen = len(all_tasks_in_state - completed - abandoned)
        report.completion_rate = (
            report.tasks_completed / report.total_tasks_seen
            if report.total_tasks_seen > 0 else 0.0
        )

        # Cognitive metrics
        dopamine_readings = []
        for wl in self.agent.weekly_logs:
            dopamine_readings.append(wl.cognitive_start.get("dopamine", 0.5))
            dopamine_readings.append(wl.cognitive_end.get("dopamine", 0.5))
        report.avg_dopamine = sum(dopamine_readings) / len(dopamine_readings) if dopamine_readings else 0.5

        report.hyperfocus_episodes = self.agent.total_hyperfocus_episodes
        report.total_hyperfocus_ticks = self.agent.total_hyperfocus_ticks
        report.avg_hyperfocus_length = (
            report.total_hyperfocus_ticks / report.hyperfocus_episodes
            if report.hyperfocus_episodes > 0 else 0.0
        )
        report.distraction_loop_ticks = self.agent.total_distraction_ticks
        report.thought_lost_events = self.agent.total_thought_lost
        report.object_permanence_misses = self.agent.total_queries_skipped
        report.total_time_blindness_offset = self.agent.total_time_blindness_offset

        # Count wall of awful and exec dysfunction from tick logs
        for wl in self.agent.weekly_logs:
            for tl in wl.ticks:
                if tl.outcome == "wall_of_awful":
                    report.wall_of_awful_triggers += 1
                if tl.outcome == "executive_dysfunction":
                    report.executive_dysfunction_stalls += 1

        # Tool usage
        report.total_queries_executed = self.agent.total_queries_executed
        report.total_queries_skipped = self.agent.total_queries_skipped
        report.messages_sent = sum(wl.messages_sent for wl in self.agent.weekly_logs)

        # ICNU
        report.icnu_completion_drivers = dict(self.agent.icnu_completion_drivers)

        # Graph stats
        report.total_messages_ingested = self.state.messages_ingested
        report.total_tasks_in_graph = len(self.graph.tasks)
        report.total_persons = len(self.graph.persons)
        report.total_projects = len(self.graph.projects)
        report.total_edges = len(self.graph.edges)

        # Weekly heatmap
        for wl in self.agent.weekly_logs:
            report.weekly_heatmap.append({
                "week": wl.week_number,
                "done": len(wl.tasks_completed),
                "abandoned": len(wl.tasks_abandoned),
                "hyperfocus": wl.hyperfocus_ticks,
                "distraction": wl.distraction_loop_ticks,
                "queries": wl.queries_executed,
                "skipped": wl.queries_skipped_object_permanence,
            })

        return report

    def format_report(self, report: ADHDSimulationReport) -> str:
        lines = []
        lines.append("=" * 72)
        lines.append("  ADHD AGENT SIMULATION REPORT — Jan-Dec 2026")
        lines.append("=" * 72)

        lines.append("\n## Task Outcomes\n")
        lines.append(f"  Tasks seen by system:       {report.total_tasks_seen}")
        lines.append(f"  Tasks completed:            {report.tasks_completed} ({report.completion_rate:.0%})")
        lines.append(f"  Tasks abandoned (friction):  {report.tasks_abandoned_friction}")
        lines.append(f"  Tasks never seen (obj perm): {report.tasks_never_seen}")
        lines.append(f"  Tasks left in progress:      {report.tasks_left_in_progress}")

        lines.append("\n## Cognitive Metrics\n")
        lines.append(f"  Average dopamine level:      {report.avg_dopamine:.2f}")
        lines.append(f"  Hyperfocus episodes:         {report.hyperfocus_episodes} (avg {report.avg_hyperfocus_length:.1f} ticks)")
        lines.append(f"  Total hyperfocus ticks:      {report.total_hyperfocus_ticks}")
        lines.append(f"  Distraction loop ticks:      {report.distraction_loop_ticks}")
        lines.append(f"  Wall of Awful triggers:      {report.wall_of_awful_triggers}")
        lines.append(f"  Exec dysfunction stalls:     {report.executive_dysfunction_stalls}")
        lines.append(f"  Thought-lost events:         {report.thought_lost_events}")
        lines.append(f"  Object permanence misses:    {report.object_permanence_misses}")

        lines.append("\n## Time Blindness\n")
        lines.append(f"  Total offset (perceived - actual): {report.total_time_blindness_offset:.0f} ticks")

        lines.append("\n## Tool Usage\n")
        lines.append(f"  Queries executed:            {report.total_queries_executed}")
        lines.append(f"  Queries skipped (obj perm):  {report.total_queries_skipped}")
        lines.append(f"  Response messages sent:       {report.messages_sent}")

        lines.append("\n## ICNU Completion Drivers\n")
        for driver, count in sorted(report.icnu_completion_drivers.items(), key=lambda x: -x[1]):
            bar = "#" * count
            lines.append(f"  {driver:12s} {count:3d}  {bar}")

        lines.append("\n## Graph Statistics\n")
        lines.append(f"  Messages ingested:           {report.total_messages_ingested}")
        lines.append(f"  Tasks in graph:              {report.total_tasks_in_graph}")
        lines.append(f"  Persons in graph:            {report.total_persons}")
        lines.append(f"  Projects in graph:           {report.total_projects}")
        lines.append(f"  Graph edges:                 {report.total_edges}")

        lines.append("\n## Weekly Heatmap\n")
        lines.append(f"  {'Week':>4}  {'Done':>4}  {'Aban':>4}  {'HyFo':>4}  {'Dist':>4}  {'Qry':>4}  {'Skip':>4}")
        lines.append(f"  {'----':>4}  {'----':>4}  {'----':>4}  {'----':>4}  {'----':>4}  {'----':>4}  {'----':>4}")
        for w in report.weekly_heatmap:
            lines.append(
                f"  {w['week']:4d}  {w['done']:4d}  {w['abandoned']:4d}  "
                f"{w['hyperfocus']:4d}  {w['distraction']:4d}  "
                f"{w['queries']:4d}  {w['skipped']:4d}"
            )

        lines.append("\n" + "=" * 72)
        return "\n".join(lines)
