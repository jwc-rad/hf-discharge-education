# Knowledge DB ↔ LLM 계약

현재 DB는 dummy 인메모리 store다 (`src/hf_edu/kb/dummy.py` + `seed_chunks.json`).
이 문서는 DB 팀이 pipeline을 건드리지 않고 실제 backend(sqlite FTS, pgvector 등)를 구축할 수 있도록
**스키마와 규칙**을 고정한다. 기준(source of truth)은 코드다:
`src/hf_edu/schemas/knowledge.py`, `src/hf_edu/kb/store.py`.

## 스키마

### `SourceDocument`
| 필드 | 타입 | 설명 |
|---|---|---|
| `document_id` | `str` `^[a-z0-9_]+$` | 고정 slug, 예: `kshf_living` |
| `title`, `publisher` | `str` | HTML 각주에 표시됨 |
| `source_type` | `guideline \| hospital \| patient_education` | `data/raw/` 하위 폴더와 일치 |
| `language` | `ko \| en` | |
| `url`, `drive_path`, `license_note` | `str?` | `drive_path`는 `data/raw/` 기준 상대 경로 |

### `Chunk`
| 필드 | 타입 | 설명 |
|---|---|---|
| `chunk_id` | `str` `{document_id}:p{page}:{n}` | 고정값; 생성된 텍스트가 인용함 |
| `document_id`, `page` | | |
| `text` | `str` | 원문 **그대로의** 구절; 절대 의역하지 않음 |
| `topics` | `list[Topic]` | `diet`, `activity`, `medication`, `symptom_action`, `followup` |
| `applies_when` | `list[TriggerCode]` | 비어 있으면 일반 chunk; 아니면 해당 trigger 중 하나가 있는 환자에게만 사용 |
| `audience` | `patient \| clinician` | 현재 생성에는 `patient`만 사용 |
| `language` | `ko \| en` | |
| `version` | `int` | text가 바뀌면 증가 |

## 인터페이스

```python
class KnowledgeStore(Protocol):
    def search(self, query: RetrievalQuery) -> list[RetrievedChunk]: ...
    def get_chunks(self, chunk_ids: list[str]) -> list[Chunk]: ...
    def get_document(self, document_id: str) -> SourceDocument | None: ...
```

`RetrievalQuery{topic, triggers, query_text?, language?, audience, top_k}` →
`RetrievedChunk{chunk, score, matched_triggers}`.

`search`는 반드시:
- `query.topic in chunk.topics`이고 `audience`/`language`(주어진 경우)가 일치하는 chunk만 반환한다;
- 비어 있지 않은 `applies_when`이 `query.triggers`와 겹치지 않는 chunk는 제외한다;
- 최대 `top_k`개를 `score` 내림차순으로 반환한다 (동점: `chunk_id` 순);
- 같은 DB 버전과 query에 대해 결정적(deterministic)이어야 한다.

## 규칙

1. **LLM은 DB를 직접 조회하지 않는다.** orchestrator(`pipeline/retrieve.py`)가 추출된
   `ClinicalContext`로부터 query를 만든다: 주제마다 일반 query 1개(`triggers=[]`), 그리고 해당 주제에
   활성 trigger가 있으면 trigger query 1개를 추가하고, trigger에 매칭된 chunk를 앞에 두어 병합한다.
   DB에 대한 tool call / function calling은 없다.
2. **생성 시점에는 읽기 전용.** 쓰기는 오프라인 ingestion(`kb/ingest.py`)에서만 한다.
3. **chunk는 데이터로서 LLM에 전달된다**: JSON user message 안에 `{id, text}`만 넣으며, system
   prompt에 출처는 지시가 아니라 데이터임을 명시한다.
4. **인용은 닫힌 집합(closed-world)이다.** 생성된 각 항목의 `source_ids`는 *해당 주제에* 제공된
   chunk ID와 `NOTE`(퇴원 기록지)의 부분집합이어야 한다. 위반 시: 오류 목록을 담아 1회 재시도 →
   그래도 위반이면 잘못된 ID를 제거하고, 출처가 하나도 남지 않은 항목은 삭제하며,
   `EducationMaterial.warnings`에 `warning`을 기록한다.
5. **버전별 text 불변.** chunk의 text를 수정하려면 새 `version`이 필요하다. 그래야 저장된 교육자료의
   인용이 재현 가능하다.
6. **DB에 환자 데이터 금지.** KB에는 출판된 / 기관 교육자료만 들어간다.
   노트(MIMIC 또는 EHR)는 요청 입력으로만 쓰이며 API가 저장하지 않는다.
7. **예산.** query당 `top_k` (기본 3, `RETRIEVAL_TOP_K`) → 주제당 ≤ 2 × `top_k`,
   4개 핵심 주제에 걸쳐 요청당 ≤ 24 chunk.
   프롬프트가 8–16k context window에 들어가도록 chunk는 짧게 유지한다 (≈ 1–3문장, < 500자).
8. **trigger는 결정적이다.** `triggers_applied` / `clinician_consult`는 LLM이 아니라 코드가
   `TRIGGER_TOPICS`로부터 설정한다.

## DB 팀 미결 사항
- chunk 분할 단위, 그리고 `topics` / `applies_when` 태깅 담당자 (임상팀 매핑 시트?).
- 한국어 vs. 영어 출처: ingestion 시 번역할지, 생성 단계에서 영어 chunk를 번역하게 할지?
- 검색 backend: 키워드(sqlite FTS5) vs. 임베딩. 임베딩 모델도 on-prem에서 돌아가야 한다.
- 현재 `query_text`는 영어 노트 내용으로 만들어지는데 dummy chunk는 한국어라서, dummy 키워드 점수는
  거의 기여하지 않는다. 실제 backend는 교차 언어 검색(다국어 임베딩)이나 한국어 query 재작성이 필요하다.
