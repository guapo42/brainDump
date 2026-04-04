"""Neo4j Knowledge Graph Engine — upsert and query logic."""

from neo4j import GraphDatabase

from models.schemas import ExtractionResult, SourceMetadata


# Cypher for upserting the full extraction into the graph
UPSERT_CYPHER = """\
// Create the Source node (PROV-O provenance record)
MERGE (src:Source {id: $source_id})
SET src.platform = $platform,
    src.sender_name = $sender_name,
    src.sender_email = $sender_email,
    src.received_at = $received_at

// Create Person nodes
WITH src
UNWIND $people AS person_data
MERGE (p:Person {name: person_data.name})
SET p.email = coalesce(person_data.email, p.email),
    p.role = coalesce(person_data.role, p.role)

// Create Project nodes
WITH src
UNWIND $projects AS proj_data
MERGE (proj:Project {name: proj_data.name})
SET proj.status = proj_data.status,
    proj.priority = proj_data.priority

// Create Tasks with relationships
WITH src
UNWIND $tasks AS task_data
MERGE (t:Task {description: task_data.description})
SET t.status = task_data.status,
    t.due_date = task_data.due_date,
    t.priority = task_data.priority,
    t.created_at = coalesce(t.created_at, datetime())

// Source -[:GENERATED]-> Task (PROV-O link)
MERGE (src)-[:GENERATED]->(t)

// Task -[:PART_OF]-> Project
WITH t, task_data
WHERE task_data.project IS NOT NULL
MERGE (proj:Project {name: task_data.project})
MERGE (t)-[:PART_OF]->(proj)

// Person -[:ASSIGNED_TO]-> Task
WITH t, task_data
WHERE task_data.assignee IS NOT NULL
MERGE (p:Person {name: task_data.assignee})
MERGE (p)-[:ASSIGNED_TO]->(t)

// Task -[:WAITING_ON]-> Person
WITH t, task_data
WHERE task_data.waiting_on IS NOT NULL
MERGE (p:Person {name: task_data.waiting_on})
MERGE (t)-[:WAITING_ON]->(p)
"""

# Query for finding blocked/hanging tasks
HANGING_TASKS_CYPHER = """\
MATCH (t:Task)-[:WAITING_ON]->(p:Person)
WHERE t.status <> 'done'
RETURN t.description AS task, p.name AS waiting_on,
       t.due_date AS due_date, t.priority AS priority
ORDER BY t.priority DESC, t.due_date ASC
"""

# Query for project overview
PROJECT_OVERVIEW_CYPHER = """\
MATCH (t:Task)-[:PART_OF]->(proj:Project)
OPTIONAL MATCH (t)-[:WAITING_ON]->(blocker:Person)
OPTIONAL MATCH (assignee:Person)-[:ASSIGNED_TO]->(t)
RETURN proj.name AS project, t.description AS task, t.status AS status,
       assignee.name AS assignee, blocker.name AS blocked_by, t.due_date AS due_date
ORDER BY proj.name, t.status
"""


class GraphStore:
    """Interface to Neo4j for upserting and querying the knowledge graph."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def upsert_extraction(
        self, source_meta: SourceMetadata, extraction: ExtractionResult
    ):
        """Write an extraction result into the graph, creating all nodes and relationships."""
        params = {
            "source_id": source_meta.source_id,
            "platform": source_meta.platform.value,
            "sender_name": source_meta.sender_name,
            "sender_email": source_meta.sender_email,
            "received_at": source_meta.received_at.isoformat(),
            "people": [p.model_dump() for p in extraction.people],
            "projects": [p.model_dump() for p in extraction.projects],
            "tasks": [t.model_dump() for t in extraction.tasks],
        }
        with self.driver.session() as session:
            session.run(UPSERT_CYPHER, **params)

    def query_hanging_tasks(self) -> list[dict]:
        """Find all tasks that are waiting on someone."""
        with self.driver.session() as session:
            result = session.run(HANGING_TASKS_CYPHER)
            return [dict(record) for record in result]

    def query_project_overview(self) -> list[dict]:
        """Get a full overview of tasks grouped by project."""
        with self.driver.session() as session:
            result = session.run(PROJECT_OVERVIEW_CYPHER)
            return [dict(record) for record in result]
