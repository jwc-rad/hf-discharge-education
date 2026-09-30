from pathlib import Path

import pytest

from hf_edu.kb import InMemoryKnowledgeStore
from hf_edu.llm import FakeLLMClient
from hf_edu.llm.fake_responses import demo_responder
from hf_edu.schemas import DischargeNote

SAMPLE = Path(__file__).resolve().parents[1] / "data/samples/discharge_note_synthetic_01.txt"


@pytest.fixture
def store() -> InMemoryKnowledgeStore:
    return InMemoryKnowledgeStore.from_json()


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    return FakeLLMClient(demo_responder)


@pytest.fixture
def note() -> DischargeNote:
    return DischargeNote(text=SAMPLE.read_text(encoding="utf-8"))
