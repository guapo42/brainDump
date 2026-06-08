"""Tests for graph and vector storage engines (mocked — no Docker required)."""

from unittest.mock import MagicMock, patch

from core.graph_engine import (
    GraphStore,
    UPSERT_CYPHER,
    TASKS_BY_ASSIGNEE_CYPHER,
    TASKS_DUE_BETWEEN_CYPHER,
    TASKS_FROM_SENDER_CYPHER,
    OVERDUE_TASKS_CYPHER,
)
from core.vector_engine import VectorStore


def _mock_graph_store():
    """Create a GraphStore with a mocked Neo4j driver."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)
    return mock_driver, mock_session


class TestGraphStore:
    def test_upsert_extraction_calls_session_run(
        self, sample_source_metadata, sample_extraction_result
    ):
        """Verify the correct Cypher and params are sent to Neo4j."""
        mock_driver, mock_session = _mock_graph_store()

        with patch("core.graph_engine.GraphDatabase.driver", return_value=mock_driver):
            store = GraphStore(uri="bolt://fake:7687", user="neo4j", password="test")
            store.upsert_extraction(sample_source_metadata, sample_extraction_result)

        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert call_args.args[0] == UPSERT_CYPHER

        kwargs = call_args.kwargs
        assert kwargs["source_id"] == "email_001"
        assert kwargs["platform"] == "gmail"
        assert kwargs["sender_name"] == "Alex Vance"
        assert len(kwargs["people"]) == 3
        assert len(kwargs["tasks"]) == 3
        assert kwargs["tasks"][0]["description"] == "Finalize the database migration"

    def test_query_hanging_tasks(self):
        """Verify hanging tasks query returns list of dicts."""
        mock_record = {"task": "Fix bug", "waiting_on": "Alice", "due_date": None, "priority": "high"}
        mock_driver, mock_session = _mock_graph_store()
        mock_session.run.return_value = MagicMock(__iter__=MagicMock(return_value=iter([mock_record])))

        with patch("core.graph_engine.GraphDatabase.driver", return_value=mock_driver):
            store = GraphStore(uri="bolt://fake:7687", user="neo4j", password="test")
            results = store.query_hanging_tasks()

        assert len(results) == 1
        assert results[0]["waiting_on"] == "Alice"

    def test_query_tasks_by_assignee(self):
        """REC-5: Verify assignee query uses correct Cypher."""
        mock_record = {"task": "Write docs", "status": "pending", "due_date": "2026-03-01",
                       "priority": "medium", "project": "Phoenix", "blocked_by": None}
        mock_driver, mock_session = _mock_graph_store()
        mock_session.run.return_value = MagicMock(__iter__=MagicMock(return_value=iter([mock_record])))

        with patch("core.graph_engine.GraphDatabase.driver", return_value=mock_driver):
            store = GraphStore(uri="bolt://fake:7687", user="neo4j", password="test")
            results = store.query_tasks_by_assignee("You")

        mock_session.run.assert_called_once_with(TASKS_BY_ASSIGNEE_CYPHER, person_name="You")
        assert len(results) == 1
        assert results[0]["task"] == "Write docs"

    def test_query_tasks_due_between(self):
        """REC-6: Verify date-range query uses correct Cypher."""
        mock_record = {"task": "Deploy", "status": "pending", "due_date": "2026-03-05",
                       "priority": "high", "assignee": "You", "project": "Phoenix"}
        mock_driver, mock_session = _mock_graph_store()
        mock_session.run.return_value = MagicMock(__iter__=MagicMock(return_value=iter([mock_record])))

        with patch("core.graph_engine.GraphDatabase.driver", return_value=mock_driver):
            store = GraphStore(uri="bolt://fake:7687", user="neo4j", password="test")
            results = store.query_tasks_due_between("2026-03-01", "2026-03-07")

        mock_session.run.assert_called_once_with(
            TASKS_DUE_BETWEEN_CYPHER, start_date="2026-03-01", end_date="2026-03-07"
        )
        assert len(results) == 1

    def test_query_tasks_from_sender(self):
        """REC-7: Verify sender query uses correct Cypher."""
        mock_record = {"task": "Submit timesheet", "status": "pending", "due_date": "2026-01-16",
                       "priority": "medium", "assignee": "You", "requested_at": "2026-01-05"}
        mock_driver, mock_session = _mock_graph_store()
        mock_session.run.return_value = MagicMock(__iter__=MagicMock(return_value=iter([mock_record])))

        with patch("core.graph_engine.GraphDatabase.driver", return_value=mock_driver):
            store = GraphStore(uri="bolt://fake:7687", user="neo4j", password="test")
            results = store.query_tasks_from_sender("Linda Torres")

        mock_session.run.assert_called_once_with(
            TASKS_FROM_SENDER_CYPHER, sender_name="Linda Torres"
        )
        assert len(results) == 1

    def test_query_overdue_tasks(self):
        """REC-8: Verify overdue query uses correct Cypher."""
        mock_record = {"task": "Fix bug", "status": "pending", "due_date": "2026-02-01",
                       "priority": "high", "assignee": "You", "project": "EPA",
                       "blocked_by": None}
        mock_driver, mock_session = _mock_graph_store()
        mock_session.run.return_value = MagicMock(__iter__=MagicMock(return_value=iter([mock_record])))

        with patch("core.graph_engine.GraphDatabase.driver", return_value=mock_driver):
            store = GraphStore(uri="bolt://fake:7687", user="neo4j", password="test")
            results = store.query_overdue_tasks("2026-03-01")

        mock_session.run.assert_called_once_with(OVERDUE_TASKS_CYPHER, today="2026-03-01")
        assert len(results) == 1
        assert results[0]["task"] == "Fix bug"


class TestVectorStore:
    def test_upsert_document_calls_collection_upsert(self):
        """Verify ChromaDB collection.upsert is called with correct args."""
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        store = VectorStore.from_client(mock_client)
        store.upsert_document(
            doc_id="email_001",
            text="Hello, this is a test email.",
            metadata={"sender_name": "Alice", "platform": "gmail"},
        )

        mock_collection.upsert.assert_called_once_with(
            ids=["email_001"],
            documents=["Hello, this is a test email."],
            metadatas=[{"sender_name": "Alice", "platform": "gmail"}],
        )

    def test_search_context_calls_collection_query(self):
        """Verify ChromaDB collection.query is called correctly."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["Some email about a task"]],
            "ids": [["email_001"]],
        }
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        store = VectorStore.from_client(mock_client)
        result = store.search_context("who is blocked?", n_results=3)

        mock_collection.query.assert_called_once_with(
            query_texts=["who is blocked?"],
            n_results=3,
        )
        assert "documents" in result
