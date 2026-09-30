"""The DB <-> pipeline interface. Any real backend (sqlite FTS, pgvector, ...) implements this.

Rules (full text in docs/engineering/db_contract.md):
- Read-only during generation. Ingestion is a separate offline step (kb/ingest.py).
- Only the orchestrator calls it; the LLM never queries the DB.
- `search` must only return chunks whose `applies_when` is empty or intersects `query.triggers`.
- Results are ordered by score, descending, at most `query.top_k` items.
"""
from typing import Protocol

from hf_edu.schemas import Chunk, RetrievalQuery, RetrievedChunk, SourceDocument


class KnowledgeStore(Protocol):
    def search(self, query: RetrievalQuery) -> list[RetrievedChunk]: ...

    def get_chunks(self, chunk_ids: list[str]) -> list[Chunk]: ...

    def get_document(self, document_id: str) -> SourceDocument | None: ...
