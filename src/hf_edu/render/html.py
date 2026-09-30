"""Step 5: EducationMaterial -> patient-facing HTML. Minimal for now; content/design come later."""
from jinja2 import Environment, PackageLoader, select_autoescape

from hf_edu.kb import KnowledgeStore
from hf_edu.schemas import EducationMaterial

_env = Environment(
    loader=PackageLoader("hf_edu", "render/templates"),
    autoescape=select_autoescape(["html", "j2"]),
)


def render_html(material: EducationMaterial, store: KnowledgeStore) -> str:
    cited = list(dict.fromkeys(i for s in material.sections for it in s.items for i in it.source_ids))
    chunks = {c.chunk_id: c for c in store.get_chunks(cited)}
    sources = []
    for sid in cited:
        chunk = chunks.get(sid)
        doc = store.get_document(chunk.document_id) if chunk else None
        sources.append(
            {"id": sid, "label": f"{doc.title}, p.{chunk.page}" if doc and chunk else "퇴원 기록지"}
        )
    numbers = {s["id"]: n for n, s in enumerate(sources, 1)}
    return _env.get_template("education.html.j2").render(m=material, sources=sources, numbers=numbers)
