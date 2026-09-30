"""Step 1: discharge note -> ClinicalContext."""
import json

from hf_edu.llm import LLMClient
from hf_edu.pipeline.prompts import EXTRACT_SYSTEM
from hf_edu.schemas import ClinicalContext, DischargeNote, TriggerCode


def extract_context(note: DischargeNote, llm: LLMClient) -> ClinicalContext:
    payload = {"trigger_codes": [t.value for t in TriggerCode], "note": note.text}
    messages = [
        {"role": "system", "content": EXTRACT_SYSTEM},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    return llm.chat_json(messages, ClinicalContext)
