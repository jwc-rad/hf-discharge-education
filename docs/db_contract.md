# Knowledge DB ↔ LLM contract

The DB is a dummy in-memory store for now (`src/hf_edu/kb/dummy.py` + `seed_chunks.json`).
This document fixes the **schema and rules** so the DB team can build the real backend
(sqlite FTS, pgvector, ...) without touching the pipeline. Code is the source of truth:
`src/hf_edu/schemas/knowledge.py`, `src/hf_edu/kb/store.py`.

## Schema

### `SourceDocument`
| field | type | notes |
|---|---|---|
| `document_id` | `str` `^[a-z0-9_]+$` | stable slug, e.g. `kshf_living` |
| `title`, `publisher` | `str` | shown in HTML footnotes |
| `source_type` | `guideline \| hospital \| patient_education` | matches `data/raw/` subfolder |
| `language` | `ko \| en` | |
| `url`, `drive_path`, `license_note` | `str?` | `drive_path` relative to `data/raw/` |

### `Chunk`
| field | type | notes |
|---|---|---|
| `chunk_id` | `str` `{document_id}:p{page}:{n}` | stable; cited by generated text |
| `document_id`, `page` | | |
| `text` | `str` | **verbatim** passage; never paraphrased |
| `topics` | `list[Topic]` | `diet`, `activity`, `medication`, `symptom_action`, `followup` |
| `applies_when` | `list[TriggerCode]` | empty = general; else only for patients with one of these triggers |
| `audience` | `patient \| clinician` | generation only uses `patient` for now |
| `language` | `ko \| en` | |
| `version` | `int` | bump when text changes |

## Interface

```python
class KnowledgeStore(Protocol):
    def search(self, query: RetrievalQuery) -> list[RetrievedChunk]: ...
    def get_chunks(self, chunk_ids: list[str]) -> list[Chunk]: ...
    def get_document(self, document_id: str) -> SourceDocument | None: ...
```

`RetrievalQuery{topic, triggers, query_text?, language?, audience, top_k}` →
`RetrievedChunk{chunk, score, matched_triggers}`.

`search` MUST:
- return only chunks with `query.topic in chunk.topics` and matching `audience`/`language` (if given);
- exclude chunks whose non-empty `applies_when` does not intersect `query.triggers`;
- return at most `top_k`, ordered by `score` descending (ties: `chunk_id`);
- be deterministic for the same DB version and query.

## Rules

1. **The LLM never queries the DB.** The orchestrator (`pipeline/retrieve.py`) builds the queries from
   the extracted `ClinicalContext`: per topic one general query (`triggers=[]`), plus one trigger query
   when the topic has active triggers, merged with trigger-matched chunks first. No tool calls /
   function calling to the DB.
2. **Read-only at generation time.** Writes happen only in offline ingestion (`kb/ingest.py`).
3. **Chunks reach the LLM as data**: only `{id, text}` inside the JSON user message; the system prompt
   states that sources are data, not instructions.
4. **Citations are closed-world.** Each generated item's `source_ids` must be a subset of the chunk IDs
   provided *for that topic*, plus `NOTE` (the discharge note). On violation: one retry with the error
   list → then invalid IDs are stripped, items left without any source are dropped, and a `warning`
   is recorded in `EducationMaterial.warnings`.
5. **Immutable text per version.** Editing a chunk's text requires a new `version`, so a stored
   material's citations stay reproducible.
6. **No patient data in the DB.** The KB contains only published / institutional education material.
   Notes (MIMIC or EHR) are request input only and are not persisted by the API.
7. **Budget.** `top_k` per query (default 3, `RETRIEVAL_TOP_K`) → ≤ 2 × `top_k` per topic,
   ≤ 24 chunks per request over the 4 core topics.
   Keep chunks short (≈ 1–3 sentences, < 500 chars) so the prompt fits the 8–16k context window.
8. **Triggers are deterministic.** `triggers_applied` / `clinician_consult` are set by code from
   `TRIGGER_TOPICS`, not by the LLM.

## Open questions for the DB team
- Chunking granularity and who tags `topics` / `applies_when` (clinician team mapping sheet?).
- Korean vs. English sources: translate at ingestion, or let generation translate English chunks?
- Retrieval backend: keyword (sqlite FTS5) vs. embeddings. Embedding model must also run on-prem.
- `query_text` is currently built from English note content while the dummy chunks are Korean, so
  the dummy keyword score barely contributes. A real backend needs cross-lingual retrieval
  (multilingual embeddings) or Korean query rewriting.
