from hf_edu.llm import FakeLLMClient
from hf_edu.llm.fake_responses import DEMO_CONTEXT, demo_responder
from hf_edu.pipeline import run_pipeline
from hf_edu.schemas import CORE_TOPICS, ClinicalContext, EducationDraft, Topic, TriggerCode


def test_pipeline_happy_path(note, store, fake_llm):
    result = run_pipeline(note, fake_llm, store)
    m = result.material
    assert [s.topic for s in m.sections] == list(CORE_TOPICS)
    assert m.warnings == []
    diet = m.sections[0]
    assert diet.clinician_consult and TriggerCode.HYPERKALEMIA in diet.triggers_applied
    activity = next(s for s in m.sections if s.topic == Topic.ACTIVITY)
    assert not activity.clinician_consult
    # every cited id was actually retrieved for that topic
    for s in m.sections:
        for it in s.items:
            assert set(it.source_ids) <= set(result.retrieved_chunk_ids[s.topic]) | {"NOTE"}


def _bad_citation_responder(retry_fixes: bool):
    state = {"gen_calls": 0}

    def respond(messages, schema):
        if schema is ClinicalContext:
            return DEMO_CONTEXT
        state["gen_calls"] += 1
        good = demo_responder(messages[:2], schema)
        if state["gen_calls"] == 1 or not retry_fixes:
            good["sections"][0]["items"].append({"text": "지어낸 문장", "source_ids": ["made_up:p9:9"]})
        return good

    return respond, state


def test_invalid_citation_retried_and_fixed(note, store):
    respond, state = _bad_citation_responder(retry_fixes=True)
    m = run_pipeline(note, FakeLLMClient(respond), store).material
    assert state["gen_calls"] == 2
    assert m.warnings == []


def test_invalid_citation_stripped_after_retry(note, store):
    respond, state = _bad_citation_responder(retry_fixes=False)
    m = run_pipeline(note, FakeLLMClient(respond), store).material
    assert state["gen_calls"] == 2
    assert any("made_up" in w for w in m.warnings)
    assert all("지어낸 문장" != it.text for s in m.sections for it in s.items)


def test_missing_section_warns(note, store):
    def respond(messages, schema):
        if schema is ClinicalContext:
            return DEMO_CONTEXT
        out = demo_responder(messages, schema)
        out["sections"] = out["sections"][:-1]
        return EducationDraft.model_validate(out)

    m = run_pipeline(note, FakeLLMClient(respond), store).material
    assert any("missing section symptom_action" in w for w in m.warnings)


def test_generation_schema_restricts_ids_per_topic(note, store, fake_llm):
    from hf_edu.pipeline.generate import NOTE_SOURCE_ID

    result = run_pipeline(note, fake_llm, store)
    _, schema, json_schema = fake_llm.calls[-1]
    assert schema is EducationDraft
    variants = json_schema["properties"]["sections"]["prefixItems"]
    assert len(variants) == json_schema["properties"]["sections"]["minItems"] == len(CORE_TOPICS)
    for variant in variants:
        topic = Topic(variant["properties"]["topic"]["const"])
        enum = variant["properties"]["items"]["items"]["properties"]["source_ids"]["items"]["enum"]
        assert set(enum) == set(result.retrieved_chunk_ids[topic]) | {NOTE_SOURCE_ID}
