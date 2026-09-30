"""Dummy in-memory knowledge store backed by seed_chunks.json.

Placeholder until the real DB is built from data/raw/. Scoring is deliberately naive:
trigger match first, then keyword overlap with `query_text`.
"""
import json
import re
from pathlib import Path

from hf_edu.schemas import Chunk, RetrievalQuery, RetrievedChunk, SourceDocument

SEED_PATH = Path(__file__).with_name("seed_chunks.json")


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[\w가-힣]+", text.lower()))


class InMemoryKnowledgeStore:
    def __init__(self, documents: list[SourceDocument], chunks: list[Chunk]):
        self._documents = {d.document_id: d for d in documents}
        self._chunks = {c.chunk_id: c for c in chunks}
        unknown = {c.document_id for c in chunks} - set(self._documents)
        if unknown:
            raise ValueError(f"chunks reference unknown documents: {sorted(unknown)}")

    @classmethod
    def from_json(cls, path: Path = SEED_PATH) -> "InMemoryKnowledgeStore":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            [SourceDocument.model_validate(d) for d in data["documents"]],
            [Chunk.model_validate(c) for c in data["chunks"]],
        )

    def search(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        wanted = set(query.triggers)
        q_tokens = _tokens(query.query_text or "")
        hits = []
        for chunk in self._chunks.values():
            if query.topic not in chunk.topics or chunk.audience != query.audience:
                continue
            if query.language and chunk.language != query.language:
                continue
            matched = [t for t in chunk.applies_when if t in wanted]
            if chunk.applies_when and not matched:
                continue
            overlap = len(q_tokens & _tokens(chunk.text)) / (len(q_tokens) or 1)
            score = 1.0 * len(matched) + overlap
            hits.append(RetrievedChunk(chunk=chunk, score=round(score, 4), matched_triggers=matched))
        hits.sort(key=lambda h: (-h.score, h.chunk.chunk_id))
        return hits[: query.top_k]

    def get_chunks(self, chunk_ids: list[str]) -> list[Chunk]:
        return [self._chunks[i] for i in chunk_ids if i in self._chunks]

    def get_document(self, document_id: str) -> SourceDocument | None:
        return self._documents.get(document_id)
