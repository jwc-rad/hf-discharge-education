"""Canned responder for LLM_FAKE=1 (demo without a GPU) and tests.

Extraction: returns a fixed context (matches data/samples/discharge_note_synthetic_01.txt).
Generation: echoes the first sentence of each provided source, so citations are always valid.
"""
import json

from pydantic import BaseModel

from hf_edu.schemas import ClinicalContext, EducationDraft

DEMO_CONTEXT = {
    "hf_type": "HFrEF",
    "ef_percent": 30,
    "discharge_weight_kg": 68.2,
    "discharge_medications": [
        {"name": "Furosemide", "dose": "40 mg", "frequency": "daily", "change": "changed",
         "evidence": "Furosemide 40 mg PO daily"},
        {"name": "Sacubitril-valsartan", "dose": "24-26 mg", "frequency": "BID", "change": "new",
         "evidence": "Sacubitril-valsartan 24-26 mg PO BID"},
    ],
    "diet_instructions": [{"text": "2 g sodium diet", "evidence": "2 g sodium diet"}],
    "activity_instructions": [{"text": "Walk as tolerated", "evidence": "Activity: walk as tolerated"}],
    "followup": [{"text": "Cardiology clinic in 1 week", "evidence": "Cardiology clinic in 1 week"}],
    "triggers": [
        {"code": "hyperkalemia", "present": True, "evidence": "Lisinopril was stopped due to\nhyperkalemia"},
        {"code": "fluid_restriction", "present": True, "evidence": "fluid restriction 1.5 L/day"},
    ],
}


def demo_responder(messages: list[dict], schema: type[BaseModel]) -> object:
    if schema is ClinicalContext:
        return DEMO_CONTEXT
    if schema is EducationDraft:
        payload = json.loads(messages[1]["content"])
        return {
            "sections": [
                {
                    "topic": t["topic"],
                    "items": [
                        {"text": s["text"], "why": None, "source_ids": [s["id"]]}
                        for s in t["sources"]
                    ],
                }
                for t in payload["topics"]
            ]
        }
    raise ValueError(f"no fake response for {schema.__name__}")
