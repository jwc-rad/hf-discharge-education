import importlib.util
from pathlib import Path

import pytest

BUILD = Path(__file__).resolve().parents[1] / "demo/build_demo.py"


@pytest.fixture(scope="module")
def demo():
    spec = importlib.util.spec_from_file_location("build_demo", BUILD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def samples(demo):
    return {s["id"]: s for s in demo.build_samples()}  # raises on warnings / bad evidence


def test_every_sample_renders_core_sections(samples):
    assert set(samples) == {"01", "02", "03"}
    for s in samples.values():
        assert not s["material"]["warnings"]
        assert s["html"].count("<section") == 4


@pytest.mark.parametrize(
    ("sample_id", "triggers", "consult_topics"),
    [
        ("01", {"hyperkalemia", "fluid_restriction"}, {"diet", "medication"}),
        ("02", {"ckd"}, {"diet", "medication"}),
        ("03", {"warfarin"}, {"diet", "medication"}),
    ],
)
def test_personalization_follows_triggers(samples, sample_id, triggers, consult_topics):
    s = samples[sample_id]
    assert {t["code"] for t in s["context"]["triggers"] if t["present"]} == triggers
    consult = {sec["topic"] for sec in s["material"]["sections"] if sec["clinician_consult"]}
    assert consult == consult_topics


def test_trigger_chunks_only_for_matching_sample(samples):
    def chunk_ids(s):
        return {h["id"] for hits in s["retrieved"].values() for h in hits}

    warfarin_chunk = "dummy_patient_guide:p4:3"
    potassium_chunk = "dummy_patient_guide:p2:1"
    assert warfarin_chunk in chunk_ids(samples["03"])
    assert warfarin_chunk not in chunk_ids(samples["01"])
    assert potassium_chunk in chunk_ids(samples["01"])
    assert potassium_chunk not in chunk_ids(samples["02"])


def test_page_embeds_data_safely(demo, samples):
    page = demo.build_page(list(samples.values()))
    assert page.startswith("<!doctype html>")
    assert demo.DATA_PLACEHOLDER not in page
    assert page.count("</script>") == 1  # embedded HTML cannot close the <script> early
    assert "<\\/section>" in page
    fragment = demo.build_page(list(samples.values()), standalone=False)
    assert "<html" not in fragment.split("const DATA", 1)[0]
