"""Simulation runner — entry point and pytest integration."""

from simulation.agents.base import SimState
from simulation.agents.coworker import SarahChenAgent
from simulation.agents.director import RobertKimAgent
from simulation.agents.manager import LindaTorresAgent
from simulation.agents.report_marcus import MarcusWebbAgent
from simulation.agents.report_priya import PriyaPatelAgent
from simulation.agents.user import UserAgent
from simulation.clock import SimClock
from simulation.reports.gap_analyzer import GapAnalyzer, SimulationReport
from simulation.sim_pipeline import SimPipeline
from simulation.stores import InMemoryGraphStore, InMemoryVectorStore


def run_simulation(verbose: bool = False) -> tuple[SimulationReport, str]:
    """Run the full 12-month office simulation.

    Returns:
        (report, formatted_text) — structured report and human-readable output.
    """
    # Initialize infrastructure
    graph = InMemoryGraphStore()
    vector = InMemoryVectorStore()
    pipeline = SimPipeline(graph, vector)
    state = SimState()
    clock = SimClock()

    # Initialize agents
    office_agents = [
        LindaTorresAgent(),
        RobertKimAgent(),
        SarahChenAgent(),
        MarcusWebbAgent(),
        PriyaPatelAgent(),
    ]
    user_agent = UserAgent(graph, vector)

    # Main simulation loop
    for week in clock.weeks():
        state.current_week = week.week_number

        # 1. Each office agent generates messages for this week
        week_messages = []
        for agent in office_agents:
            messages = agent.generate_messages(week, state)
            week_messages.extend(messages)

        # 2. Ingest all messages
        for msg in week_messages:
            pipeline.ingest(msg.text, msg.source_meta, msg.extraction)
            state.record_message(msg)

            # Resolve tasks that this message marks as done
            for task_desc in msg.resolves_tasks:
                graph.mark_task_done(task_desc)

        # 3. User agent queries the system
        user_agent.run_weekly_queries(week)

        if verbose and week_messages:
            print(f"  Week {week.week_number:2d} (Q{week.quarter}): "
                  f"{len(week_messages)} messages, "
                  f"{sum(len(m.extraction.tasks) for m in week_messages)} tasks")

    # Generate report
    analyzer = GapAnalyzer(user_agent, state, graph, vector)
    report = analyzer.generate_report()
    formatted = analyzer.format_report(report)

    return report, formatted


# === Pytest integration ===

def test_simulation_runs_successfully():
    """Full simulation completes without errors."""
    report, text = run_simulation()
    assert report.total_messages > 100, f"Expected >100 messages, got {report.total_messages}"
    assert report.total_tasks > 50, f"Expected >50 tasks, got {report.total_tasks}"


def test_simulation_all_queries_succeed():
    """All production queries should run at 100% success rate."""
    report, _ = run_simulation()
    for qt, stats in report.query_stats.items():
        assert stats["rate"] == "100%", f"Query {qt} failed: {stats}"


def test_simulation_tasks_resolve():
    """Some tasks should move to 'done' over the course of the simulation."""
    report, _ = run_simulation()
    assert report.tasks_resolved > 5, f"Expected >5 resolved tasks, got {report.tasks_resolved}"


def test_simulation_finds_overdue_tasks():
    """Tasks with passed due dates that aren't done should be flagged."""
    report, _ = run_simulation()
    assert report.tasks_overdue > 0, "Should find overdue tasks"


def test_simulation_recommendations_implemented():
    """All 8 recommendations should be marked as IMPLEMENTED."""
    report, _ = run_simulation()
    assert len(report.implemented_features) == 8, (
        f"Expected 8 implemented features, got {len(report.implemented_features)}"
    )
    for feat in report.implemented_features:
        assert feat["status"] == "IMPLEMENTED", f"{feat['id']} not implemented"


def test_simulation_graph_integrity():
    """Graph should have the expected structure after full simulation."""
    report, _ = run_simulation()
    assert report.total_persons >= 5, f"Expected >=5 persons, got {report.total_persons}"
    assert report.total_projects >= 2, f"Expected >=2 projects, got {report.total_projects}"
    assert report.total_edges > 100, f"Expected >100 edges, got {report.total_edges}"


def test_simulation_new_queries_return_data():
    """The new REC-5/6/7/8 queries should return actual results."""
    graph = InMemoryGraphStore()
    vector = InMemoryVectorStore()
    pipeline = SimPipeline(graph, vector)
    state = SimState()
    clock = SimClock()

    agents = [
        LindaTorresAgent(), RobertKimAgent(), SarahChenAgent(),
        MarcusWebbAgent(), PriyaPatelAgent(),
    ]

    # Run first 10 weeks to build up data
    for week in clock.weeks():
        if week.week_number > 10:
            break
        for agent in agents:
            for msg in agent.generate_messages(week, state):
                pipeline.ingest(msg.text, msg.source_meta, msg.extraction)
                state.record_message(msg)

    # REC-5: Tasks by assignee
    my_tasks = graph.query_tasks_by_assignee("You")
    assert len(my_tasks) > 0, "Should find tasks assigned to You"

    # REC-6: Tasks due between dates
    due = graph.query_tasks_due_between("2026-01-01", "2026-04-01")
    assert len(due) > 0, "Should find tasks due in Q1"

    # REC-7: Tasks from sender
    linda_tasks = graph.query_tasks_from_sender("Linda Torres")
    assert len(linda_tasks) > 0, "Should find tasks from Linda"

    # REC-8: Overdue tasks
    overdue = graph.query_overdue_tasks("2026-04-01")
    assert len(overdue) > 0, "Should find overdue tasks by April"


# === CLI entry point ===

if __name__ == "__main__":
    print("Running 12-month office simulation...\n")
    report, text = run_simulation(verbose=True)
    print()
    print(text)
