# HF Discharge Education (심부전 퇴원 교육자료 생성)

> 2026-2 서울대학교 **「디지털 헬스케어 데이터의 이해와 실습」** 6팀 팀 프로젝트

**심부전** 환자를 위한 AI 기반 환자 친화적 퇴원 교육자료 생성 프로젝트.
퇴원 기록지를 입력하면, 가이드라인·교육자료로 구성된 지식 베이스(KB)에서 근거를 검색하고
구조화된 한국어 교육자료(식이 / 재활 / 복약 / 주의사항)를 생성하여 HTML로 보여준다.

> 연구용 프로토타입이다. 출력물은 **의료진 검토용 초안**이며 임상적 조언이 아니다.
> 환자 데이터(MIMIC 노트, EHR 추출본)나 원본 PDF는 절대 커밋하지 않는다.

```
퇴원 기록지 ──▶ ① 추출 (LLM) ──▶ ② 검색 (KB) ──▶ ③ 생성 (LLM) ──▶ ④ HTML
                 ClinicalContext    RetrievedChunk[]   EducationMaterial
```

설계는 [docs/architecture.md](docs/architecture.md), DB ↔ LLM 규칙은
[docs/db_contract.md](docs/db_contract.md) 참고.

## 빠른 시작

**conda + pip**만 사용한다 (배포 워크스테이션에서 허용되는 도구).

```bash
conda env create -f environment.yml      # `hf-edu` 환경 생성, requirements + 본 패키지 pip 설치
conda activate hf-edu
cp .env.example .env

pytest -q                                # GPU / LLM 불필요 (fake LLM 사용)
```

pull 후 기존 환경 업데이트: `pip install -r requirements.txt -r requirements-dev.txt -e .`

### API 실행

```bash
# GPU 없이 (미리 준비된 데모 응답):
LLM_FAKE=1 uvicorn hf_edu.api.main:app --reload

# 실제 모델 사용: 먼저 로컬 vLLM 실행 (docs/local_llm.md), 그 다음
uvicorn hf_edu.api.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs (vLLM이 이미 8000 포트를 쓰고 있으면 uvicorn에 `--port 8080` 지정)
- 예시:

```bash
python - <<'PY' > /tmp/note.json
import json; print(json.dumps({"text": open("data/samples/discharge_note_synthetic_01.txt").read()}))
PY
curl -s -X POST localhost:8080/v1/education/html -H 'Content-Type: application/json' \
     -d @/tmp/note.json > education.html
```

| Endpoint | 입력 → 출력 |
|---|---|
| `GET /health` | 서버 상태 확인 |
| `GET /llm/status` | 설정된 endpoint, 서빙 중인 모델 |
| `POST /v1/extract` | `DischargeNote` → `ClinicalContext` |
| `POST /v1/education` | `DischargeNote` → `{context, retrieved_chunk_ids, material}` |
| `POST /v1/education/html` | `DischargeNote` → `text/html` |

## 데모 (LLM·설치 불필요)

브라우저에서 `demo/index.html`을 연다. 합성 퇴원 기록지 3개 중 하나를 골라
추출 → 검색 → 생성 → 최종 환자용 HTML 단계를 차례로 확인할 수 있다. LLM 출력은 사람이 직접 작성한
fixture(`demo/fixtures/`)이고, 검색·인용 검증·HTML 렌더링은 실제 코드를 사용한다.

pipeline, 템플릿, KB seed, fixture를 변경한 뒤에는 다시 생성한다 (fixture가 pipeline과 더 이상
맞지 않으면 실패함): `python demo/build_demo.py`

`main` 브랜치에서 `demo/index.html`이 변경되면(또는 수동 실행 시) `.github/workflows/pages.yml`이
GitHub Pages에 배포한다. 최초 1회 설정: Settings → Pages → Source: **GitHub Actions**.
repo가 private이어도 페이지는 공개된다 (private repo Pages는 유료 플랜 필요).

## LLM 설정

| | `LLM_BASE_URL` |
|---|---|
| 개발 (로컬 vLLM) | `http://localhost:8000/v1` |
| 배포 | `https://llm.snuh.org/llm` |

세부 설정, 모델 선택, SNUH 체크리스트: [docs/local_llm.md](docs/local_llm.md).

## 저장소 구조

```
data/raw/            Shared Drive의 RAG 원본 PDF (git-ignored; data/raw/README.md 참고)
data/processed/      향후 구조화된 chunk 저장 위치 (git-ignored)
data/samples/        개발용 합성 퇴원 기록지
docs/                아키텍처, DB 계약, LLM 설정
scripts/             serve_vllm.sh, smoke_llm.py
src/hf_edu/
  config.py          환경변수 기반 설정
  schemas/           Pydantic 모델: note, knowledge (DB), education (출력)
  llm/               OpenAI 호환 client + fake client
  kb/                KnowledgeStore protocol, dummy store + seed 데이터, ingestion stub
  pipeline/          extract → retrieve → generate, 프롬프트
  render/            Jinja2 HTML 템플릿
  api/               FastAPI 앱
tests/
```

## 팀별 시작 지점

- **DB/RAG:** `docs/db_contract.md`에 따라 `kb/ingest.py`와 실제 `KnowledgeStore`를 구현한다.
  `api/main.py:get_store`에서 교체한다.
- **임상팀:** 주제(topic)와 `TriggerCode`(`schemas/common.py`) 검토, chunk 태깅, 프롬프트 검토
  (`pipeline/prompts.py`).
- **생성:** 실제 MIMIC 노트로 프롬프트 개선. 반드시 승인된 연구 환경에서만 진행하며, 노트는 절대
  이 repo에 들어오지 않는다.
- **프론트엔드/HTML:** `render/templates/education.html.j2`.
- **평가:** 미착수 (누락 / 근거 일치 / 가독성; 1차 평가 10월말).
