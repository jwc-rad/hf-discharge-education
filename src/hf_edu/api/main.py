"""FastAPI app. Run: uvicorn hf_edu.api.main:app --reload"""
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from hf_edu import __version__
from hf_edu.config import Settings, get_settings
from hf_edu.kb import InMemoryKnowledgeStore, KnowledgeStore
from hf_edu.llm import LLMClient, LLMError, build_client
from hf_edu.pipeline import PipelineResult, run_pipeline
from hf_edu.pipeline.extract import extract_context
from hf_edu.render import render_html
from hf_edu.schemas import ClinicalContext, DischargeNote

app = FastAPI(title="HF discharge education", version=__version__)


@lru_cache
def get_llm() -> LLMClient:
    return build_client(get_settings())


@lru_cache
def get_store() -> KnowledgeStore:
    # TODO: swap for the real DB backend once data/raw/ ingestion exists.
    return InMemoryKnowledgeStore.from_json()


LLM = Annotated[LLMClient, Depends(get_llm)]
Store = Annotated[KnowledgeStore, Depends(get_store)]
Config = Annotated[Settings, Depends(get_settings)]


def _run(note: DischargeNote, llm: LLMClient, store: KnowledgeStore, settings: Settings) -> PipelineResult:
    try:
        return run_pipeline(note, llm, store, top_k=settings.retrieval_top_k)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/llm/status")
def llm_status(llm: LLM) -> dict:
    return llm.status()


@app.post("/v1/extract", response_model=ClinicalContext)
def extract(note: DischargeNote, llm: LLM) -> ClinicalContext:
    try:
        return extract_context(note, llm)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/v1/education", response_model=PipelineResult)
def education(note: DischargeNote, llm: LLM, store: Store, settings: Config) -> PipelineResult:
    return _run(note, llm, store, settings)


@app.post("/v1/education/html", response_class=HTMLResponse)
def education_html(note: DischargeNote, llm: LLM, store: Store, settings: Config) -> str:
    return render_html(_run(note, llm, store, settings).material, store)
