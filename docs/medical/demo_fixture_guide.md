# 데모 fixture 작성 가이드 (의료진용)

정적 데모 페이지(`demo/index.html`)에 새 샘플을 추가하거나 기존 샘플을 고치는 방법을 설명한다.
코드를 몰라도 **텍스트 파일 1개(합성 노트)와 JSON 파일 1개(fixture)** 만 다룰 수 있도록 썼다.
직접 작성해도 되고, 초안만 만들어 기술 파트에 넘겨도 된다 ([작업 방식](#2-작업-방식-직접-작성-vs-기술-파트-인계) 참고).

> 합성 노트에는 **실제 환자 정보(MIMIC 포함)를 절대 쓰지 않는다.** 모든 내용은 팀이 만든 가상의 사례여야 한다.

## 1. 구성: 노트와 fixture가 함께 동작하는 방식

```
data/samples/discharge_note_synthetic_NN.txt   합성 퇴원 기록지 (영어)
demo/fixtures/NN.json                          LLM이 냈어야 할 출력을 사람이 대신 적은 파일
            └─ note_path ─────────────────────▶ 위 노트 파일을 가리킴
```

데모는 LLM을 호출하지 않는다. pipeline의 LLM 단계 2개를 fixture로 대체하고, 나머지는 실제 코드가 수행한다.

| 단계 | 누가 수행 | fixture의 어느 부분 |
|---|---|---|
| ① 추출 (노트 → 임상 정보) | **사람이 작성** (LLM 대역) | `context` |
| ② 검색 (KB에서 근거 chunk 찾기) | 실제 코드 (dummy KB) | 없음 — `context`의 trigger로 결정됨 |
| ③ 생성 (환자용 문장 작성) | **사람이 작성** (LLM 대역) | `draft` |
| 인용 검증 · 제목/trigger/상담 안내 부여 · HTML 렌더링 | 실제 코드 | 없음 |

따라서 fixture를 잘못 쓰면 **실제 코드의 검증이 빌드 실패로 알려준다.** 실패는 정상적인 피드백이니 메시지를 읽고 고치면 된다.

## 2. 작업 방식: 직접 작성 vs. 기술 파트 인계

**A. 의료진이 직접 작성** — [3장](#3-기존-예시를-복사해-수정하기)부터 [8장](#8-빌드와-확인)까지 그대로 진행한다.

**B. 초안만 작성해 기술 파트에 인계** — JSON 문법이 부담스러우면 아래를 전달한다.
- 합성 노트 `.txt` (또는 노트에 넣고 싶은 임상 내용)
- 켜고 싶은 trigger와 근거가 되는 문장, "의료진 상담 필요"가 표시되길 원하는 주제
- 환자용 문장 초안 (주제별, 출처는 노트인지 어떤 chunk인지 표시)
- 표·문서 형태면 충분하다. JSON 변환은 기술 파트가 한다.

**인계 시 기술 파트가 해야 하는 일:** `tests/test_demo.py`가 fixture를 `01`, `02`, `03`으로 고정해 검사하므로,
새 fixture를 추가하면 테스트도 함께 갱신해야 한다. 직접 작성한 경우에도 PR/공유 시 이 점을 알려 준다.
(기존 fixture를 수정만 하는 경우에는 테스트 변경이 필요 없다.)

## 3. 기존 예시를 복사해 수정하기

가장 쉬운 방법은 비슷한 기존 샘플을 복사하는 것이다. 예: 새 샘플 `04`.

```bash
cp data/samples/discharge_note_synthetic_01.txt data/samples/discharge_note_synthetic_04.txt
cp demo/fixtures/01.json demo/fixtures/04.json
```

1. 노트 `.txt`를 가상의 새 사례로 고쳐 쓴다. 첫 줄의 `SYNTHETIC NOTE FOR DEVELOPMENT ONLY...` 문구는 유지한다.
2. `04.json`의 `note_path`를 새 노트 경로로 바꾼다.
3. `title`(드롭다운에 보이는 제목)과 `summary`(한두 문장 요약)를 고친다.
4. `context`와 `draft`를 새 노트에 맞게 고친다 (아래 4–7장).

### `context`의 필드

| 필드 | 값 | 설명 |
|---|---|---|
| `hf_type` | `HFrEF` / `HFmrEF` / `HFpEF` / `unknown` | 노트에 근거가 없으면 `unknown` |
| `ef_percent` | 숫자 또는 `null` | |
| `discharge_weight_kg` | 숫자 또는 `null` | |
| `discharge_medications[]` | `name`, `dose`, `frequency`, `change`, `evidence` | `change`: `new` / `changed` / `continued` / `stopped` / `unknown` |
| `diet_instructions[]`, `activity_instructions[]`, `followup[]` | `text`, `evidence` | `text`은 영어로 간단히 정리해도 됨 |
| `triggers[]` | `code`, `present`, `evidence` | [5장](#5-trigger) 참고 |

**주의: 값이 없어도 키를 지우지 않는다.** 없는 값은 `null`로 적는다 (예: 중단된 약의 `"dose": null`).
목록이 비면 `[]`로 둔다.

### `draft`의 구조

```json
"draft": {
  "sections": [
    { "topic": "diet", "items": [
      { "text": "환자용 문장", "why": "이유 한 문장 또는 null", "source_ids": ["NOTE", "dummy_patient_guide:p1:1"] }
    ]},
    { "topic": "activity", "items": [ ... ] },
    { "topic": "medication", "items": [ ... ] },
    { "topic": "symptom_action", "items": [ ... ] }
  ]
}
```

## 4. verbatim evidence (원문 그대로 인용)

`evidence`에는 노트에서 **글자 그대로 복사한 구절**만 넣는다. 요약·번역·철자 수정·대소문자 변경을 하지 않는다.
빌드 시 각 `evidence`가 노트에 그대로 들어 있는지 검사하며, 없으면 실패한다.

- 적용 대상: 약, 식이, 활동, 외래(`followup`)의 `evidence`와, trigger 중 `evidence`가 있는 것.
- 노트에서 줄이 바뀌는 곳을 걸쳐 인용하려면 JSON에서 `\n`으로 적는다. 01번 예:
  노트에 `Lisinopril was stopped due to` + 줄바꿈 + `hyperkalemia`가 있으므로
  `"evidence": "Lisinopril was stopped due to\nhyperkalemia"`.
- 줄바꿈 때문에 헷갈리면 한 줄 안에서 끝나는 짧은 구절을 인용한다 (예: `2 g sodium diet`).
- 노트를 수정했다면 그 노트를 인용하는 `evidence`도 함께 확인한다.

## 5. trigger

trigger는 노트에서 개인화를 켜는 임상 조건이다. 8개 코드가 정해져 있다 (`src/hf_edu/schemas/common.py`).
모든 코드를 `triggers[]`에 **각각 한 번씩** 적고 값을 표시한다 (01.json 참고).

| `present` | 의미 | `evidence` |
|---|---|---|
| `true` | 노트에 해당 조건이 있음 | 노트 원문 구절 (필수) |
| `false` | 노트에 "없음"이 명시됨 | 보통 `null` |
| `null` | 언급 없음 | `null` |

코드 목록과 영향받는 주제:

| `code` | 의미 | 개인화되는 주제 |
|---|---|---|
| `hyperkalemia` | 고칼륨혈증 | diet, medication |
| `hypokalemia` | 저칼륨혈증 | diet, medication |
| `hyponatremia` | 저나트륨혈증 | diet |
| `ckd` | 만성 콩팥병 | diet, medication |
| `diabetes` | 당뇨 | diet |
| `fluid_restriction` | 수분 제한 | diet |
| `warfarin` | 와파린 복용 | medication, diet |
| `icd_or_pacemaker` | ICD/심박동기 | activity, symptom_action |

- 위 표에 따라 **`present: true`인 trigger가 영향을 주는 주제에 "의료진 상담 필요" 안내가 자동으로 붙는다.**
  `draft`에 상담 안내 문구를 직접 쓰지 않는다.
- trigger 전용 근거 chunk(예: 고칼륨혈증일 때만 쓰는 칼륨 식이 안내)는 해당 trigger가 켜졌을 때만 검색된다.
  그러므로 trigger를 켜면 `draft`의 해당 주제에서 그 chunk를 인용할 수 있고, 꺼져 있으면 인용할 수 없다.
- 코드 목록 자체(추가·삭제)는 임상 파트가 제안하고 기술 파트가 반영한다 (`roadmap/medical.md`).

## 6. 교육 4개 주제

`draft.sections`에는 다음 4개 주제를 **모두, 이 순서로** 넣는다 (외래 `followup`은 핵심 주제에서 제외되어 있다).

| `topic` | 화면 제목 | 내용 |
|---|---|---|
| `diet` | 식사 | 나트륨, 수분 제한, 칼륨 등 |
| `activity` | 활동과 재활 | 걷기, 무거운 물건, 재활 |
| `medication` | 약 복용 | 새로 시작 / 변경 / 중단 / 유지 |
| `symptom_action` | 증상 악화 대처법 | 매일 체중 측정, 연락 기준, 응급 증상 |

제목·순서·trigger 표시는 코드가 붙인다. 작성자는 각 항목의 세 값만 쓴다.

| 필드 | 규칙 |
|---|---|
| `text` | 환자가 바로 실천할 수 있는 쉬운 한국어 문장. 한 항목에 하나의 행동 |
| `why` | 이유 한 문장. 필요 없으면 `null` |
| `source_ids` | 근거 ID 1개 이상 ([7장](#7-인용-규칙)) |

주제당 항목은 **1–5개**를 권장한다 (실제 생성기의 제한과 동일).

## 7. 인용 규칙

모든 항목은 근거를 `source_ids`로 밝혀야 한다. 인용은 **닫힌 집합**이라, 아래 둘 중 하나만 쓸 수 있다.

1. **`NOTE`** — 퇴원 기록지 자체. 노트에 적힌 사실(약 용량, 식이 제한 수치, 퇴원 체중 등)에서 나온 문장.
2. **그 주제에 검색된 chunk ID** — 형식 `문서ID:p페이지:번호` (예: `dummy_patient_guide:p2:1`).
   일반 교육 내용(예: "숨이 차면 진료팀에 연락하세요")은 노트가 아니라 chunk를 인용한다.

주의:
- 다른 주제에서 검색된 chunk를 인용하면 실패한다. chunk는 자신이 속한 `topics`에서만 검색된다.
- 없는 ID, 오타, 빈 `source_ids`도 실패한다.
- 한 항목에 여러 개를 함께 인용할 수 있다 (`["NOTE", "dummy_patient_guide:p1:1"]`).

**쓸 수 있는 chunk ID 찾는 법**
1. `src/hf_edu/kb/seed_chunks.json`에서 chunk의 `topics`(어느 주제에 쓰이는지)와
   `applies_when`(어떤 trigger가 켜져 있어야 하는지, 비어 있으면 항상)을 본다.
2. 빌드 후 `demo/index.html`에서 샘플을 열어 **검색 단계**를 보면 그 주제에 실제로 검색된 chunk가 나온다.
   여기에 없는 ID는 인용할 수 없다.

현재 KB는 dummy 문장이며, 실제 KB가 구축되면 chunk ID와 내용이 바뀐다.
그때는 인용 ID를 다시 확인해야 하므로 fixture는 KB 변경 후 재빌드해서 점검한다.

## 8. 빌드와 확인

```bash
conda activate hf-edu
python demo/build_demo.py           # demo/index.html 재생성. 성공하면 샘플별 항목 수와 warnings 0 출력
pytest tests/test_demo.py -q        # 데모 테스트 (fixture를 추가했다면 기술 파트가 테스트 갱신)
```

성공하면 브라우저로 `demo/index.html`을 열어 새 샘플을 확인한다 (설치·서버 불필요).
`main` 브랜치에 `demo/index.html` 변경이 반영되면 GitHub Pages로 자동 배포된다.
따라서 **fixture나 노트를 바꿨다면 `demo/index.html`도 재생성해서 함께 제출**한다.

## 9. 자주 나는 오류

| 메시지 / 증상 | 원인 | 해결 |
|---|---|---|
| `FixtureError: 04: evidence not found verbatim in note: [...]` | `evidence`가 노트와 글자 단위로 다름 (대소문자, 공백, 줄바꿈) | 노트에서 다시 복사. 줄바꿈이 있으면 `\n` |
| `FixtureError: 04: pipeline warnings [...]` | 인용 오류: 그 주제에서 검색되지 않은 chunk ID, 오타, 누락된 섹션 | [7장](#7-인용-규칙)대로 ID 확인. warning 본문에 문제 항목이 나온다 |
| `pydantic ValidationError` | 오타 (`change` 값, `topic`, trigger `code`), 누락된 키, 타입 오류 | 메시지의 필드 경로를 보고 3–6장 표와 대조 |
| `json.decoder.JSONDecodeError` | JSON 문법 오류: 마지막 항목 뒤 쉼표, 따옴표 누락, 문자열 안의 실제 줄바꿈 | 지정된 줄·열 근처를 확인. 줄바꿈은 `\n`으로 |
| `FileNotFoundError` | `note_path` 오타 또는 노트 파일 없음 | 경로는 repo 루트 기준 (`data/samples/...`) |
| 새 샘플이 드롭다운에 없음 | `demo/index.html`을 재생성하지 않음 | `python demo/build_demo.py` |
| `test_demo.py` 실패 (`set(samples) == {"01","02","03"}`) | 새 fixture 추가 후 테스트 미갱신 | 기술 파트에 테스트 갱신 요청 |

## 10. 검토 체크리스트

작성 후 제출 전에 확인한다.

**노트와 추출(`context`)**
- [ ] 노트에 실제 환자 정보가 없고 `SYNTHETIC NOTE` 문구가 있다
- [ ] 모든 `evidence`가 노트에서 그대로 복사되었다 (빌드 통과)
- [ ] 약 이름·용량·횟수·`change`가 노트와 일치한다
- [ ] 8개 trigger가 모두 적혀 있고, `present`가 노트 내용과 맞다 (`true`는 근거 있음)
- [ ] 의료진 상담이 필요한 주제가 의도대로 표시된다 (데모 화면에서 확인)

**교육자료(`draft`)**
- [ ] 4개 주제가 모두 있고 각 1–5개 항목이다
- [ ] 수치(체중 증가 기준, 수분 제한 등)가 노트와 일치한다
- [ ] 환자 눈높이의 쉬운 말이고, 한 문장에 한 행동이다
- [ ] 불필요한 진단·치료 지시가 없다 (연구용 초안, 의료진 검토용)
- [ ] 모든 항목에 `source_ids`가 있고, 노트 사실은 `NOTE`, 일반 교육은 chunk를 인용한다
- [ ] 중단된 약·새 약 안내가 빠지지 않았다 ("누락 없이")

**빌드**
- [ ] `python demo/build_demo.py`가 warning 없이 끝난다
- [ ] 브라우저에서 새 샘플의 추출·검색·생성·최종 HTML을 확인했다
- [ ] `demo/index.html`도 함께 갱신되었다

관련 문서: [의료진 로드맵](../../roadmap/medical.md) · [DB ↔ LLM 계약](../engineering/db_contract.md)(인용 규칙의 근거) · [문서 목차](../README.md)
