from hf_edu.pipeline import run_pipeline
from hf_edu.render import render_html


def test_render_has_sections_and_sources(note, store, fake_llm):
    html = render_html(run_pipeline(note, fake_llm, store).material, store)
    assert html.count("<section") == 4
    assert "의료진 검토 전 초안" in html
    assert "[DUMMY] 심부전 환자 생활 안내" in html
    assert "의료진과 꼭 상의하세요" in html


def test_render_escapes_model_text(store):
    from hf_edu.schemas import EducationItem, EducationMaterial, EducationSection, Topic

    m = EducationMaterial(
        model="x",
        sections=[EducationSection(topic=Topic.DIET, title="t", items=[
            EducationItem(text="<script>alert(1)</script>", source_ids=["NOTE"])])],
    )
    assert "<script>alert" not in render_html(m, store)
