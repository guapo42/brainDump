"""Gap Analyzer — generates the final simulation report with recommendations."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from simulation.agents.base import SimState
from simulation.agents.user import QueryAttempt, UserAgent
from simulation.stores import InMemoryGraphStore, InMemoryVectorStore


@dataclass
class SimulationReport:
    """Full simulation report with statistics, gaps, and recommendations."""
    total_messages: int = 0
    total_tasks: int = 0
    tasks_resolved: int = 0
    tasks_hanging: int = 0
    tasks_overdue: int = 0
    total_persons: int = 0
    total_projects: int = 0
    total_edges: int = 0
    query_stats: dict = field(default_factory=dict)
    gaps: list[dict] = field(default_factory=list)
    integrity_issues: list[dict] = field(default_factory=list)
    recommendations: list[dict] = field(default_factory=list)


class GapAnalyzer:
    """Analyzes UserAgent query logs and produces a gap report."""

    def __init__(
        self,
        user_agent: UserAgent,
        state: SimState,
        graph: InMemoryGraphStore,
        vector: InMemoryVectorStore,
    ):
        self.user = user_agent
        self.state = state
        self.graph = graph
        self.vector = vector

    def generate_report(self) -> SimulationReport:
        report = SimulationReport()

        # --- Statistics ---
        report.total_messages = self.state.messages_ingested
        report.total_tasks = len(self.graph.tasks)
        report.tasks_resolved = sum(
            1 for t in self.graph.tasks.values() if t["status"] == "done"
        )
        report.tasks_hanging = len(self.graph.query_hanging_tasks())
        report.tasks_overdue = len([
            i for i in self.user.integrity_issues if i["type"] == "overdue_task"
        ])
        report.total_persons = len(self.graph.persons)
        report.total_projects = len(self.graph.projects)
        report.total_edges = len(self.graph.edges)

        # --- Query coverage ---
        query_types = Counter(q.query_type for q in self.user.query_log)
        query_success = Counter(
            q.query_type for q in self.user.query_log if q.success
        )
        report.query_stats = {
            qt: {
                "attempts": count,
                "successes": query_success.get(qt, 0),
                "rate": f"{query_success.get(qt, 0) / count * 100:.0f}%",
            }
            for qt, count in query_types.items()
        }

        # --- Gaps ---
        gap_queries = [q for q in self.user.query_log if q.gap_id]
        gap_groups: dict[str, list[QueryAttempt]] = {}
        for q in gap_queries:
            gap_groups.setdefault(q.gap_id, []).append(q)

        for gap_id, queries in sorted(gap_groups.items()):
            report.gaps.append({
                "id": gap_id,
                "description": queries[0].gap_description,
                "times_attempted": len(queries),
                "query_type": queries[0].query_type,
            })

        # --- Integrity issues ---
        issue_groups: dict[str, list[dict]] = {}
        for issue in self.user.integrity_issues:
            issue_groups.setdefault(issue["type"], []).append(issue)

        for issue_type, issues in issue_groups.items():
            report.integrity_issues.append({
                "type": issue_type,
                "count": len(issues),
                "first_detected_week": min(i["week"] for i in issues),
                "gap_id": issues[0].get("gap_id"),
                "examples": [i["detail"] for i in issues[:3]],
            })

        # --- Recommendations ---
        report.recommendations = self._build_recommendations(report)

        return report

    def _build_recommendations(self, report: SimulationReport) -> list[dict]:
        recs = []

        # Schema changes
        recs.append({
            "category": "Schema Change",
            "id": "REC-1",
            "title": "Add REQUESTED_BY relationship",
            "detail": (
                "Add (Task)-[:REQUESTED_BY]->(Person) linking the sender of the source "
                "message to the tasks it generated. Without this, the user cannot answer "
                "'What do I owe Linda?' — a question attempted "
                f"{sum(1 for g in report.gaps if g['id'] == 'GAP-3')} gap group(s), "
                f"totaling {sum(g['times_attempted'] for g in report.gaps if g['id'] == 'GAP-3')} queries."
            ),
            "priority": "high",
            "files": ["models/schemas.py", "core/graph_engine.py"],
        })

        recs.append({
            "category": "Schema Change",
            "id": "REC-2",
            "title": "Add task updated_at timestamp and status history",
            "detail": (
                "Tasks need an updated_at field and a status change history. Without this, "
                "temporal queries like 'What did Marcus work on last month?' are impossible. "
                "The weekly summary query was attempted every week but required manual date "
                "filtering on the vector store."
            ),
            "priority": "high",
            "files": ["models/schemas.py", "core/graph_engine.py"],
        })

        recs.append({
            "category": "Schema Change",
            "id": "REC-3",
            "title": "Use composite key for Task identity (description + project)",
            "detail": (
                "Currently tasks MERGE on description alone. The simulation detected "
                f"{len([i for i in report.integrity_issues if i['type'] == 'task_description_collision'])} "
                "task description collision(s) where the same description appeared in different "
                "project contexts and was incorrectly merged."
            ),
            "priority": "medium",
            "files": ["core/graph_engine.py"],
        })

        recs.append({
            "category": "Schema Change",
            "id": "REC-4",
            "title": "Add person name normalization / alias system",
            "detail": (
                "The simulation detected "
                f"{len([i for i in report.integrity_issues if i['type'] == 'person_name_collision'])} "
                "person name collision(s). Names like 'Sarah' and 'Sarah Chen' create duplicate "
                "nodes. Recommend merging on email when available and adding an alias property."
            ),
            "priority": "high",
            "files": ["models/schemas.py", "core/graph_engine.py"],
        })

        # New queries
        recs.append({
            "category": "New Query",
            "id": "REC-5",
            "title": "Add query_tasks_by_assignee(person_name)",
            "detail": (
                "The most fundamental user query — 'What are my tasks?' — has no production "
                "implementation. The simulation used this query every week (52 times). "
                "Cypher: MATCH (p:Person {name: $name})-[:ASSIGNED_TO]->(t:Task) WHERE t.status <> 'done'"
            ),
            "priority": "critical",
            "files": ["core/graph_engine.py"],
        })

        recs.append({
            "category": "New Query",
            "id": "REC-6",
            "title": "Add query_tasks_due_between(start, end)",
            "detail": (
                "'What's due this week?' was attempted every week. Requires filtering tasks "
                "by due_date range. Cypher: MATCH (t:Task) WHERE t.due_date >= $start AND "
                "t.due_date <= $end AND t.status <> 'done'"
            ),
            "priority": "critical",
            "files": ["core/graph_engine.py"],
        })

        recs.append({
            "category": "New Query",
            "id": "REC-7",
            "title": "Add query_tasks_from_sender(sender_name)",
            "detail": (
                "To answer 'What do I owe <person>?', traverse Source-[:GENERATED]->Task "
                "filtered by Source.sender_name. Enables accountability tracking per requester."
            ),
            "priority": "high",
            "files": ["core/graph_engine.py"],
        })

        recs.append({
            "category": "New Query",
            "id": "REC-8",
            "title": "Add overdue task detection query",
            "detail": (
                f"The simulation found {report.tasks_overdue} overdue task(s). "
                "Add a query that returns tasks where due_date < today AND status != 'done'. "
                "This should be a first-class query, not just a side-effect of hanging tasks."
            ),
            "priority": "high",
            "files": ["core/graph_engine.py"],
        })

        return recs

    def format_report(self, report: SimulationReport) -> str:
        """Format the report as readable text."""
        lines = []
        lines.append("=" * 72)
        lines.append("  OFFICE SIMULATION REPORT — Jan–Dec 2026")
        lines.append("=" * 72)

        lines.append("\n## Statistics\n")
        lines.append(f"  Messages ingested:     {report.total_messages}")
        lines.append(f"  Tasks created:         {report.total_tasks}")
        lines.append(f"  Tasks resolved:        {report.tasks_resolved}")
        lines.append(f"  Tasks hanging:         {report.tasks_hanging}")
        lines.append(f"  Tasks overdue:         {report.tasks_overdue}")
        lines.append(f"  Persons in graph:      {report.total_persons}")
        lines.append(f"  Projects in graph:     {report.total_projects}")
        lines.append(f"  Graph edges:           {report.total_edges}")

        lines.append("\n## Query Coverage\n")
        for qt, stats in sorted(report.query_stats.items()):
            lines.append(f"  {qt:30s} {stats['successes']:>4}/{stats['attempts']:<4} ({stats['rate']})")

        lines.append("\n## System Gaps Detected\n")
        for gap in report.gaps:
            lines.append(f"  [{gap['id']}] {gap['description']}")
            lines.append(f"         Attempted {gap['times_attempted']} time(s) via '{gap['query_type']}'")

        lines.append("\n## Data Integrity Issues\n")
        for issue in report.integrity_issues:
            lines.append(f"  [{issue.get('gap_id', '?')}] {issue['type']} — {issue['count']} occurrence(s)")
            lines.append(f"         First detected: week {issue['first_detected_week']}")
            for ex in issue["examples"]:
                lines.append(f"         • {ex}")

        lines.append("\n## Recommendations\n")
        for rec in report.recommendations:
            lines.append(f"  [{rec['id']}] [{rec['priority'].upper()}] {rec['title']}")
            lines.append(f"         Category: {rec['category']}")
            lines.append(f"         Files: {', '.join(rec['files'])}")
            # Wrap detail text
            detail = rec["detail"]
            while len(detail) > 70:
                split_at = detail[:70].rfind(" ")
                if split_at == -1:
                    split_at = 70
                lines.append(f"         {detail[:split_at]}")
                detail = detail[split_at:].lstrip()
            if detail:
                lines.append(f"         {detail}")
            lines.append("")

        lines.append("=" * 72)
        return "\n".join(lines)
