"""Knowledge-base (RAG DB) schema. See docs/engineering/db_contract.md for the rules."""
from typing import Literal

from pydantic import BaseModel, Field

from hf_edu.schemas.common import Topic, TriggerCode

CHUNK_ID_PATTERN = r"^[a-z0-9_]+:p\d+:\d+$"  # {document_id}:p{page}:{n}


class SourceDocument(BaseModel):
    document_id: str = Field(pattern=r"^[a-z0-9_]+$")
    title: str
    publisher: str
    source_type: Literal["guideline", "hospital", "patient_education"]
    language: Literal["ko", "en"]
    url: str | None = None
    drive_path: str | None = Field(None, description="Path relative to data/raw/")
    license_note: str | None = None


class Chunk(BaseModel):
    """One retrievable passage. `text` is verbatim and immutable for a given `version`."""

    chunk_id: str = Field(pattern=CHUNK_ID_PATTERN)
    document_id: str
    page: int
    text: str
    topics: list[Topic]
    applies_when: list[TriggerCode] = Field(
        default_factory=list, description="Empty = general; else only relevant with these triggers"
    )
    audience: Literal["patient", "clinician"] = "patient"
    language: Literal["ko", "en"]
    version: int = 1


class RetrievalQuery(BaseModel):
    """Built by the orchestrator from ClinicalContext. The LLM never builds or runs queries."""

    topic: Topic
    triggers: list[TriggerCode] = Field(default_factory=list)
    query_text: str | None = None
    language: Literal["ko", "en"] | None = None
    audience: Literal["patient", "clinician"] = "patient"
    top_k: int = Field(3, ge=1, le=20)


class RetrievedChunk(BaseModel):
    chunk: Chunk
    score: float
    matched_triggers: list[TriggerCode] = Field(default_factory=list)
