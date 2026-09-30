# 기술/엔지니어링 파트 계획

설계와 규칙은 [docs/architecture.md](../docs/architecture.md), [docs/db_contract.md](../docs/db_contract.md),
[docs/local_llm.md](../docs/local_llm.md) 참고. 의료진 파트 계획은 [clinical.md](clinical.md).

## 완료

- [x] repo 구성: 스키마, extract → retrieve → generate pipeline, FastAPI, 테스트 (fake LLM)
- [x] dummy KB (`kb/dummy.py`, `seed_chunks.json`) 및 DB ↔ LLM 계약 문서
- [x] 로컬 vLLM 서빙 스크립트 + smoke test
- [x] 정적 데모 페이지 (`demo/`) + GitHub Pages 배포
- [x] 문서 한국어 전환

## DB / RAG

- [ ] `kb/ingest.py` 구현: `data/raw/` PDF → `SourceDocument` / `Chunk` → `data/processed/`
- [ ] chunk 분할 기준 확정 (≈ 1–3문장, < 500자) — 태깅 방식은 [clinical.md](clinical.md)와 협의
- [ ] 검색 backend 결정: 키워드(sqlite FTS5) vs. 임베딩 (on-prem 가능한 모델)
- [ ] 교차 언어 검색 대응: 영어 노트 기반 `query_text` ↔ 한국어 chunk (다국어 임베딩 또는 한국어 query 재작성)
- [ ] 영어 출처 처리 방식 결정: ingestion 시 번역 vs. 생성 단계에서 번역 — [clinical.md](clinical.md)와 협의
- [ ] 실제 `KnowledgeStore` 구현 후 `api/main.py:get_store`에서 교체, 계약(`search` 규칙) 테스트 추가

## 생성 (추출 · 생성 프롬프트)

- [ ] 승인된 연구 환경에서 실제 MIMIC 노트로 추출 프롬프트 개선 (노트는 repo에 절대 넣지 않음)
- [ ] 생성 프롬프트 개선: 가독성, 인용 누락/위반 비율 확인
- [ ] 의료진 파트의 프롬프트 검토 의견 반영 (`pipeline/prompts.py`)
- [ ] trigger 추가 시: enum + `TRIGGER_TOPICS` + KB 태깅 + 테스트

## LLM / 배포

- [ ] SNUH endpoint 체크리스트 확인 ([docs/local_llm.md](../docs/local_llm.md#snuh-endpoint-httpsllmsnuhorgllm)): 경로, 모델 이름, `response_format`, 인증/프록시
- [ ] SNUH 서빙 모델과 같은 계열로 로컬 개발 모델 맞추기

## HTML / 프론트엔드

- [ ] `render/templates/education.html.j2` 디자인 개선 (환자 가독성, 모바일, 인쇄)
- [ ] 의료진 상담 안내(`clinician_consult`) 및 출처 각주 표시 방식 의료진 파트와 확인

## 평가 (1차 평가 10월말)

- [ ] 의료진 파트가 정한 평가 기준을 바탕으로 평가용 입력 세트와 실행 스크립트 준비
- [ ] 자동 지표: 인용 유효성, 섹션 누락, warning 발생 비율
- [ ] 의료진 평가용 출력물 묶음(HTML + 근거) 생성

## 메모

- 10-01: dummy KB는 한국어, 입력 노트는 영어라 현재 키워드 점수는 거의 기여하지 않음. 실제 backend에서 해결 필요.
