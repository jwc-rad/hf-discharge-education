"""Minimal OpenAI-compatible chat client returning validated Pydantic objects.

Dev: local vLLM (`http://localhost:8000/v1`). Deployment: `https://llm.snuh.org/llm`.
Only the chat-completions and models endpoints are used, so any OpenAI-compatible server works.
"""
import json
from collections.abc import Callable
from typing import Protocol, TypeVar

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError

from hf_edu.config import Settings

T = TypeVar("T", bound=BaseModel)
Message = dict[str, str]


class LLMError(RuntimeError):
    pass


class LLMClient(Protocol):
    model: str

    def chat_json(self, messages: list[Message], schema: type[T], json_schema: dict | None = None) -> T:
        """`json_schema` optionally overrides the schema sent to the server (e.g. a per-request
        enum of allowed IDs); the result is always validated against the Pydantic `schema`."""
        ...

    def status(self) -> dict: ...


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


class OpenAICompatibleClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.llm_model
        self._client = OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key or "EMPTY",
            timeout=settings.llm_timeout,
            max_retries=1,
        )

    def _response_format(self, schema: type[BaseModel], json_schema: dict | None) -> dict | None:
        mode = self.settings.llm_structured_output
        if mode == "json_schema":
            return {
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "schema": json_schema or schema.model_json_schema()},
            }
        if mode == "json_object":
            return {"type": "json_object"}
        return None

    def _complete(
        self, messages: list[Message], schema: type[BaseModel], json_schema: dict | None
    ) -> str:
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": self.settings.llm_temperature,
            "max_tokens": self.settings.llm_max_tokens,
        }
        if self.settings.llm_seed is not None:
            kwargs["seed"] = self.settings.llm_seed
        if (fmt := self._response_format(schema, json_schema)) is not None:
            kwargs["response_format"] = fmt
        if self.settings.llm_extra_body:
            kwargs["extra_body"] = self.settings.llm_extra_body
        try:
            resp = self._client.chat.completions.create(**kwargs)
        except OpenAIError as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc
        return resp.choices[0].message.content or ""

    def chat_json(self, messages: list[Message], schema: type[T], json_schema: dict | None = None) -> T:
        """Call the model and validate against `schema`; retry once with the validation error."""
        if self.settings.llm_structured_output != "json_schema":
            schema_hint = json.dumps(json_schema or schema.model_json_schema(), ensure_ascii=False)
            messages = [*messages, {"role": "user", "content": f"JSON schema:\n{schema_hint}"}]
        raw = self._complete(messages, schema, json_schema)
        try:
            return schema.model_validate_json(_strip_fences(raw))
        except ValidationError as exc:
            retry = [
                *messages,
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"Invalid JSON for the schema. Fix and return JSON only.\n{exc}"},
            ]
            raw = self._complete(retry, schema, json_schema)
            try:
                return schema.model_validate_json(_strip_fences(raw))
            except ValidationError as exc2:
                raise LLMError(f"LLM output failed schema {schema.__name__}: {exc2}") from exc2

    def status(self) -> dict:
        out = {"base_url": self.settings.llm_base_url, "model": self.model}
        try:
            served = [m.id for m in self._client.models.list().data]
            out.update(status="ready" if self.model in served else "model_missing", served_models=served)
        except OpenAIError as exc:
            out.update(status="offline", error=str(exc))
        return out


class FakeLLMClient:
    """Deterministic stand-in for tests and GPU-free demos.

    `responder(messages, schema)` returns a schema instance or a dict/JSON string.
    """

    def __init__(self, responder: Callable[[list[Message], type[BaseModel]], object], model: str = "fake-llm"):
        self.responder = responder
        self.model = model
        self.calls: list[tuple[list[Message], type[BaseModel], dict | None]] = []

    def chat_json(self, messages: list[Message], schema: type[T], json_schema: dict | None = None) -> T:
        self.calls.append((messages, schema, json_schema))
        out = self.responder(messages, schema)
        if isinstance(out, schema):
            return out
        if isinstance(out, str):
            return schema.model_validate_json(out)
        return schema.model_validate(out)

    def status(self) -> dict:
        return {"base_url": None, "model": self.model, "status": "fake"}


def build_client(settings: Settings) -> LLMClient:
    if settings.llm_fake:
        from hf_edu.llm.fake_responses import demo_responder

        return FakeLLMClient(demo_responder)
    return OpenAICompatibleClient(settings)
