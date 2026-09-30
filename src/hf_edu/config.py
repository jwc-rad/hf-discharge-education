"""Runtime settings. Everything comes from environment variables / `.env`.

Dev (local vLLM) and deployment (https://llm.snuh.org/llm) differ only by `.env`.
"""
from functools import lru_cache
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI-compatible endpoint. Used verbatim as the SDK base_url
    # (the SDK appends /chat/completions, /models, ...).
    llm_base_url: str = "http://localhost:8000/v1"
    llm_api_key: str = "EMPTY"
    llm_model: str = "local-llm"
    llm_structured_output: Literal["json_schema", "json_object", "none"] = "json_schema"
    llm_temperature: float = 0.0
    llm_seed: int | None = 20260930
    llm_max_tokens: int = 3000
    llm_timeout: float = 300.0
    llm_extra_body: dict[str, Any] = Field(default_factory=dict)
    llm_fake: bool = False

    retrieval_top_k: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
