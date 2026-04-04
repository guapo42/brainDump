"""In-memory replacements for Neo4j and ChromaDB — no Docker required."""

from __future__ import annotations

from models.schemas import ExtractionResult, SourceMetadata


class InMemoryGraphStore:
    """Replicates Neo4j MERGE semantics using plain Python dicts.

    Data structures mirror the Cypher UPSERT_CYPHER logic:
    - MERGE on Source.id, Person.name, Project.name, Task.description
    - Relationships stored as (from_label, from_key, rel, to_label, to_key)
    """

    def __init__(self):
        self.sources: dict[str, dict] = {}
        self.persons: dict[str, dict] = {}
        self.projects: dict[str, dict] = {}
        self.tasks: dict[str, dict] = {}
        self.edges: list[tuple[str, str, str, str, str]] = []

    def upsert_extraction(
        self, source_meta: SourceMetadata, extraction: ExtractionResult
    ):
        """Mirror the UPSERT_CYPHER logic: merge nodes, create relationships."""
        sid = source_meta.source_id

        # MERGE Source
        self.sources[sid] = {
            "platform": source_meta.platform.value,
            "sender_name": source_meta.sender_name,
            "sender_email": source_meta.sender_email,
            "received_at": source_meta.received_at.isoformat(),
        }

        # MERGE People
        for p in extraction.people:
            existing = self.persons.get(p.name, {})
            self.persons[p.name] = {
                "email": p.email or existing.get("email"),
                "role": p.role or existing.get("role"),
            }

        # MERGE Projects
        for proj in extraction.projects:
            self.projects[proj.name] = {
                "status": proj.status,
                "priority": proj.priority,
            }

        # MERGE Tasks + relationships
        for task in extraction.tasks:
            desc = task.description
            existing = self.tasks.get(desc, {})
            self.tasks[desc] = {
                "status": task.status,
                "due_date": task.due_date,
                "priority": task.priority,
                "created_at": existing.get("created_at", source_meta.received_at.isoformat()),
            }

            # Source -[:GENERATED]-> Task
            self._add_edge("Source", sid, "GENERATED", "Task", desc)

            # Task -[:PART_OF]-> Project
            if task.project:
                self._add_edge("Task", desc, "PART_OF", "Project", task.project)

            # Person -[:ASSIGNED_TO]-> Task
            if task.assignee:
                self._add_edge("Person", task.assignee, "ASSIGNED_TO", "Task", desc)

            # Task -[:WAITING_ON]-> Person
            if task.waiting_on:
                self._add_edge("Task", desc, "WAITING_ON", "Person", task.waiting_on)

    def mark_task_done(self, description: str):
        """Mark a task as done (used by simulation to resolve tasks)."""
        if description in self.tasks:
            self.tasks[description]["status"] = "done"
            # Remove WAITING_ON edges for this task
            self.edges = [
                e for e in self.edges
                if not (e[0] == "Task" and e[1] == description and e[2] == "WAITING_ON")
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
                        "task": from_key,
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
                task_desc = from_key
                task = self.tasks.get(task_desc, {})

                assignee = None
                blocked_by = None
                for e2 in self.edges:
                    if e2[2] == "ASSIGNED_TO" and e2[3] == "Task" and e2[4] == task_desc:
                        assignee = e2[1]
                    if e2[0] == "Task" and e2[1] == task_desc and e2[2] == "WAITING_ON":
                        blocked_by = e2[4]

                results.append({
                    "project": to_key,
                    "task": task_desc,
                    "status": task.get("status"),
                    "assignee": assignee,
                    "blocked_by": blocked_by,
                    "due_date": task.get("due_date"),
                })
        results.sort(key=lambda r: (r["project"], r["status"] or ""))
        return results

    # --- GAP QUERIES: these are queries the UserAgent will TRY but don't exist
    # on the real GraphStore. The simulation implements them here to show what's
    # needed, and the gap report flags them as missing from the production system.

    def query_tasks_by_assignee(self, person_name: str) -> list[dict]:
        """GAP: Find all tasks assigned to a specific person."""
        results = []
        for edge in self.edges:
            if edge[0] == "Person" and edge[1] == person_name and edge[2] == "ASSIGNED_TO":
                task_desc = edge[4]
                task = self.tasks.get(task_desc, {})
                results.append({"task": task_desc, **task})
        return results

    def query_tasks_due_between(self, start: str, end: str) -> list[dict]:
        """GAP: Find tasks due within a date range (ISO strings)."""
        results = []
        for desc, task in self.tasks.items():
            dd = task.get("due_date")
            if dd and start <= dd <= end:
                results.append({"task": desc, **task})
        return results

    def query_tasks_from_sender(self, sender_name: str) -> list[dict]:
        """GAP: Find tasks generated from a specific sender's messages."""
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
                task_desc = edge[4]
                if task_desc not in seen:
                    seen.add(task_desc)
                    task = self.tasks.get(task_desc, {})
                    results.append({"task": task_desc, **task})
        return results

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
