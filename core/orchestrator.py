"""Orchestrator — ties NLP extraction, graph, and vector storage together."""

from datetime import datetime
from pathlib import Path

from models.schemas import ExtractionResult, Platform, SourceMetadata
from core.nlp_processor import Extractor
from core.graph_engine import GraphStore
from core.vector_engine import VectorStore


class Pipeline:
    """The dual-write ingestion pipeline."""

    def __init__(self, extractor: Extractor, graph: GraphStore, vector: VectorStore):
        self.extractor = extractor
        self.graph = graph
        self.vector = vector

    def process_text(
        self,
        text: str,
        source_id: str,
        platform: Platform = Platform.GMAIL,
        sender_name: str = "Unknown",
        sender_email: str = "unknown@unknown.com",
        received_at: datetime | None = None,
    ) -> ExtractionResult:
        """Process raw communication text through the full pipeline.

        1. Extract entities via LLM
        2. Write to Neo4j (graph)
        3. Write to ChromaDB (vector)
        """
        if received_at is None:
            received_at = datetime.now()

        # Step 1: LLM extraction
        extraction = self.extractor.extract_entities(text)

        # Step 2: Build provenance metadata
        source_meta = SourceMetadata(
            source_id=source_id,
            platform=platform,
            sender_name=sender_name,
            sender_email=sender_email,
            received_at=received_at,
        )

        # Step 3: Dual-write
        self.graph.upsert_extraction(source_meta, extraction)
        self.vector.upsert_document(
            doc_id=source_id,
            text=text,
            metadata={
                "sender_name": sender_name,
                "sender_email": sender_email,
                "platform": platform.value,
                "received_at": received_at.isoformat(),
                "summary": extraction.summary,
            },
        )

        return extraction

    def process_file(self, filepath: str, **kwargs) -> ExtractionResult:
        """Read a text file and process it through the pipeline."""
        path = Path(filepath)
        text = path.read_text(encoding="utf-8")

        # Use filename as source_id if not provided
        if "source_id" not in kwargs:
            kwargs["source_id"] = path.stem

        return self.process_text(text, **kwargs)
