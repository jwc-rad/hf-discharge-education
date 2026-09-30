# data/raw — RAG 원본 자료

지식 베이스용 원본 PDF (pipeline 1단계: 원천 데이터 → 구조화 저장 → DB).
**PDF는 git-ignored 대상이다.** 팀 공유 Google Drive(HF 교육자료 폴더)에서 내려받는다
(링크는 팀원에게 문의):

- 예: `GHH_HF-PatientGuide_EN_2023_FINAL_240423_e-copy.pdf`

| 폴더 | 넣을 자료 | `source_type` |
|---|---|---|
| `guidelines/` | 학회 가이드라인 (KSHF, ESC, AHA/ACC 등) | `guideline` |
| `hospital/` | SNUH / 원내 퇴원·교육 자료 | `hospital` |
| `patient_education/` | 환자용 책자·가이드 (예: KSHF 생활백서, AHA 자료) | `patient_education` |

규칙:
- 원본 파일명을 유지한다. 제목, 발행처, URL, 라이선스는 ingestion manifest에 기록한다
  (`src/hf_edu/schemas/knowledge.py`의 `SourceDocument`). `drive_path`는 이 폴더 기준 상대 경로다.
- 환자 데이터(MIMIC 노트, EHR 추출본)는 절대 여기에 두지 않는다. 환자 노트는 KB 내용이 아니라 pipeline의 *입력*이다.
- ingestion의 구조화 결과물은 `data/processed/`에 저장한다 (역시 git-ignored).
