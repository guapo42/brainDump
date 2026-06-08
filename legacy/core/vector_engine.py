"""ChromaDB Vector Store — semantic embedding and retrieval."""

import chromadb


class VectorStore:
    """Interface to ChromaDB for storing and searching communication text."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection = self.client.get_or_create_collection(
            name="communication_chunks"
        )

    @classmethod
    def from_client(cls, client, collection_name: str = "communication_chunks"):
        """Create a VectorStore with an injected client (useful for testing)."""
        instance = cls.__new__(cls)
        instance.client = client
        instance.collection = client.get_or_create_collection(name=collection_name)
        return instance

    def upsert_document(self, doc_id: str, text: str, metadata: dict):
        """Store a communication chunk with its metadata for later retrieval."""
        self.collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata],
        )

    def search_context(self, query: str, n_results: int = 5) -> dict:
        """Semantic search for communications related to a query."""
        return self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )

    def get_by_ids(self, ids: list[str]) -> dict:
        """Retrieve specific documents by their source IDs."""
        return self.collection.get(ids=ids)
