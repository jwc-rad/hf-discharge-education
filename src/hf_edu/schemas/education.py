"""Output schema: structured education material (rendered to HTML later)."""
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from hf_edu.schemas.common import Topic, TriggerCode


class EducationItem(BaseModel):
    text: str = Field(description="환자용 쉬운 한국어 실천 문장")
    why: str | None = Field(None, description="이유 한 문장 (선택)")
    source_ids: list[str] = Field(description="근거 chunk_id / NOTE 인용 ID")


class EducationSection(BaseModel):
    topic: Topic
    title: str
    items: list[EducationItem]
    clinician_consult: bool = Field(False, description="의료진 상담 필요 안내 표시")
    triggers_applied: list[TriggerCode] = Field(default_factory=list)


class DraftSection(BaseModel):
    topic: Topic
    items: list[EducationItem]


class EducationDraft(BaseModel):
    """What the LLM returns (step 3). Title, triggers and consult flag are set by code, not the LLM."""

    sections: list[DraftSection]


class EducationMaterial(BaseModel):
    sections: list[EducationSection]
    model: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    warnings: list[str] = Field(default_factory=list)
    reviewed_by_clinician: bool = False
