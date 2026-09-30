#!/usr/bin/env bash
# Start a local OpenAI-compatible vLLM server for development.
# Run inside the separate `hf-edu-vllm` conda env (see docs/local_llm.md).
set -euo pipefail

VLLM_MODEL="${VLLM_MODEL:-Qwen/Qwen3-8B}"
VLLM_PORT="${VLLM_PORT:-8000}"
VLLM_SERVED_NAME="${VLLM_SERVED_NAME:-local-llm}"   # must equal LLM_MODEL in .env
VLLM_MAX_LEN="${VLLM_MAX_LEN:-16384}"
VLLM_GPU_UTIL="${VLLM_GPU_UTIL:-0.85}"
# FlashInfer JIT-compiles its sampler with the system nvcc; an old host CUDA toolkit
# (e.g. 11.8) fails with "Unknown option '--compress-mode=size'". Use PyTorch sampling
# by default; set to 1 on hosts with a recent CUDA toolkit.
export VLLM_USE_FLASHINFER_SAMPLER="${VLLM_USE_FLASHINFER_SAMPLER:-0}"

exec vllm serve "$VLLM_MODEL" \
  --host 127.0.0.1 \
  --port "$VLLM_PORT" \
  --served-model-name "$VLLM_SERVED_NAME" \
  --max-model-len "$VLLM_MAX_LEN" \
  --gpu-memory-utilization "$VLLM_GPU_UTIL" \
  "$@"
