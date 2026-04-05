"""Docker integration tests — requires `docker compose up -d` running.

Run with: pytest -m integration
Skip by default in normal test runs.
Automatically skips if Neo4j/ChromaDB are not reachable.
"""

import pytest
from datetime import datetime

from models.schemas import (
    ExtractionResult,
    MessageTone,
    PersonEntity,
    Platform,
    ProjectEntity,
    SourceMetadata,
    TaskEntity,
)


def _neo4j_available() -> bool:
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password_here"))
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


def _chroma_available() -> bool:
    try:
        import chromadb
        client = chromadb.HttpClient(host="localhost", port=8000)
        client.heartbeat()
        return True
    except Exception:
        return False


# Mark all tests in this module as integration tests
# Skip entire module if containers aren't running
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _neo4j_available() or not _chroma_available(),
        reason="Docker containers not running (neo4j:7687 / chroma:8000)",
    ),
]


# --- Fixtures ---

@pytest.fixture(scope="module")
def neo4j_driver():
    """Connect to local Neo4j Docker container."""
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password_here"))
    yield driver
    driver.close()


@pytest.fixture(autouse=True)
def clean_neo4j(neo4j_driver):
    """Wipe all data between tests."""
    yield
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")


@pytest.fixture(scope="module")
def chroma_client():
    """Connect to local ChromaDB Docker container."""
    import chromadb
    return chromadb.HttpClient(host="localhost", port=8000)


@pytest.fixture(autouse=True)
def clean_chroma(chroma_client):
    """Delete test collection between tests."""
    yield
    try:
        chroma_client.delete_collection("communication_chunks")
    except Exception:
        pass


@pytest.fixture
def graph_store():
    from core.graph_engine import GraphStore
    store = GraphStore(uri="bolt://localhost:7687", user="neo4j", password="password_here")
    yield store
    store.close()


@pytest.fixture
def vector_store():
    from core.vector_engine import VectorStore
    return VectorStore(host="localhost", port=8000)


@pytest.fixture
def sample_meta():
    return SourceMetadata(
        source_id="test_001",
        platform=Platform.GMAIL,
        sender_name="Linda Torres",
        sender_email="ltorres@company.com",
        received_at=datetime(2026, 3, 1, 9, 0),
    )


@pytest.fixture
def sample_extraction():
    return ExtractionResult(
        people=[
            PersonEntity(name="Linda Torres", email="ltorres@company.com", role="Manager"),
            PersonEntity(name="You", email="you@company.com"),
        ],
        projects=[ProjectEntity(name="Project Phoenix", priority="high")],
        tasks=[
            TaskEntity(
                description="Submit Q1 timesheet",
                assignee="You",
                due_date="2026-01-16",
                priority="medium",
            ),
            TaskEntity(
                description="Write Phoenix design doc",
                assignee="You",
                due_date="2026-02-06",
                priority="high",
                project="Project Phoenix",
                waiting_on="Linda Torres",
            ),
        ],
        summary="Linda requests timesheet and Phoenix design doc.",
        tone=MessageTone(urgency_language=0.5, escalation_signals=False),
    )


# --- Tests ---

class TestNeo4jUpsertAndQuery:
    def test_upsert_creates_nodes(self, graph_store, sample_meta, sample_extraction):
        graph_store.upsert_extraction(sample_meta, sample_extraction)

        results = graph_store.query_tasks_by_assignee("You")
        assert len(results) >= 1
        task_names = [r["task"] for r in results]
        assert "Submit Q1 timesheet" in task_names

    def test_hanging_tasks(self, graph_store, sample_meta, sample_extraction):
        graph_store.upsert_extraction(sample_meta, sample_extraction)

        results = graph_store.query_hanging_tasks()
        assert len(results) >= 1
        assert any(r["waiting_on"] == "Linda Torres" for r in results)

    def test_project_overview(self, graph_store, sample_meta, sample_extraction):
        graph_store.upsert_extraction(sample_meta, sample_extraction)

        results = graph_store.query_project_overview()
        assert len(results) >= 1
        assert any(r["project"] == "Project Phoenix" for r in results)

    def test_tasks_due_between(self, graph_store, sample_meta, sample_extraction):
        graph_store.upsert_extraction(sample_meta, sample_extraction)

        results = graph_store.query_tasks_due_between("2026-01-01", "2026-01-31")
        assert len(results) >= 1
        assert any(r["task"] == "Submit Q1 timesheet" for r in results)

    def test_overdue_tasks(self, graph_store, sample_meta, sample_extraction):
        graph_store.upsert_extraction(sample_meta, sample_extraction)

        results = graph_store.query_overdue_tasks("2026-03-01")
        assert len(results) >= 1

    def test_tasks_from_sender(self, graph_store, sample_meta, sample_extraction):
        graph_store.upsert_extraction(sample_meta, sample_extraction)

        results = graph_store.query_tasks_from_sender("Linda Torres")
        assert len(results) >= 1

    def test_relationship_health(self, graph_store, sample_meta, sample_extraction):
        graph_store.upsert_extraction(sample_meta, sample_extraction)

        results = graph_store.query_relationship_health("2026-03-01")
        assert len(results) >= 1
        assert any(r["person"] == "Linda Torres" for r in results)


class TestNeo4jThreadAwareness:
    def test_responds_to_edge(self, graph_store):
        meta1 = SourceMetadata(
            source_id="thread_msg_1", platform=Platform.SLACK,
            sender_name="Sarah Chen", sender_email="schen@company.com",
            received_at=datetime(2026, 3, 1, 9, 0), thread_id="thread_abc",
        )
        meta2 = SourceMetadata(
            source_id="thread_msg_2", platform=Platform.SLACK,
            sender_name="You", sender_email="you@company.com",
            received_at=datetime(2026, 3, 1, 10, 0), thread_id="thread_abc",
        )
        extraction = ExtractionResult(people=[], tasks=[], summary="Thread test.")

        graph_store.upsert_extraction(meta1, extraction)
        graph_store.upsert_extraction(meta2, extraction)

        # Verify RESPONDS_TO edge exists
        with graph_store.driver.session() as session:
            result = session.run(
                "MATCH (a:Source)-[:RESPONDS_TO]->(b:Source) RETURN a.id, b.id"
            )
            records = [dict(r) for r in result]
        assert len(records) >= 1

    def test_unanswered_threads(self, graph_store):
        meta1 = SourceMetadata(
            source_id="unanswered_1", platform=Platform.SLACK,
            sender_name="You", sender_email="you@company.com",
            received_at=datetime(2026, 3, 1, 9, 0), thread_id="thread_xyz",
        )
        meta2 = SourceMetadata(
            source_id="unanswered_2", platform=Platform.SLACK,
            sender_name="Sarah Chen", sender_email="schen@company.com",
            received_at=datetime(2026, 3, 1, 14, 0), thread_id="thread_xyz",
        )
        extraction = ExtractionResult(people=[], tasks=[], summary="Unanswered test.")

        graph_store.upsert_extraction(meta1, extraction)
        graph_store.upsert_extraction(meta2, extraction)

        results = graph_store.query_unanswered_threads("You")
        assert len(results) >= 1
        assert results[0]["last_sender"] == "Sarah Chen"


class TestChromaDB:
    def test_upsert_and_search(self, vector_store):
        vector_store.upsert_document(
            doc_id="test_001",
            text="Phoenix milestone 1 is due Friday. The API layer needs to be complete.",
            metadata={"sender_name": "Robert Kim", "platform": "gmail"},
        )
        vector_store.upsert_document(
            doc_id="test_002",
            text="Please submit your Q1 timesheet by January 16th.",
            metadata={"sender_name": "Linda Torres", "platform": "gmail"},
        )

        results = vector_store.search_context("Phoenix API milestone", n_results=2)
        assert len(results["documents"][0]) >= 1
        # The Phoenix-related doc should rank higher
        assert "Phoenix" in results["documents"][0][0]

    def test_get_by_ids(self, vector_store):
        vector_store.upsert_document(
            doc_id="test_get_1",
            text="Test document for retrieval.",
            metadata={"sender_name": "Test"},
        )

        results = vector_store.get_by_ids(["test_get_1"])
        assert len(results["documents"]) == 1


class TestFullPipeline:
    def test_dual_write(self, graph_store, vector_store, sample_meta, sample_extraction):
        """Test Pipeline with real stores but mocked extractor."""
        from core.orchestrator import Pipeline

        # Create a mock extractor that returns our fixture
        class MockExtractor:
            def extract_entities(self, text):
                return sample_extraction

        pipeline = Pipeline(MockExtractor(), graph_store, vector_store)
        result = pipeline.process_text(
            text="Linda says submit timesheet and Phoenix design doc.",
            source_id="pipeline_test_001",
            sender_name="Linda Torres",
            sender_email="ltorres@company.com",
        )

        # Verify graph has data
        tasks = graph_store.query_tasks_by_assignee("You")
        assert len(tasks) >= 1

        # Verify vector store has data
        search = vector_store.search_context("timesheet", n_results=1)
        assert len(search["documents"][0]) >= 1
