import pytest
from pydantic import ValidationError

from hf_edu.llm.fake_responses import DEMO_CONTEXT
from hf_edu.schemas import Chunk, ClinicalContext, DischargeNote, EducationDraft, TriggerCode


def test_context_round_trip():
    ctx = ClinicalContext.model_validate(DEMO_CONTEXT)
    assert ClinicalContext.model_validate_json(ctx.model_dump_json()) == ctx
    assert ctx.active_triggers() == [TriggerCode.HYPERKALEMIA, TriggerCode.FLUID_RESTRICTION]


def test_chunk_id_format_enforced():
    base = {"document_id": "doc", "page": 1, "text": "t", "topics": ["diet"], "language": "ko"}
    Chunk(chunk_id="doc:p1:1", **base)
    with pytest.raises(ValidationError):
        Chunk(chunk_id="Doc page 1", **base)


def test_note_rejects_empty_text():
    with pytest.raises(ValidationError):
        DischargeNote(text="short")


def test_json_schemas_export():
    # These are sent as response_format json_schema to vLLM.
    for model in (ClinicalContext, EducationDraft):
        assert model.model_json_schema()["type"] == "object"
