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

    Exercises two tiers:
    A) Production queries — all REC-1 through REC-8 are now implemented
    B) Data integrity checks — structural issues in the graph
    """

    def __init__(self, graph: InMemoryGraphStore, vector: InMemoryVectorStore):
        self.graph = graph
        self.vector = vector
        self.query_log: list[QueryAttempt] = []
        self.integrity_issues: list[dict] = []

    def run_weekly_queries(self, week: SimWeek):
        """Run all query tiers for the given week."""
        self._tier_a_production_queries(week)
        self._tier_b_integrity_checks(week)

    # === TIER A: Production queries (all implemented) ===

    def _tier_a_production_queries(self, week: SimWeek):
        w = week.week_number

        # Hanging tasks
        results = self.graph.query_hanging_tasks()
        self.query_log.append(QueryAttempt(
            week=w, query_type="hanging_tasks", query_params={},
            result_count=len(results), success=True,
        ))

        # Project overview
        results = self.graph.query_project_overview()
        self.query_log.append(QueryAttempt(
            week=w, query_type="project_overview", query_params={},
            result_count=len(results), success=True,
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
            week=w, query_type="search_context",
            query_params={"query": query},
            result_count=doc_count,
            success=doc_count > 0 if w > 4 else True,
        ))

        # REC-5: "What are my tasks?"
        my_tasks = self.graph.query_tasks_by_assignee("You")
        self.query_log.append(QueryAttempt(
            week=w, query_type="tasks_by_assignee",
            query_params={"person": "You"},
            result_count=len(my_tasks), success=True,
        ))

        # REC-6: "What's due this week?"
        week_start = week.monday.isoformat()
        week_end = (week.monday + timedelta(days=6)).isoformat()
        due_this_week = self.graph.query_tasks_due_between(week_start, week_end)
        self.query_log.append(QueryAttempt(
            week=w, query_type="tasks_due_between",
            query_params={"start": week_start, "end": week_end},
            result_count=len(due_this_week), success=True,
        ))

        # REC-7: "What do I owe Linda?" (monthly)
        if w % 4 == 0:
            linda_tasks = self.graph.query_tasks_from_sender("Linda Torres")
            self.query_log.append(QueryAttempt(
                week=w, query_type="tasks_from_sender",
                query_params={"sender": "Linda Torres"},
                result_count=len(linda_tasks), success=True,
            ))

        # REC-7: "What do I owe Robert?" (biweekly)
        if w % 2 == 0:
            robert_tasks = self.graph.query_tasks_from_sender("Robert Kim")
            self.query_log.append(QueryAttempt(
                week=w, query_type="tasks_from_sender",
                query_params={"sender": "Robert Kim"},
                result_count=len(robert_tasks), success=True,
            ))

        # REC-8: Overdue tasks
        today = week.monday.isoformat()
        overdue = self.graph.query_overdue_tasks(today)
        self.query_log.append(QueryAttempt(
            week=w, query_type="overdue_tasks",
            query_params={"today": today},
            result_count=len(overdue), success=True,
        ))

        # Weekly summary (vector store date filtering)
        week_msgs = [
            doc_id for doc_id, doc in self.vector.documents.items()
            if any(
                doc["metadata"].get("received_at", "").startswith(
                    (week.monday + timedelta(days=d)).isoformat()[:10]
                )
                for d in range(7)
            )
        ]
        self.query_log.append(QueryAttempt(
            week=w, query_type="weekly_summary",
            query_params={"week": w},
            result_count=len(week_msgs), success=True,
        ))

    # === TIER B: Data integrity checks ===

    def _tier_b_integrity_checks(self, week: SimWeek):
        w = week.week_number

        # REC-4: Check for person name collisions
        person_names = list(self.graph.persons.keys())
        for name in person_names:
            for other in person_names:
                if name != other and name in other and len(name) > 2:
                    issue = {
                        "week": w,
                        "type": "person_name_collision",
                        "detail": f'"{name}" and "{other}" may be the same person',
                    }
                    if issue not in self.integrity_issues:
                        self.integrity_issues.append(issue)

        # REC-3: Check for task description collisions across projects
        # With composite keys this should no longer happen, but verify
        desc_projects: dict[str, set[str]] = {}
        for tk, task in self.graph.tasks.items():
            desc = task.get("description", "")
            proj = task.get("project") or "(none)"
            desc_projects.setdefault(desc, set()).add(proj)

        for desc, projects in desc_projects.items():
            if len(projects) > 1 and "(none)" not in projects:
                issue = {
                    "week": w,
                    "type": "task_description_collision",
                    "detail": f'Task "{desc}" appears in projects: {projects}',
                }
                if issue not in self.integrity_issues:
                    self.integrity_issues.append(issue)

        # Check for overdue tasks
        week_date = week.monday.isoformat()
        for tk, task in self.graph.tasks.items():
            dd = task.get("due_date")
            if dd and dd < week_date and task.get("status") != "done":
                detail = f'Task "{task.get("description", tk)}" was due {dd} but status is {task.get("status")}'
                existing = [i for i in self.integrity_issues
                            if i["type"] == "overdue_task" and i["detail"] == detail]
                if not existing:
                    self.integrity_issues.append({
                        "week": w,
                        "type": "overdue_task",
                        "detail": detail,
                    })

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
