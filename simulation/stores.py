"""In-memory replacements for Neo4j and ChromaDB — no Docker required."""

from __future__ import annotations

from models.schemas import ExtractionResult, SourceMetadata


class InMemoryGraphStore:
    """Replicates Neo4j MERGE semantics using plain Python dicts.

    Updated to match production GraphStore after REC-1 through REC-8:
    - REC-1: REQUESTED_BY edges from source sender to generated tasks
    - REC-2: updated_at timestamp on tasks
    - REC-3: Composite task key (description + project)
    - REC-4: Person MERGE on email when available, alias tracking
    - REC-5/6/7/8: New query methods now in production
    """

    def __init__(self):
        self.sources: dict[str, dict] = {}
        self.persons: dict[str, dict] = {}          # key = canonical name
        self._email_to_name: dict[str, str] = {}    # REC-4: email -> canonical name
        self.projects: dict[str, dict] = {}
        self.tasks: dict[str, dict] = {}             # key = "desc||project" or "desc||"
        self.edges: list[tuple[str, str, str, str, str]] = []

    @staticmethod
    def _task_key(description: str, project: str | None) -> str:
        """REC-3: Composite key for task identity."""
        return f"{description}||{project or ''}"

    def _resolve_person_name(self, name: str, email: str | None = None) -> str:
        """REC-4: Resolve a person to their canonical name, merging on email."""
        if email and email in self._email_to_name:
            return self._email_to_name[email]
        if email:
            self._email_to_name[email] = name
        return name

    def upsert_extraction(
        self, source_meta: SourceMetadata, extraction: ExtractionResult
    ):
        """Mirror the UPSERT_CYPHER logic: merge nodes, create relationships."""
        sid = source_meta.source_id
        received_at = source_meta.received_at.isoformat()

        # MERGE Source
        self.sources[sid] = {
            "platform": source_meta.platform.value,
            "sender_name": source_meta.sender_name,
            "sender_email": source_meta.sender_email,
            "received_at": received_at,
        }

        # MERGE People (REC-4: merge on email when available)
        for p in extraction.people:
            canonical = self._resolve_person_name(p.name, p.email)
            existing = self.persons.get(canonical, {})
            aliases = list(set(existing.get("aliases", []) + (p.aliases or [])))
            # Track short-name as alias if different from canonical
            if p.name != canonical and p.name not in aliases:
                aliases.append(p.name)
            self.persons[canonical] = {
                "email": p.email or existing.get("email"),
                "role": p.role or existing.get("role"),
                "aliases": aliases,
            }

        # MERGE Projects
        for proj in extraction.projects:
            self.projects[proj.name] = {
                "status": proj.status,
                "priority": proj.priority,
            }

        # MERGE Tasks + relationships
        for task in extraction.tasks:
            # REC-3: Composite key
            tk = self._task_key(task.description, task.project)
            existing = self.tasks.get(tk, {})
            self.tasks[tk] = {
                "description": task.description,
                "project": task.project,
                "status": task.status,
                "due_date": task.due_date,
                "priority": task.priority,
                "created_at": existing.get("created_at", received_at),
                "updated_at": received_at,  # REC-2
            }

            # Source -[:GENERATED]-> Task
            self._add_edge("Source", sid, "GENERATED", "Task", tk)

            # REC-1: Source sender -[:REQUESTED_BY]-> Person
            self._add_edge("Task", tk, "REQUESTED_BY", "Person", source_meta.sender_name)

            # Task -[:PART_OF]-> Project
            if task.project:
                self._add_edge("Task", tk, "PART_OF", "Project", task.project)

            # Person -[:ASSIGNED_TO]-> Task
            if task.assignee:
                self._add_edge("Person", task.assignee, "ASSIGNED_TO", "Task", tk)

            # Task -[:WAITING_ON]-> Person
            if task.waiting_on:
                self._add_edge("Task", tk, "WAITING_ON", "Person", task.waiting_on)

    def mark_task_done(self, description: str):
        """Mark a task as done by description (checks all project variants)."""
        for tk, task in self.tasks.items():
            if task["description"] == description:
                task["status"] = "done"
                # Remove WAITING_ON edges for this task
                self.edges = [
                    e for e in self.edges
                    if not (e[0] == "Task" and e[1] == tk and e[2] == "WAITING_ON")
                ]

    def query_hanging_tasks(self) -> list[dict]:
        """Find tasks waiting on someone (status != done)."""
        results = []
        for edge in self.edges:
            from_label, from_key, rel, to_label, to_key = edge
            if from_label == "Task" and rel == "WAITING_ON" and to_label == "Person":
                task = self.tasks.get(from_key, {})
                if task.get("status") != "done":
                    results.append({
                        "task": task.get("description", from_key),
                        "waiting_on": to_key,
                        "due_date": task.get("due_date"),
                        "priority": task.get("priority"),
                    })
        return results

    def query_project_overview(self) -> list[dict]:
        """Get tasks grouped by project with assignee and blocker info."""
        results = []
        for edge in self.edges:
            from_label, from_key, rel, to_label, to_key = edge
            if from_label == "Task" and rel == "PART_OF" and to_label == "Project":
                task = self.tasks.get(from_key, {})

                assignee = None
                blocked_by = None
                for e2 in self.edges:
                    if e2[2] == "ASSIGNED_TO" and e2[3] == "Task" and e2[4] == from_key:
                        assignee = e2[1]
                    if e2[0] == "Task" and e2[1] == from_key and e2[2] == "WAITING_ON":
                        blocked_by = e2[4]

                results.append({
                    "project": to_key,
                    "task": task.get("description", from_key),
                    "status": task.get("status"),
                    "assignee": assignee,
                    "blocked_by": blocked_by,
                    "due_date": task.get("due_date"),
                })
        results.sort(key=lambda r: (r["project"], r["status"] or ""))
        return results

    # --- NEW QUERIES (formerly gap queries, now in production) ---

    def query_tasks_by_assignee(self, person_name: str) -> list[dict]:
        """REC-5: Find all pending tasks assigned to a specific person."""
        results = []
        for edge in self.edges:
            if edge[0] == "Person" and edge[1] == person_name and edge[2] == "ASSIGNED_TO":
                task = self.tasks.get(edge[4], {})
                if task.get("status") != "done":
                    # Enrich with project and blocker
                    project = task.get("project")
                    blocked_by = None
                    for e2 in self.edges:
                        if e2[0] == "Task" and e2[1] == edge[4] and e2[2] == "WAITING_ON":
                            blocked_by = e2[4]
                    results.append({
                        "task": task.get("description", edge[4]),
                        "status": task.get("status"),
                        "due_date": task.get("due_date"),
                        "priority": task.get("priority"),
                        "project": project,
                        "blocked_by": blocked_by,
                    })
        return results

    def query_tasks_due_between(self, start: str, end: str) -> list[dict]:
        """REC-6: Find tasks due within a date range (ISO strings)."""
        results = []
        for tk, task in self.tasks.items():
            dd = task.get("due_date")
            if dd and start <= dd <= end and task.get("status") != "done":
                # Find assignee
                assignee = None
                for e in self.edges:
                    if e[2] == "ASSIGNED_TO" and e[3] == "Task" and e[4] == tk:
                        assignee = e[1]
                results.append({
                    "task": task.get("description", tk),
                    "status": task.get("status"),
                    "due_date": dd,
                    "priority": task.get("priority"),
                    "assignee": assignee,
                    "project": task.get("project"),
                })
        results.sort(key=lambda r: r["due_date"])
        return results

    def query_tasks_from_sender(self, sender_name: str) -> list[dict]:
        """REC-7: Find tasks generated from a specific sender's messages."""
        # Find source IDs from this sender
        source_ids = [
            sid for sid, s in self.sources.items()
            if s["sender_name"] == sender_name
        ]
        # Find tasks generated by those sources
        results = []
        seen = set()
        for edge in self.edges:
            if (edge[0] == "Source" and edge[1] in source_ids
                    and edge[2] == "GENERATED" and edge[3] == "Task"):
                tk = edge[4]
                if tk not in seen:
                    seen.add(tk)
                    task = self.tasks.get(tk, {})
                    if task.get("status") != "done":
                        # Find assignee
                        assignee = None
                        for e in self.edges:
                            if e[2] == "ASSIGNED_TO" and e[3] == "Task" and e[4] == tk:
                                assignee = e[1]
                        results.append({
                            "task": task.get("description", tk),
                            "status": task.get("status"),
                            "due_date": task.get("due_date"),
                            "priority": task.get("priority"),
                            "assignee": assignee,
                            "project": task.get("project"),
                        })
        return results

    def query_overdue_tasks(self, today: str) -> list[dict]:
        """REC-8: Find tasks past their due date that aren't done."""
        results = []
        for tk, task in self.tasks.items():
            dd = task.get("due_date")
            if dd and dd < today and task.get("status") != "done":
                # Find assignee and blocker
                assignee = None
                blocked_by = None
                project = task.get("project")
                for e in self.edges:
                    if e[2] == "ASSIGNED_TO" and e[3] == "Task" and e[4] == tk:
                        assignee = e[1]
                    if e[0] == "Task" and e[1] == tk and e[2] == "WAITING_ON":
                        blocked_by = e[4]
                results.append({
                    "task": task.get("description", tk),
                    "status": task.get("status"),
                    "due_date": dd,
                    "priority": task.get("priority"),
                    "assignee": assignee,
                    "project": project,
                    "blocked_by": blocked_by,
                })
        results.sort(key=lambda r: r["due_date"])
        return results

    def _compute_frustration(self, tk: str, task: dict, today: str) -> dict:
        """Compute frustration score for a single task."""
        desc = task.get("description", tk)
        priority = task.get("priority", "medium")
        due_date = task.get("due_date")
        priority_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(priority, 2)

        # Count mentions (Source -[:GENERATED]-> Task)
        source_ids = [e[1] for e in self.edges
                      if e[0] == "Source" and e[2] == "GENERATED"
                      and e[3] == "Task" and e[4] == tk]
        mention_count = len(set(source_ids))

        # Get requesters
        requesters = list({self.sources[sid]["sender_name"]
                          for sid in source_ids if sid in self.sources})

        # Days overdue
        days_overdue = 0
        if due_date and due_date < today:
            from datetime import date as _date
            try:
                dp = due_date.split("-")
                dd = _date(int(dp[0]), int(dp[1]), int(dp[2]))
                tp = today.split("-")
                td = _date(int(tp[0]), int(tp[1]), int(tp[2]))
                days_overdue = (td - dd).days
            except (ValueError, IndexError):
                pass

        # Last mention timestamp
        last_mention = None
        for sid in source_ids:
            if sid in self.sources:
                rm = self.sources[sid].get("received_at")
                if rm and (last_mention is None or rm > last_mention):
                    last_mention = rm

        # Find assignee
        assignee = None
        for e in self.edges:
            if e[2] == "ASSIGNED_TO" and e[3] == "Task" and e[4] == tk:
                assignee = e[1]

        frustration = (mention_count * 1.5 + days_overdue) * priority_weight

        return {
            "task": desc,
            "status": task.get("status"),
            "due_date": due_date,
            "priority": priority,
            "assignee": assignee,
            "project": task.get("project"),
            "requesters": requesters,
            "mention_count": mention_count,
            "days_overdue": days_overdue,
            "last_mention": last_mention,
            "frustration_score": frustration,
            "estimated_minutes": task.get("estimated_minutes"),
        }

    def query_frustration_scores(self, today: str | None = None) -> list[dict]:
        """Stakeholder frustration: how annoyed are your requesters?"""
        if today is None:
            today = "2026-12-31"
        results = []
        for tk, task in self.tasks.items():
            if task.get("status") == "done":
                continue
            result = self._compute_frustration(tk, task, today)
            if result["frustration_score"] > 0:
                results.append(result)
        results.sort(key=lambda r: r["frustration_score"], reverse=True)
        return results

    def query_forgetting(self, person_name: str, today: str | None = None) -> list[dict]:
        """Anti-object-permanence: tasks assigned to you, ranked by frustration."""
        if today is None:
            today = "2026-12-31"
        results = []
        for edge in self.edges:
            if edge[0] == "Person" and edge[1] == person_name and edge[2] == "ASSIGNED_TO":
                tk = edge[4]
                task = self.tasks.get(tk, {})
                if task.get("status") == "done":
                    continue
                results.append(self._compute_frustration(tk, task, today))
        results.sort(key=lambda r: r["frustration_score"], reverse=True)
        return results

    def query_nudge(self, person_name: str, today: str | None = None) -> dict | None:
        """Timebox nudge: return the single most urgent task to start right now."""
        results = self.query_forgetting(person_name, today)
        return results[0] if results else None

    def close(self):
        pass

    def _add_edge(self, from_label: str, from_key: str, rel: str, to_label: str, to_key: str):
        edge = (from_label, from_key, rel, to_label, to_key)
        if edge not in self.edges:
            self.edges.append(edge)


class InMemoryVectorStore:
    """Replicates ChromaDB using simple keyword matching."""

    def __init__(self):
        self.documents: dict[str, dict] = {}  # doc_id -> {text, metadata}

    def upsert_document(self, doc_id: str, text: str, metadata: dict):
        self.documents[doc_id] = {"text": text, "metadata": metadata}

    def search_context(self, query: str, n_results: int = 5) -> dict:
        """Keyword-based search (no embeddings needed for simulation)."""
        query_lower = query.lower()
        query_terms = query_lower.split()

        scored = []
        for doc_id, doc in self.documents.items():
            text_lower = doc["text"].lower()
            score = sum(1 for term in query_terms if term in text_lower)
            if score > 0:
                scored.append((score, doc_id, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:n_results]

        return {
            "ids": [[item[1] for item in top]],
            "documents": [[item[2]["text"] for item in top]],
            "metadatas": [[item[2]["metadata"] for item in top]],
        }

    def get_by_ids(self, ids: list[str]) -> dict:
        docs = []
        metas = []
        found_ids = []
        for doc_id in ids:
            if doc_id in self.documents:
                found_ids.append(doc_id)
                docs.append(self.documents[doc_id]["text"])
                metas.append(self.documents[doc_id]["metadata"])
        return {"ids": found_ids, "documents": docs, "metadatas": metas}

    def close(self):
        pass
