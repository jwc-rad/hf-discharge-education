"""Offline ingestion: data/raw/**/*.pdf -> SourceDocument + Chunk rows (pipeline stage 1).

Not implemented yet. Expected contract for whoever builds it:
1. One SourceDocument per PDF; `document_id` is a stable snake_case slug, `drive_path` is
   the path relative to data/raw/.
2. Split into passages; `chunk_id = f"{document_id}:p{page}:{n}"`, `text` verbatim (no
   paraphrasing: generation cites it).
3. Tag each chunk with `topics` and, if the passage only applies to some patients,
   `applies_when` trigger codes (clinician team mapping).
4. Changing a chunk's text requires bumping `version`; never edit text in place.
5. Write to data/processed/ (git-ignored) and load it through a KnowledgeStore backend.
"""
from pathlib import Path

from hf_edu.schemas import Chunk, SourceDocument

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def ingest_pdf(path: Path) -> tuple[SourceDocument, list[Chunk]]:
    raise NotImplementedError("PDF ingestion is not implemented yet; see module docstring.")
