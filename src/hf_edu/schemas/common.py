"""Enums shared between the note, knowledge-base and education schemas."""
from enum import Enum


class Topic(str, Enum):
    """Education topics from the 09-30 algorithm schema (식이 / 재활 / 복약 / 주의사항)."""

    DIET = "diet"  # 식이
    ACTIVITY = "activity"  # 활동·재활
    MEDICATION = "medication"  # 복약
    SYMPTOM_ACTION = "symptom_action"  # 주의사항: 증상악화 대처법 (체중 모니터링 포함)
    FOLLOWUP = "followup"  # 외래 (optional; data often unusable in practice)


CORE_TOPICS: tuple[Topic, ...] = (
    Topic.DIET,
    Topic.ACTIVITY,
    Topic.MEDICATION,
    Topic.SYMPTOM_ACTION,
)

TOPIC_TITLES: dict[Topic, str] = {
    Topic.DIET: "식사: 무엇을 어떻게 드실까요",
    Topic.ACTIVITY: "활동과 재활",
    Topic.MEDICATION: "약 복용",
    Topic.SYMPTOM_ACTION: "이럴 때는 연락하세요: 증상 악화 대처법",
    Topic.FOLLOWUP: "다음 진료",
}


class TriggerCode(str, Enum):
    """Personalization triggers extracted from the note (09-30: e.g. 고칼륨혈증).

    A present trigger switches trigger-specific education chunks on and may
    require a "consult your clinician" notice. Extend together with the KB tags.
    """

    HYPERKALEMIA = "hyperkalemia"
    HYPOKALEMIA = "hypokalemia"
    HYPONATREMIA = "hyponatremia"
    CKD = "ckd"
    DIABETES = "diabetes"
    FLUID_RESTRICTION = "fluid_restriction"
    WARFARIN = "warfarin"
    ICD_OR_PACEMAKER = "icd_or_pacemaker"


# Which topics a trigger personalizes. Deterministic (set by the orchestrator, not the LLM):
# a section whose topic has an active trigger gets `triggers_applied` and a clinician-consult notice.
TRIGGER_TOPICS: dict[TriggerCode, tuple[Topic, ...]] = {
    TriggerCode.HYPERKALEMIA: (Topic.DIET, Topic.MEDICATION),
    TriggerCode.HYPOKALEMIA: (Topic.DIET, Topic.MEDICATION),
    TriggerCode.HYPONATREMIA: (Topic.DIET,),
    TriggerCode.CKD: (Topic.DIET, Topic.MEDICATION),
    TriggerCode.DIABETES: (Topic.DIET,),
    TriggerCode.FLUID_RESTRICTION: (Topic.DIET,),
    TriggerCode.WARFARIN: (Topic.MEDICATION, Topic.DIET),
    TriggerCode.ICD_OR_PACEMAKER: (Topic.ACTIVITY, Topic.SYMPTOM_ACTION),
}
