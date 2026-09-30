"""Check the configured LLM endpoint (reads .env): list models, then one structured JSON call.

    python scripts/smoke_llm.py
"""
import sys

from pydantic import BaseModel

from hf_edu.config import get_settings
from hf_edu.llm import LLMError, OpenAICompatibleClient


class Ping(BaseModel):
    answer: str
    ok: bool


def main() -> int:
    settings = get_settings()
    client = OpenAICompatibleClient(settings)
    status = client.status()
    print("status:", status)
    if status["status"] == "offline":
        print("Endpoint unreachable. Check LLM_BASE_URL (does it need a /v1 suffix?).")
        return 1
    try:
        out = client.chat_json(
            [{"role": "user", "content": '심부전이 무엇인지 한 문장으로 답하고 ok=true로 JSON을 반환하세요.'}],
            Ping,
        )
    except LLMError as exc:
        print("chat_json failed:", exc)
        print("If the server rejects json_schema, try LLM_STRUCTURED_OUTPUT=json_object.")
        return 1
    print("chat_json:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
