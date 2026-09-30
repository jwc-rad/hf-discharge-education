"""Wires the three steps: extract -> retrieve -> generate."""
from pydantic import BaseModel

from hf_edu.kb import KnowledgeStore
from hf_edu.llm import LLMClient
from hf_edu.pipeline.extract import extract_context
from hf_edu.pipeline.generate import generate_material
from hf_edu.pipeline.retrieve import build_queries, retrieve
from hf_edu.schemas import ClinicalContext, DischargeNote, EducationMaterial, Topic


class PipelineResult(BaseModel):
    context: ClinicalContext
    retrieved_chunk_ids: dict[Topic, list[str]]
    material: EducationMaterial


def run_pipeline(
    note: DischargeNote, llm: LLMClient, store: KnowledgeStore, top_k: int = 3
) -> PipelineResult:
    context = extract_context(note, llm)
    retrieved = retrieve(store, build_queries(context, top_k))
    material = generate_material(context, retrieved, llm)
    return PipelineResult(
        context=context,
        retrieved_chunk_ids={t: [h.chunk.chunk_id for h in hits] for t, hits in retrieved.items()},
        material=material,
    )
