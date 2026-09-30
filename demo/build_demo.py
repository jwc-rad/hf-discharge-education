"""Build demo/index.html: a static, self-contained walkthrough of the pipeline on fixed samples.

No LLM is called. Each fixture in demo/fixtures/ holds hand-written "LLM" output (extraction
`context` and generation `draft`); everything else is the real code: retrieval from the dummy
KB, citation validation, finalize (titles, triggers, consult flag) and HTML rendering.

    python demo/build_demo.py                    # writes demo/index.html
    python demo/build_demo.py --fragment out.html  # also writes a skeleton-less copy (Artifact publish)
"""
import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from hf_edu.kb import InMemoryKnowledgeStore
from hf_edu.llm import FakeLLMClient
from hf_edu.pipeline.extract import extract_context
from hf_edu.pipeline.generate import NOTE_SOURCE_ID, generate_material
from hf_edu.pipeline.retrieve import build_queries, retrieve
from hf_edu.render import render_html
from hf_edu.schemas import (
    TOPIC_TITLES,
    TRIGGER_TOPICS,
    ClinicalContext,
    DischargeNote,
    EducationDraft,
)

DEMO_DIR = Path(__file__).resolve().parent
REPO = DEMO_DIR.parent
FIXTURES = DEMO_DIR / "fixtures"
TEMPLATE = DEMO_DIR / "template.html"
OUTPUT = DEMO_DIR / "index.html"
DATA_PLACEHOLDER = "/*__DEMO_DATA__*/null"
MODEL_NAME = "demo-dummy-llm"
GENERATED_AT = datetime(2026, 9, 30, 9, 0, tzinfo=UTC)  # pinned so the output is reproducible
TOP_K = 3


class FixtureError(ValueError):
    pass


def _responder(fixture: dict):
    def respond(messages: list[dict], schema: type[BaseModel]) -> object:
        if schema is ClinicalContext:
            return fixture["context"]
        if schema is EducationDraft:
            return fixture["draft"]
        raise ValueError(f"no demo response for {schema.__name__}")

    return respond


def _check_evidence(fixture_id: str, note: str, context: ClinicalContext) -> None:
    spans = [
        i.evidence
        for i in [
            *context.discharge_medications,
            *context.diet_instructions,
            *context.activity_instructions,
            *context.followup,
        ]
    ] + [t.evidence for t in context.triggers if t.evidence]
    missing = [s for s in spans if s not in note]
    if missing:
        raise FixtureError(f"{fixture_id}: evidence not found verbatim in note: {missing}")


def build_sample(path: Path, store: InMemoryKnowledgeStore) -> dict:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    note_text = (REPO / fixture["note_path"]).read_text(encoding="utf-8")
    llm = FakeLLMClient(_responder(fixture), model=MODEL_NAME)

    context = extract_context(DischargeNote(text=note_text), llm)
    _check_evidence(path.stem, note_text, context)
    queries = build_queries(context, TOP_K)
    retrieved = retrieve(store, queries)
    material = generate_material(context, retrieved, llm)
    if material.warnings:
        raise FixtureError(f"{path.stem}: pipeline warnings {material.warnings}")
    material = material.model_copy(update={"generated_at": GENERATED_AT})

    return {
        "id": path.stem,
        "title": fixture["title"],
        "summary": fixture["summary"],
        "note_path": fixture["note_path"],
        "note": note_text,
        "context": context.model_dump(mode="json"),
        "queries": [q.model_dump(mode="json") for q in queries],
        "retrieved": {
            topic.value: [
                {
                    "id": h.chunk.chunk_id,
                    "doc": store.get_document(h.chunk.document_id).title,
                    "page": h.chunk.page,
                    "text": h.chunk.text,
                    "score": h.score,
                    "matched": [t.value for t in h.matched_triggers],
                    "applies_when": [t.value for t in h.chunk.applies_when],
                }
                for h in hits
            ]
            for topic, hits in retrieved.items()
        },
        "material": material.model_dump(mode="json"),
        "html": render_html(material, store),
    }


def build_samples() -> list[dict]:
    store = InMemoryKnowledgeStore.from_json()
    return [build_sample(p, store) for p in sorted(FIXTURES.glob("*.json"))]


def build_page(samples: list[dict], standalone: bool = True) -> str:
    data = {
        "samples": samples,
        "topic_titles": {t.value: title for t, title in TOPIC_TITLES.items()},
        "trigger_topics": {t.value: [x.value for x in ts] for t, ts in TRIGGER_TOPICS.items()},
        "note_source_id": NOTE_SOURCE_ID,
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    body = TEMPLATE.read_text(encoding="utf-8").replace(DATA_PLACEHOLDER, payload)
    if not standalone:  # the Artifact publisher adds its own document skeleton
        return body
    return (
        '<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"</head>\n<body>\n{body}</body>\n</html>\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fragment", type=Path, help="also write a copy without <html>/<head>")
    args = parser.parse_args()

    samples = build_samples()
    OUTPUT.write_text(build_page(samples), encoding="utf-8")
    for s in samples:
        items = sum(len(sec["items"]) for sec in s["material"]["sections"])
        print(f"  {s['id']}: {s['title']} — {items} items, 0 warnings")
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    if args.fragment:
        args.fragment.write_text(build_page(samples, standalone=False), encoding="utf-8")
        print(f"wrote {args.fragment}")


if __name__ == "__main__":
    main()
