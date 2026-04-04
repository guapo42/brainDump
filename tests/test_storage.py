"""Tests for graph and vector storage engines (mocked — no Docker required)."""

from unittest.mock import MagicMock, patch

from core.graph_engine import GraphStore, UPSERT_CYPHER
from core.vector_engine import VectorStore


class TestGraphStore:
    def test_upsert_extraction_calls_session_run(
        self, sample_source_metadata, sample_extraction_result
    ):
        """Verify the correct Cypher and params are sent to Neo4j."""
        # Mock the Neo4j driver
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

        with patch("core.graph_engine.GraphDatabase.driver", return_value=mock_driver):
            store = GraphStore(uri="bolt://fake:7687", user="neo4j", password="test")
            store.upsert_extraction(sample_source_metadata, sample_extraction_result)

        # session.run should have been called with our UPSERT_CYPHER
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert call_args.args[0] == UPSERT_CYPHER

        # Check params
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
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))

        mock_session = MagicMock()
        mock_session.run.return_value = mock_result

        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

        with patch("core.graph_engine.GraphDatabase.driver", return_value=mock_driver):
            store = GraphStore(uri="bolt://fake:7687", user="neo4j", password="test")
            results = store.query_hanging_tasks()

        assert len(results) == 1
        assert results[0]["waiting_on"] == "Alice"


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
