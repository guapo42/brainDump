# Phase 3: Graph and Vector Storage Engines (Mocked)

## Objective
Create the interface classes for Neo4j and ChromaDB, implementing the core upsert and query logic. Use mocked database clients for TDD.

## Specifications
1. **Vector Engine (`core/vector_engine.py`):**
   - Implement a `VectorStore` class with `upsert_document(text, metadata)` and `search_context(query)` methods.
   - Use ChromaDB syntax, but design the class so the underlying client can be injected/mocked.
2. **Graph Engine (`core/graph_engine.py`):**
   - Implement a `GraphStore` class with a method `upsert_extraction(source_meta: SourceMetadata, extraction: ExtractionResult)`.
   - Write the Cypher query inside this method to `MERGE` Projects, People, Tasks, and create the `(Source)-[:GENERATED]->(Task)` relationships.
3. **Testing (`tests/test_storage.py`):**
   - Write tests that instantiate `VectorStore` and `GraphStore` with `MagicMock()` database clients.
   - For Neo4j, assert that `session.run()` is called with the correct Cypher string and parameters.
   - For ChromaDB, assert that `collection.add()` is called with the correct document and metadata.

## Prompt for Claude Code
"Read `docs/phase3_storage_engines.md`. Implement `vector_engine.py` and `graph_engine.py` focusing on the interface and query structures. Write tests in `test_storage.py` using `MagicMock` to verify the DB clients receive the correct commands without needing live databases. Run the tests."