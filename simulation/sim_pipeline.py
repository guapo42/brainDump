"""SimPipeline: direct ingest bypassing the LLM layer."""

from models.schemas import ExtractionResult, SourceMetadata
from simulation.stores import InMemoryGraphStore, InMemoryVectorStore


class SimPipeline:
    """Accepts pre-built ExtractionResult objects and writes to both stores."""

    def __init__(self, graph: InMemoryGraphStore, vector: InMemoryVectorStore):
        self.graph = graph
        self.vector = vector

    def ingest(
        self,
        message_text: str,
        source_meta: SourceMetadata,
        extraction: ExtractionResult,
    ):
        """Write to graph + vector stores without calling an LLM."""
        self.graph.upsert_extraction(source_meta, extraction)
        self.vector.upsert_document(
            doc_id=source_meta.source_id,
            text=message_text,
            metadata={
                "sender_name": source_meta.sender_name,
                "sender_email": source_meta.sender_email,
                "platform": source_meta.platform.value,
                "received_at": source_meta.received_at.isoformat(),
                "summary": extraction.summary,
            },
        )
