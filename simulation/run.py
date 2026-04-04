"""Simulation runner — entry point and pytest integration."""

from simulation.agents.adhd_user import ADHDUserAgent
from simulation.agents.base import SimState
from simulation.agents.coworker import SarahChenAgent
from simulation.agents.director import RobertKimAgent
from simulation.agents.manager import LindaTorresAgent
from simulation.agents.report_marcus import MarcusWebbAgent
from simulation.agents.report_priya import PriyaPatelAgent
from simulation.agents.user import UserAgent
from simulation.clock import SimClock
from simulation.reports.adhd_report import ADHDReportGenerator, ADHDSimulationReport
from simulation.reports.gap_analyzer import GapAnalyzer, SimulationReport
from simulation.sim_pipeline import SimPipeline
from simulation.stores import InMemoryGraphStore, InMemoryVectorStore


def run_simulation(
    verbose: bool = False,
    use_adhd_agent: bool = True,
    seed: int = 42,
) -> tuple[SimulationReport | ADHDSimulationReport, str]:
    """Run the full 12-month office simulation.

    Args:
        verbose: Print weekly progress.
        use_adhd_agent: Use ADHD cognitive model (True) or passive UserAgent (False).
        seed: Random seed for ADHD agent reproducibility.

    Returns:
        (report, formatted_text)
    """
    graph = InMemoryGraphStore()
    vector = InMemoryVectorStore()
    pipeline = SimPipeline(graph, vector)
    state = SimState()
    clock = SimClock()

    office_agents = [
        LindaTorresAgent(),
        RobertKimAgent(),
        SarahChenAgent(),
        MarcusWebbAgent(),
        PriyaPatelAgent(),
    ]

    if use_adhd_agent:
        adhd_agent = ADHDUserAgent(graph, vector, seed=seed)
    else:
        user_agent = UserAgent(graph, vector)

    for week in clock.weeks():
        state.current_week = week.week_number

        # 1. Office agents generate messages
        week_messages = []
        for agent in office_agents:
            messages = agent.generate_messages(week, state)
            week_messages.extend(messages)

        # 2. Ingest office messages
        for msg in week_messages:
            pipeline.ingest(msg.text, msg.source_meta, msg.extraction)
            state.record_message(msg)
            for task_desc in msg.resolves_tasks:
                graph.mark_task_done(task_desc)

        # 3. Agent processes the week
        if use_adhd_agent:
            response_msgs = adhd_agent.run_weekly(week, state, week_messages)
            for msg in response_msgs:
                pipeline.ingest(msg.text, msg.source_meta, msg.extraction)
                state.record_message(msg)
                for task_desc in msg.resolves_tasks:
                    graph.mark_task_done(task_desc)
        else:
            user_agent.run_weekly_queries(week)

        if verbose:
            n_msgs = len(week_messages)
            n_tasks = sum(len(m.extraction.tasks) for m in week_messages)
            if use_adhd_agent:
                cog = adhd_agent.state
                done = len(adhd_agent.total_tasks_completed)
                print(f"  W{week.week_number:2d} Q{week.quarter}: "
                      f"{n_msgs} msgs, {n_tasks} tasks | "
                      f"DA={cog.dopamine_level:.2f} phase={cog.phase.name:20s} "
                      f"done={done} resp={len(response_msgs)}")
            elif week_messages:
                print(f"  W{week.week_number:2d} Q{week.quarter}: "
                      f"{n_msgs} msgs, {n_tasks} tasks")

    # Generate report
    if use_adhd_agent:
        gen = ADHDReportGenerator(adhd_agent, state, graph, vector)
        report = gen.generate_report()
        formatted = gen.format_report(report)
    else:
        analyzer = GapAnalyzer(user_agent, state, graph, vector)
        report = analyzer.generate_report()
        formatted = analyzer.format_report(report)

    return report, formatted


# === Pytest: passive UserAgent tests (backward compat) ===

def test_passive_simulation_runs():
    """Passive UserAgent simulation completes."""
    report, _ = run_simulation(use_adhd_agent=False)
    assert report.total_messages > 100
    assert report.total_tasks > 50


def test_passive_all_queries_succeed():
    """Passive agent: all queries at 100%."""
    report, _ = run_simulation(use_adhd_agent=False)
    for qt, stats in report.query_stats.items():
        assert stats["rate"] == "100%", f"Query {qt} failed: {stats}"


def test_passive_tasks_resolve():
    report, _ = run_simulation(use_adhd_agent=False)
    assert report.tasks_resolved > 5


def test_passive_recommendations_implemented():
    report, _ = run_simulation(use_adhd_agent=False)
    assert len(report.implemented_features) == 8


# === Pytest: ADHD agent tests ===

def test_adhd_simulation_runs():
    """ADHD agent simulation completes without errors."""
    report, _ = run_simulation(use_adhd_agent=True)
    assert report.total_tasks_seen > 50
    assert report.tasks_completed > 0


def test_adhd_completion_rate_below_100():
    """ADHD agent should NOT complete all tasks (that's the point)."""
    report, _ = run_simulation(use_adhd_agent=True)
    assert report.completion_rate < 1.0, "ADHD agent should not complete everything"
    assert report.completion_rate > 0.0, "ADHD agent should complete something"


def test_adhd_hyperfocus_occurs():
    """ADHD agent should enter hyperfocus at least once."""
    report, _ = run_simulation(use_adhd_agent=True)
    assert report.hyperfocus_episodes > 0


def test_adhd_distraction_occurs():
    """ADHD agent should experience distraction loops."""
    report, _ = run_simulation(use_adhd_agent=True)
    assert report.distraction_loop_ticks > 0 or report.wall_of_awful_triggers > 0


def test_adhd_object_permanence_misses():
    """ADHD agent should skip some queries due to object permanence."""
    report, _ = run_simulation(use_adhd_agent=True)
    assert report.object_permanence_misses > 0


def test_adhd_generates_responses():
    """ADHD agent should generate response messages when completing tasks."""
    report, _ = run_simulation(use_adhd_agent=True)
    assert report.messages_sent > 0


def test_adhd_deterministic_with_seed():
    """Same seed should produce identical results."""
    r1, _ = run_simulation(use_adhd_agent=True, seed=42)
    r2, _ = run_simulation(use_adhd_agent=True, seed=42)
    assert r1.tasks_completed == r2.tasks_completed
    assert r1.hyperfocus_episodes == r2.hyperfocus_episodes


def test_adhd_graph_integrity():
    """Graph should have expected structure after ADHD simulation."""
    report, _ = run_simulation(use_adhd_agent=True)
    assert report.total_persons >= 5
    assert report.total_projects >= 2
    assert report.total_edges > 100


# === CLI entry point ===

if __name__ == "__main__":
    import sys
    mode = "adhd"
    if "--passive" in sys.argv:
        mode = "passive"

    if mode == "adhd":
        print("Running 12-month ADHD employee simulation...\n")
        report, text = run_simulation(verbose=True, use_adhd_agent=True)
    else:
        print("Running 12-month passive simulation...\n")
        report, text = run_simulation(verbose=True, use_adhd_agent=False)

    print()
    print(text)
