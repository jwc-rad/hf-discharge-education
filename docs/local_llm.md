# LLM endpoints: local vLLM (dev) and SNUH (deployment)

The app only talks to an **OpenAI-compatible** chat-completions API through the `openai` SDK
(`src/hf_edu/llm/client.py`). Switching environments = editing `.env`.

| | Dev | Deployment |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:8000/v1` | `https://llm.snuh.org/llm` |
| `LLM_MODEL` | `local-llm` (vLLM `--served-model-name`) | model name served by SNUH (TBD) |
| `LLM_API_KEY` | `EMPTY` | issued key (never commit) |
| `LLM_STRUCTURED_OUTPUT` | `json_schema` | `json_schema` if supported, else `json_object` |

## Local vLLM

vLLM pins its own torch/CUDA, so it lives in a **separate conda env** from the app:

```bash
conda create -n hf-edu-vllm python=3.12 pip -y
conda activate hf-edu-vllm
pip install vllm

# Default: Qwen/Qwen3-8B (≈16 GB bf16, fits a 24 GB GPU). Override with VLLM_MODEL.
./scripts/serve_vllm.sh
# e.g. smaller GPU:  VLLM_MODEL=Qwen/Qwen3-4B ./scripts/serve_vllm.sh
```

The first run downloads the weights from Hugging Face (`~/.cache/huggingface`). Then, in the app env:

```bash
conda activate hf-edu
cp .env.example .env            # defaults already point to localhost:8000
python scripts/smoke_llm.py     # lists served models + one structured JSON call
```

Notes
- **Model choice:** prefer the same family as the SNUH-served model once known, so prompts transfer.
  The 09-23 MVP used Qwen3.5 9B via Ollama.
- **Qwen3 thinking mode:** keep `LLM_EXTRA_BODY={"chat_template_kwargs": {"enable_thinking": false}}`
  so the model returns plain JSON. Remove it for models without that chat-template option.
- **Structured output:** vLLM enforces `response_format: json_schema` with guided decoding, so
  schema-invalid output is rare; the client still validates with Pydantic and retries once.
- **FlashInfer build error** (`nvcc fatal : Unknown option '--compress-mode=size'` / `Ninja build failed`):
  the host CUDA toolkit is older than FlashInfer expects. `serve_vllm.sh` sets
  `VLLM_USE_FLASHINFER_SAMPLER=0` by default (PyTorch sampling) to avoid it. Tested with vLLM 0.30.0,
  host nvcc 11.8, driver CUDA 13.0 and an RTX 4090.
- No GPU? Set `LLM_FAKE=1` to run the API with a canned responder (demo/tests only).

## SNUH endpoint (`https://llm.snuh.org/llm`)

Before the first deployment run, confirm with `python scripts/smoke_llm.py`:
1. **Path:** the SDK appends `/chat/completions` and `/models` to `LLM_BASE_URL`. If the gateway expects
   `/llm/v1/...`, set `LLM_BASE_URL=https://llm.snuh.org/llm/v1`.
2. **Model name:** from the `served_models` list printed by the smoke test.
3. **`response_format`:** if `json_schema` is rejected, use `json_object` (or `none`); the schema is then
   added to the prompt and Pydantic validation still applies.
4. **Auth / network:** API key header and whether the deployment workstation needs a proxy.
