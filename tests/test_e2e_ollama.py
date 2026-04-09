"""End-to-end test: real Ollama LLM → Neo4j → ChromaDB → query.

Exercises the full ingestion path that the unit tests skip:
  raw email text → Extractor (Ollama) → GraphStore + VectorStore → query API.

Skips automatically if Ollama, Neo4j, or ChromaDB aren't reachable.

Run with:
    pytest tests/test_e2e_ollama.py -v -m integration -s
"""

from datetime import datetime
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

from models.schemas import Platform, SourceMetadata

load_dotenv()


# --- Availability checks ---

def _ollama_available() -> bool:
    try:
        return requests.get("http://localhost:11434/api/tags", timeout=2).ok
    except Exception:
        return False


def _neo4j_available() -> bool:
    try:
        from neo4j import GraphDatabase
        d = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password_here"))
        d.verify_connectivity()
        d.close()
        return True
    except Exception:
        return False


def _chroma_available() -> bool:
    try:
        import chromadb
        chromadb.HttpClient(host="localhost", port=8000).heartbeat()
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (_ollama_available() and _neo4j_available() and _chroma_available()),
        reason="Requires Ollama (11434), Neo4j (7687), and ChromaDB (8000)",
    ),
]


# --- Fixtures ---

@pytest.fixture(scope="module")
def extractor():
    from core.nlp_processor import create_extractor_from_env
    return create_extractor_from_env()


@pytest.fixture
def graph_store():
    from core.graph_engine import GraphStore
    store = GraphStore(uri="bolt://localhost:7687", user="neo4j", password="password_here")
    # clean slate
    with store.driver.session() as s:
        s.run("MATCH (n) DETACH DELETE n")
    yield store
    with store.driver.session() as s:
        s.run("MATCH (n) DETACH DELETE n")
    store.close()


@pytest.fixture
def vector_store():
    from core.vector_engine import VectorStore
    import chromadb
    client = chromadb.HttpClient(host="localhost", port=8000)
    try:
        client.delete_collection("communication_chunks")
    except Exception:
        pass
    store = VectorStore(host="localhost", port=8000)
    yield store
    try:
        client.delete_collection("communication_chunks")
    except Exception:
        pass


# --- The end-to-end test ---

def test_ingest_email_1_through_ollama(extractor, graph_store, vector_store):
    """Real LLM extracts entities from email_1.txt, then stores and queries them."""
    text = Path("tests/email_1.txt").read_text()

    # 1. Extract via real Ollama
    result = extractor.extract_entities(text)
    print(f"\n[extract] {len(result.people)} people, {len(result.projects)} projects, "
          f"{len(result.tasks)} tasks")

    # Sanity-check the extraction itself
    assert len(result.tasks) >= 2, "expected multiple tasks from email_1"
    assert any("EPA" in p.name for p in result.projects), "should extract EPA project"
    names = {p.name for p in result.people}
    assert any("Sarah" in n for n in names), f"should extract Sarah, got {names}"

    # 2. Persist to both stores
    meta = SourceMetadata(
        source_id="e2e_email_1",
        platform=Platform.GMAIL,
        sender_name="Alex Vance",
        sender_email="avance@rti.org",
        received_at=datetime(2026, 2, 26, 9, 0),
    )
    graph_store.upsert_extraction(meta, result)
    vector_store.upsert_document(
        doc_id="e2e_email_1",
        text=text,
        metadata={"sender": "Alex Vance", "platform": "gmail"},
    )

    # 3. Query graph back — at least one Task and one Person should exist
    with graph_store.driver.session() as s:
        task_count = s.run("MATCH (t:Task) RETURN count(t) AS n").single()["n"]
        person_count = s.run("MATCH (p:Person) RETURN count(p) AS n").single()["n"]
        gen_count = s.run(
            "MATCH (:Source)-[:GENERATED]->(:Task) RETURN count(*) AS n"
        ).single()["n"]
    print(f"[graph] tasks={task_count} people={person_count} GENERATED={gen_count}")
    assert task_count >= 2, f"expected >=2 Task nodes, got {task_count}"
    assert person_count >= 2, f"expected >=2 Person nodes, got {person_count}"
    assert gen_count >= 2, f"expected Source→Task provenance edges, got {gen_count}"

    # 4. Query vector store — should retrieve the email by semantic search
    hits = vector_store.search_context("AWS EC2 provisioning blockers", n_results=3)
    assert hits and hits.get("ids") and hits["ids"][0], "vector search returned nothing"
    assert "e2e_email_1" in hits["ids"][0], f"expected our doc, got {hits['ids']}"
    print(f"[vector] retrieved {len(hits['ids'][0])} hits, top match: {hits['ids'][0][0]}")
