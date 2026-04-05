"""Neo4j Knowledge Graph Engine — upsert and query logic."""

from neo4j import GraphDatabase

from models.schemas import ExtractionResult, SourceMetadata


# REC-3: Composite MERGE key (description + project) prevents false merges.
# REC-1: REQUESTED_BY relationship links source sender to generated tasks.
# REC-2: updated_at timestamp set on every upsert.
# REC-4: Person MERGE on email when available, alias tracking.
UPSERT_CYPHER = """\
// Create the Source node (PROV-O provenance record)
MERGE (src:Source {id: $source_id})
SET src.platform = $platform,
    src.sender_name = $sender_name,
    src.sender_email = $sender_email,
    src.received_at = $received_at

// Create Person nodes — MERGE on email when available (REC-4)
WITH src
UNWIND $people AS person_data
CALL {
    WITH person_data
    WITH person_data
    WHERE person_data.email IS NOT NULL
    MERGE (p:Person {email: person_data.email})
    SET p.name = person_data.name,
        p.role = coalesce(person_data.role, p.role),
        p.aliases = coalesce(person_data.aliases, p.aliases)
    RETURN p
  UNION
    WITH person_data
    WITH person_data
    WHERE person_data.email IS NULL
    MERGE (p:Person {name: person_data.name})
    SET p.role = coalesce(person_data.role, p.role),
        p.aliases = coalesce(person_data.aliases, p.aliases)
    RETURN p
}

// Create Project nodes
WITH src
UNWIND $projects AS proj_data
MERGE (proj:Project {name: proj_data.name})
SET proj.status = proj_data.status,
    proj.priority = proj_data.priority

// Create Tasks — MERGE on composite key description+project (REC-3)
WITH src
UNWIND $tasks AS task_data
CALL {
    WITH task_data
    WITH task_data
    WHERE task_data.project IS NOT NULL
    MERGE (t:Task {description: task_data.description, project: task_data.project})
    RETURN t
  UNION
    WITH task_data
    WITH task_data
    WHERE task_data.project IS NULL
    MERGE (t:Task {description: task_data.description})
    RETURN t
}
SET t.status = task_data.status,
    t.due_date = task_data.due_date,
    t.priority = task_data.priority,
    t.created_at = coalesce(t.created_at, datetime()),
    t.updated_at = datetime()

// Source -[:GENERATED]-> Task (PROV-O link)
MERGE (src)-[:GENERATED]->(t)

// Source sender -[:REQUESTED_BY]-> Person (REC-1)
WITH src, t
MATCH (requester:Person)
WHERE requester.name = src.sender_name OR requester.email = src.sender_email
MERGE (t)-[:REQUESTED_BY]->(requester)

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

# REC-5: Tasks assigned to a specific person
TASKS_BY_ASSIGNEE_CYPHER = """\
MATCH (p:Person)-[:ASSIGNED_TO]->(t:Task)
WHERE p.name = $person_name AND t.status <> 'done'
OPTIONAL MATCH (t)-[:PART_OF]->(proj:Project)
OPTIONAL MATCH (t)-[:WAITING_ON]->(blocker:Person)
RETURN t.description AS task, t.status AS status, t.due_date AS due_date,
       t.priority AS priority, proj.name AS project, blocker.name AS blocked_by
ORDER BY t.priority DESC, t.due_date ASC
"""

# REC-6: Tasks due within a date range
TASKS_DUE_BETWEEN_CYPHER = """\
MATCH (t:Task)
WHERE t.due_date >= $start_date AND t.due_date <= $end_date AND t.status <> 'done'
OPTIONAL MATCH (assignee:Person)-[:ASSIGNED_TO]->(t)
OPTIONAL MATCH (t)-[:PART_OF]->(proj:Project)
RETURN t.description AS task, t.status AS status, t.due_date AS due_date,
       t.priority AS priority, assignee.name AS assignee, proj.name AS project
ORDER BY t.due_date ASC
"""

# REC-7: Tasks originating from a specific sender's messages
TASKS_FROM_SENDER_CYPHER = """\
MATCH (src:Source)-[:GENERATED]->(t:Task)
WHERE src.sender_name = $sender_name AND t.status <> 'done'
OPTIONAL MATCH (assignee:Person)-[:ASSIGNED_TO]->(t)
RETURN t.description AS task, t.status AS status, t.due_date AS due_date,
       t.priority AS priority, assignee.name AS assignee, src.received_at AS requested_at
ORDER BY src.received_at DESC
"""

# REC-8: Overdue tasks (due date in the past, not done)
OVERDUE_TASKS_CYPHER = """\
MATCH (t:Task)
WHERE t.due_date < $today AND t.status <> 'done'
OPTIONAL MATCH (assignee:Person)-[:ASSIGNED_TO]->(t)
OPTIONAL MATCH (t)-[:PART_OF]->(proj:Project)
OPTIONAL MATCH (t)-[:WAITING_ON]->(blocker:Person)
RETURN t.description AS task, t.status AS status, t.due_date AS due_date,
       t.priority AS priority, assignee.name AS assignee, proj.name AS project,
       blocker.name AS blocked_by
ORDER BY t.due_date ASC
"""


# Frustration score: how annoyed is the requester?
# Combines: days overdue × follow-up count × sender rank
FRUSTRATION_SCORE_CYPHER = """\
MATCH (src:Source)-[:GENERATED]->(t:Task)
WHERE t.status <> 'done'
OPTIONAL MATCH (assignee:Person)-[:ASSIGNED_TO]->(t)
WITH t, assignee,
     count(DISTINCT src) AS mention_count,
     max(src.received_at) AS last_mention,
     collect(DISTINCT src.sender_name)[0] AS requester
WITH t, assignee, mention_count, last_mention, requester,
     CASE
       WHEN t.due_date IS NOT NULL AND t.due_date < date().toString()
       THEN duration.between(date(t.due_date), date()).days
       ELSE 0
     END AS days_overdue
RETURN t.description AS task, t.status AS status, t.due_date AS due_date,
       t.priority AS priority, assignee.name AS assignee, requester,
       mention_count, days_overdue, last_mention,
       (mention_count * 1.5 + days_overdue) *
         CASE t.priority
           WHEN 'critical' THEN 4 WHEN 'high' THEN 3
           WHEN 'medium' THEN 2 ELSE 1
         END AS frustration_score
ORDER BY frustration_score DESC
"""

# "What are you forgetting?" — anti-object-permanence query
FORGETTING_CYPHER = """\
MATCH (p:Person)-[:ASSIGNED_TO]->(t:Task)
WHERE p.name = $person_name AND t.status <> 'done'
OPTIONAL MATCH (src:Source)-[:GENERATED]->(t)
WITH t, count(DISTINCT src) AS mention_count,
     max(src.received_at) AS last_mention,
     collect(DISTINCT src.sender_name) AS requesters
OPTIONAL MATCH (t)-[:PART_OF]->(proj:Project)
WITH t, mention_count, last_mention, requesters, proj,
     CASE
       WHEN t.due_date IS NOT NULL AND t.due_date < date().toString()
       THEN duration.between(date(t.due_date), date()).days
       ELSE 0
     END AS days_overdue
RETURN t.description AS task, t.due_date AS due_date,
       t.priority AS priority, proj.name AS project,
       requesters, mention_count, days_overdue, last_mention,
       (mention_count * 1.5 + days_overdue) *
         CASE t.priority
           WHEN 'critical' THEN 4 WHEN 'high' THEN 3
           WHEN 'medium' THEN 2 ELSE 1
         END AS frustration_score,
       t.estimated_minutes AS estimated_minutes
ORDER BY frustration_score DESC
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

    def query_tasks_by_assignee(self, person_name: str) -> list[dict]:
        """Find all pending tasks assigned to a specific person (REC-5)."""
        with self.driver.session() as session:
            result = session.run(TASKS_BY_ASSIGNEE_CYPHER, person_name=person_name)
            return [dict(record) for record in result]

    def query_tasks_due_between(self, start_date: str, end_date: str) -> list[dict]:
        """Find tasks due within a date range (REC-6)."""
        with self.driver.session() as session:
            result = session.run(TASKS_DUE_BETWEEN_CYPHER, start_date=start_date, end_date=end_date)
            return [dict(record) for record in result]

    def query_tasks_from_sender(self, sender_name: str) -> list[dict]:
        """Find tasks generated from a specific sender's messages (REC-7)."""
        with self.driver.session() as session:
            result = session.run(TASKS_FROM_SENDER_CYPHER, sender_name=sender_name)
            return [dict(record) for record in result]

    def query_overdue_tasks(self, today: str) -> list[dict]:
        """Find tasks past their due date that aren't done (REC-8)."""
        with self.driver.session() as session:
            result = session.run(OVERDUE_TASKS_CYPHER, today=today)
            return [dict(record) for record in result]

    def query_frustration_scores(self) -> list[dict]:
        """Stakeholder frustration: how annoyed are your requesters?"""
        with self.driver.session() as session:
            result = session.run(FRUSTRATION_SCORE_CYPHER)
            return [dict(record) for record in result]

    def query_forgetting(self, person_name: str) -> list[dict]:
        """Anti-object-permanence: what are you forgetting?"""
        with self.driver.session() as session:
            result = session.run(FORGETTING_CYPHER, person_name=person_name)
            return [dict(record) for record in result]
