# LLM endpoint: 로컬 vLLM (개발) 및 SNUH (배포)

앱은 `openai` SDK(`src/hf_edu/llm/client.py`)를 통해 **OpenAI 호환** chat-completions API와만
통신한다. 환경 전환 = `.env` 수정.

| | 개발 | 배포 |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:8000/v1` | `https://llm.snuh.org/llm` |
| `LLM_MODEL` | `local-llm` (vLLM `--served-model-name`) | SNUH에서 서빙하는 모델 이름 (미정) |
| `LLM_API_KEY` | `EMPTY` | 발급받은 키 (절대 커밋 금지) |
| `LLM_STRUCTURED_OUTPUT` | `json_schema` | 지원되면 `json_schema`, 아니면 `json_object` |

## 로컬 vLLM

vLLM은 자체적으로 torch/CUDA 버전을 고정하므로, 앱과 **별도의 conda 환경**에 설치한다:

```bash
conda create -n hf-edu-vllm python=3.12 pip -y
conda activate hf-edu-vllm
pip install vllm

# 기본값: Qwen/Qwen3-8B (bf16 기준 ≈16 GB, 24 GB GPU에 들어감). VLLM_MODEL로 변경 가능.
./scripts/serve_vllm.sh
# 예: 더 작은 GPU:  VLLM_MODEL=Qwen/Qwen3-4B ./scripts/serve_vllm.sh
```

첫 실행 시 Hugging Face에서 가중치를 내려받는다 (`~/.cache/huggingface`). 그 다음 앱 환경에서:

```bash
conda activate hf-edu
cp .env.example .env            # 기본값이 이미 localhost:8000을 가리킴
python scripts/smoke_llm.py     # 서빙 중인 모델 목록 + 구조화 JSON 호출 1회
```

참고
- **모델 선택:** SNUH에서 서빙하는 모델이 정해지면 프롬프트가 그대로 옮겨지도록 같은 계열을 우선한다.
  09-23 MVP는 Ollama로 Qwen3.5 9B를 사용했다.
- **Qwen3 thinking 모드:** 모델이 순수 JSON을 반환하도록
  `LLM_EXTRA_BODY={"chat_template_kwargs": {"enable_thinking": false}}`를 유지한다. 해당
  chat-template 옵션이 없는 모델에서는 제거한다.
- **구조화 출력:** vLLM은 guided decoding으로 `response_format: json_schema`를 강제하므로 스키마에
  맞지 않는 출력은 드물다. 그래도 client가 Pydantic으로 검증하고 1회 재시도한다.
- **FlashInfer 빌드 오류** (`nvcc fatal : Unknown option '--compress-mode=size'` / `Ninja build failed`):
  호스트 CUDA toolkit이 FlashInfer가 기대하는 버전보다 오래된 경우다. `serve_vllm.sh`는 이를 피하기 위해
  기본으로 `VLLM_USE_FLASHINFER_SAMPLER=0`(PyTorch sampling)을 설정한다. vLLM 0.30.0,
  호스트 nvcc 11.8, 드라이버 CUDA 13.0, RTX 4090에서 테스트함.
- GPU가 없다면? `LLM_FAKE=1`로 설정하면 미리 준비된 응답으로 API가 동작한다 (데모/테스트 전용).

## SNUH endpoint (`https://llm.snuh.org/llm`)

첫 배포 실행 전에 `python scripts/smoke_llm.py`로 다음을 확인한다:
1. **경로:** SDK는 `LLM_BASE_URL` 뒤에 `/chat/completions`와 `/models`를 붙인다. gateway가
   `/llm/v1/...` 형태를 기대하면 `LLM_BASE_URL=https://llm.snuh.org/llm/v1`로 설정한다.
2. **모델 이름:** smoke test가 출력하는 `served_models` 목록에서 확인한다.
3. **`response_format`:** `json_schema`가 거부되면 `json_object`(또는 `none`)를 사용한다. 이 경우
   스키마가 프롬프트에 추가되며 Pydantic 검증은 그대로 적용된다.
4. **인증 / 네트워크:** API 키 헤더 형식, 그리고 배포 워크스테이션에 프록시가 필요한지 여부.
