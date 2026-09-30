from hf_edu.schemas import RetrievalQuery, Topic, TriggerCode


def test_general_chunks_only_without_triggers(store):
    hits = store.search(RetrievalQuery(topic=Topic.DIET, top_k=20))
    assert hits and all(not h.chunk.applies_when for h in hits)


def test_trigger_chunks_ranked_first(store):
    hits = store.search(RetrievalQuery(topic=Topic.DIET, triggers=[TriggerCode.HYPERKALEMIA], top_k=3))
    assert TriggerCode.HYPERKALEMIA in hits[0].matched_triggers
    assert all(Topic.DIET in h.chunk.topics for h in hits)


def test_top_k_respected(store):
    assert len(store.search(RetrievalQuery(topic=Topic.DIET, top_k=1))) == 1


def test_get_chunks_skips_unknown(store):
    assert [c.chunk_id for c in store.get_chunks(["dummy_patient_guide:p1:1", "nope:p1:1"])] == [
        "dummy_patient_guide:p1:1"
    ]


def test_trigger_chunks_do_not_crowd_out_general(store):
    from hf_edu.llm.fake_responses import DEMO_CONTEXT
    from hf_edu.pipeline.retrieve import build_queries, retrieve
    from hf_edu.schemas import ClinicalContext

    diet = retrieve(store, build_queries(ClinicalContext.model_validate(DEMO_CONTEXT), top_k=3))[Topic.DIET]
    assert diet[0].matched_triggers  # trigger-specific first
    assert any(not h.chunk.applies_when for h in diet)  # general guidance still present
    assert len({h.chunk.chunk_id for h in diet}) == len(diet)
