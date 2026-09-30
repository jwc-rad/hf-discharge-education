"""Step 3: context + retrieved chunks -> EducationMaterial, with citation validation."""
import json

from hf_edu.llm import LLMClient
from hf_edu.pipeline.prompts import GENERATE_SYSTEM
from hf_edu.pipeline.retrieve import triggers_for_topic
from hf_edu.schemas import (
    TOPIC_TITLES,
    ClinicalContext,
    DraftSection,
    EducationDraft,
    EducationMaterial,
    EducationSection,
    RetrievedChunk,
    Topic,
)

NOTE_SOURCE_ID = "NOTE"  # cites the discharge note (ClinicalContext) itself


def build_payload(context: ClinicalContext, retrieved: dict[Topic, list[RetrievedChunk]]) -> dict:
    return {
        "clinical_context": context.model_dump(mode="json"),
        "topics": [
            {
                "topic": topic.value,
                "title": TOPIC_TITLES[topic],
                "triggers_applied": [t.value for t in triggers_for_topic(context, topic)],
                "sources": [{"id": h.chunk.chunk_id, "text": h.chunk.text} for h in hits],
            }
            for topic, hits in retrieved.items()
        ],
    }


def allowed_ids(retrieved: dict[Topic, list[RetrievedChunk]]) -> dict[Topic, set[str]]:
    return {t: {h.chunk.chunk_id for h in hits} | {NOTE_SOURCE_ID} for t, hits in retrieved.items()}


def draft_json_schema(retrieved: dict[Topic, list[RetrievedChunk]]) -> dict:
    """EducationDraft schema narrowed for this request (sent to the server for guided decoding).

    One section per requested topic; each topic's `source_ids` is an enum of the IDs retrieved
    for that topic, so the model cannot cite anything else. Mirrors the MVP's per-topic enum.
    """
    allowed = allowed_ids(retrieved)
    variants = [
        {
            "type": "object",
            "properties": {
                "topic": {"const": topic.value},
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 5,
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "why": {"type": ["string", "null"]},
                            "source_ids": {
                                "type": "array",
                                "minItems": 1,
                                "items": {"enum": sorted(allowed[topic])},
                            },
                        },
                        "required": ["text", "why", "source_ids"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["topic", "items"],
            "additionalProperties": False,
        }
        for topic in retrieved
    ]
    return {
        "type": "object",
        "properties": {
            "sections": {
                "type": "array",
                "prefixItems": variants,
                "items": False,
                "minItems": len(variants),
                "maxItems": len(variants),
            }
        },
        "required": ["sections"],
        "additionalProperties": False,
    }


def citation_errors(draft: EducationDraft, allowed: dict[Topic, set[str]]) -> list[str]:
    errors = []
    for section in draft.sections:
        ok = allowed.get(section.topic, set())
        for n, item in enumerate(section.items):
            bad = [i for i in item.source_ids if i not in ok]
            if bad:
                errors.append(f"{section.topic.value} item {n}: unknown source_ids {bad}")
            if not item.source_ids:
                errors.append(f"{section.topic.value} item {n}: empty source_ids")
    return errors


def _finalize(
    draft: EducationDraft,
    context: ClinicalContext,
    retrieved: dict[Topic, list[RetrievedChunk]],
    warnings: list[str],
) -> list[EducationSection]:
    allowed = allowed_ids(retrieved)
    by_topic: dict[Topic, DraftSection] = {}
    for s in draft.sections:
        if s.topic not in retrieved:
            warnings.append(f"dropped section for unrequested topic {s.topic.value}")
        elif s.topic in by_topic:
            warnings.append(f"duplicate section {s.topic.value}; kept the first")
        else:
            by_topic[s.topic] = s
    sections = []
    for topic in retrieved:  # preserve requested order
        draft_section = by_topic.get(topic)
        if draft_section is None:
            warnings.append(f"missing section {topic.value}")
            continue
        items = []
        for item in draft_section.items:
            valid = [i for i in dict.fromkeys(item.source_ids) if i in allowed[topic]]
            if not valid:
                warnings.append(f"dropped uncited item in {topic.value}: {item.text[:40]}")
                continue
            items.append(item.model_copy(update={"source_ids": valid}))
        triggers = triggers_for_topic(context, topic)
        sections.append(
            EducationSection(
                topic=topic,
                title=TOPIC_TITLES[topic],
                items=items,
                triggers_applied=triggers,
                clinician_consult=bool(triggers),
            )
        )
    return sections


def generate_material(
    context: ClinicalContext, retrieved: dict[Topic, list[RetrievedChunk]], llm: LLMClient
) -> EducationMaterial:
    messages = [
        {"role": "system", "content": GENERATE_SYSTEM},
        {"role": "user", "content": json.dumps(build_payload(context, retrieved), ensure_ascii=False)},
    ]
    json_schema = draft_json_schema(retrieved)
    draft = llm.chat_json(messages, EducationDraft, json_schema)
    warnings: list[str] = []
    errors = citation_errors(draft, allowed_ids(retrieved))
    if errors:  # contract rule 4: retry once with feedback, then strip + warn
        feedback = (
            "source_ids 오류를 고쳐, 모든 topic의 sections를 빠짐없이 포함한 전체 JSON을 다시 반환하세요:\n"
            + "\n".join(errors)
        )
        messages += [
            {"role": "assistant", "content": draft.model_dump_json()},
            {"role": "user", "content": feedback},
        ]
        draft = llm.chat_json(messages, EducationDraft, json_schema)
        warnings += [f"citation retry: {e}" for e in citation_errors(draft, allowed_ids(retrieved))]
    sections = _finalize(draft, context, retrieved, warnings)
    return EducationMaterial(sections=sections, model=llm.model, warnings=warnings)
