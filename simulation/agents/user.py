"""UserAgent — queries the system each week, logs results, detects gaps."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from simulation.clock import SimWeek
from simulation.stores import InMemoryGraphStore, InMemoryVectorStore


@dataclass
class QueryAttempt:
    """Record of a single query the UserAgent tried."""
    week: int
    query_type: str
    query_params: dict
    result_count: int
    success: bool
    gap_id: str | None = None
    gap_description: str | None = None


class UserAgent:
    """Simulates a user managing their work through the brain-dump system.

    Exercises three tiers:
    A) Existing queries that should work
    B) Natural queries that expose system gaps
    C) Data integrity checks
    """

    def __init__(self, graph: InMemoryGraphStore, vector: InMemoryVectorStore):
        self.graph = graph
        self.vector = vector
        self.query_log: list[QueryAttempt] = []
        self.integrity_issues: list[dict] = []

    def run_weekly_queries(self, week: SimWeek):
        """Run all query tiers for the given week."""
        self._tier_a_existing_queries(week)
        self._tier_b_gap_queries(week)
        self._tier_c_integrity_checks(week)

    # === TIER A: Existing queries (should work) ===

    def _tier_a_existing_queries(self, week: SimWeek):
        # Hanging tasks
        results = self.graph.query_hanging_tasks()
        self.query_log.append(QueryAttempt(
            week=week.week_number,
            query_type="hanging_tasks",
            query_params={},
            result_count=len(results),
            success=True,
        ))

        # Project overview
        results = self.graph.query_project_overview()
        self.query_log.append(QueryAttempt(
            week=week.week_number,
            query_type="project_overview",
            query_params={},
            result_count=len(results),
            success=True,
        ))

        # Semantic search — varies by quarter
        search_terms = {
            1: "Phoenix architecture design",
            2: "milestone deadline blocked",
            3: "UAT deployment testing",
            4: "retrospective accomplishments",
        }
        query = search_terms[week.quarter]
        results = self.vector.search_context(query, n_results=3)
        doc_count = len(results.get("documents", [[]])[0])
        self.query_log.append(QueryAttempt(
            week=week.week_number,
            query_type="search_context",
            query_params={"query": query},
            result_count=doc_count,
            success=doc_count > 0 if week.week_number > 4 else True,
        ))

    # === TIER B: Gap queries (expose missing capabilities) ===

    def _tier_b_gap_queries(self, week: SimWeek):
        w = week.week_number

        # GAP-1: "What are my tasks?" — no assignee filter on real GraphStore
        my_tasks = self.graph.query_tasks_by_assignee("You")
        pending = [t for t in my_tasks if t.get("status") != "done"]
        self.query_log.append(QueryAttempt(
            week=w,
            query_type="tasks_by_assignee",
            query_params={"person": "You"},
            result_count=len(pending),
            success=len(pending) >= 0,  # always "works" on InMemory
            gap_id="GAP-1",
            gap_description="No query_tasks_by_assignee() on production GraphStore",
        ))

        # GAP-2: "What's due this week?" — no date range filter
        week_start = week.monday.isoformat()
        week_end = (week.monday + timedelta(days=6)).isoformat()
        due_this_week = self.graph.query_tasks_due_between(week_start, week_end)
        self.query_log.append(QueryAttempt(
            week=w,
            query_type="tasks_due_between",
            query_params={"start": week_start, "end": week_end},
            result_count=len(due_this_week),
            success=True,
            gap_id="GAP-2",
            gap_description="No query_tasks_due_between() on production GraphStore",
        ))

        # GAP-3: "What do I owe Linda?" — no requester tracking
        if w % 4 == 0:  # Monthly check
            linda_tasks = self.graph.query_tasks_from_sender("Linda Torres")
            pending_for_linda = [t for t in linda_tasks if t.get("status") != "done"]
            self.query_log.append(QueryAttempt(
                week=w,
                query_type="tasks_from_sender",
                query_params={"sender": "Linda Torres"},
                result_count=len(pending_for_linda),
                success=True,
                gap_id="GAP-3",
                gap_description="No REQUESTED_BY relationship or query_tasks_from_sender() on production GraphStore",
            ))

        # GAP-4: "What do I owe Robert?" — same gap, different person
        if w % 2 == 0:
            robert_tasks = self.graph.query_tasks_from_sender("Robert Kim")
            pending_for_robert = [t for t in robert_tasks if t.get("status") != "done"]
            self.query_log.append(QueryAttempt(
                week=w,
                query_type="tasks_from_sender",
                query_params={"sender": "Robert Kim"},
                result_count=len(pending_for_robert),
                success=True,
                gap_id="GAP-3",
                gap_description="No REQUESTED_BY relationship or query_tasks_from_sender() on production GraphStore",
            ))

        # GAP-5: "Summarize my week" — no weekly aggregation query
        week_msgs = [
            doc_id for doc_id, doc in self.vector.documents.items()
            if doc["metadata"].get("received_at", "").startswith(week_start[:10])
            or any(
                doc["metadata"].get("received_at", "").startswith(
                    (week.monday + timedelta(days=d)).isoformat()[:10]
                )
                for d in range(7)
            )
        ]
        self.query_log.append(QueryAttempt(
            week=w,
            query_type="weekly_summary",
            query_params={"week": w},
            result_count=len(week_msgs),
            success=True,
            gap_id="GAP-5",
            gap_description="No weekly aggregation/summary query — requires manual filtering by date",
        ))

    # === TIER C: Data integrity checks ===

    def _tier_c_integrity_checks(self, week: SimWeek):
        w = week.week_number

        # Check for person name collisions (e.g., "Sarah" vs "Sarah Chen")
        person_names = list(self.graph.persons.keys())
        for name in person_names:
            # Find names that are substrings of other names
            for other in person_names:
                if name != other and name in other and len(name) > 2:
                    issue = {
                        "week": w,
                        "type": "person_name_collision",
                        "detail": f'"{name}" and "{other}" may be the same person',
                        "gap_id": "GAP-6",
                    }
                    if issue not in self.integrity_issues:
                        self.integrity_issues.append(issue)

        # Check for task description collisions across projects
        task_projects: dict[str, set[str]] = {}
        for edge in self.graph.edges:
            if edge[0] == "Task" and edge[2] == "PART_OF":
                task_projects.setdefault(edge[1], set()).add(edge[4])
        # Tasks that appear in multiple projects may be false merges
        for desc, projects in task_projects.items():
            if len(projects) > 1:
                issue = {
                    "week": w,
                    "type": "task_description_collision",
                    "detail": f'Task "{desc}" appears in projects: {projects}',
                    "gap_id": "GAP-7",
                }
                if issue not in self.integrity_issues:
                    self.integrity_issues.append(issue)

        # Check for overdue tasks
        week_date = week.monday.isoformat()
        for desc, task in self.graph.tasks.items():
            dd = task.get("due_date")
            if dd and dd < week_date and task.get("status") != "done":
                issue = {
                    "week": w,
                    "type": "overdue_task",
                    "detail": f'Task "{desc}" was due {dd} but status is {task.get("status")}',
                    "gap_id": "GAP-8",
                }
                # Only record first detection
                existing = [i for i in self.integrity_issues
                            if i["type"] == "overdue_task" and i["detail"] == issue["detail"]]
                if not existing:
                    self.integrity_issues.append(issue)

    # === Summary stats ===

    def get_stats(self) -> dict:
        total = len(self.query_log)
        successful = sum(1 for q in self.query_log if q.success)
        gap_queries = [q for q in self.query_log if q.gap_id]
        unique_gaps = {q.gap_id for q in gap_queries}

        return {
            "total_queries": total,
            "successful_queries": successful,
            "success_rate": successful / total if total else 0,
            "gap_query_count": len(gap_queries),
            "unique_gaps_detected": len(unique_gaps),
            "integrity_issues": len(self.integrity_issues),
            "unique_integrity_types": len({i["type"] for i in self.integrity_issues}),
        }
