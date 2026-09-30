"""Input (discharge note) and extraction output (ClinicalContext)."""
from typing import Literal

from pydantic import BaseModel, Field

from hf_edu.schemas.common import TriggerCode


class DischargeNote(BaseModel):
    """Raw discharge note text (MIMIC-Note style).

    Identifiers such as subject_id / hadm_id must stay with the caller and are never sent
    to the LLM. `note_id` is an opaque caller-side reference only.
    """

    note_id: str | None = None
    text: str = Field(min_length=20, max_length=60_000)
    language: Literal["en", "ko"] = "en"


class Evidenced(BaseModel):
    """Every extracted item keeps the verbatim span it came from, for clinician tracing."""

    evidence: str = Field(description="Verbatim span copied from the note")


# Fields below are required-but-nullable (no defaults) on purpose: with guided decoding
# (json_schema), optional fields are often skipped by the model. Required forces an explicit
# value or null.


class Medication(Evidenced):
    name: str
    dose: str | None
    frequency: str | None
    change: Literal["new", "changed", "continued", "stopped", "unknown"]


class Instruction(Evidenced):
    text: str


class Trigger(BaseModel):
    code: TriggerCode
    present: bool | None = Field(description="true / false / null (not mentioned)")
    evidence: str | None = Field(description="Verbatim span from the note; null if not mentioned")


class ClinicalContext(BaseModel):
    """Structured facts extracted from the note. Output of pipeline step 1."""

    hf_type: Literal["HFrEF", "HFmrEF", "HFpEF", "unknown"]
    ef_percent: float | None
    discharge_weight_kg: float | None
    discharge_medications: list[Medication]
    diet_instructions: list[Instruction]
    activity_instructions: list[Instruction]
    followup: list[Instruction]
    triggers: list[Trigger]

    def active_triggers(self) -> list[TriggerCode]:
        return [t.code for t in self.triggers if t.present]
