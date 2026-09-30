# data/raw — raw RAG sources

Raw source PDFs for the knowledge base (pipeline stage 1: 원천 데이터 → 구조화 저장 → DB).
**PDFs are git-ignored.** Download them from the team Shared Google Drive (HF 교육자료 folder;
ask a team member for the link):

- e.g. `GHH_HF-PatientGuide_EN_2023_FINAL_240423_e-copy.pdf`

| Folder | Put here | `source_type` |
|---|---|---|
| `guidelines/` | Society guidelines (KSHF, ESC, AHA/ACC, ...) | `guideline` |
| `hospital/` | SNUH / in-house discharge and education materials | `hospital` |
| `patient_education/` | Patient-facing booklets and guides (e.g. KSHF 생활백서, AHA packets) | `patient_education` |

Conventions:
- Keep the original file name. Record title, publisher, URL and license in the ingestion manifest
  (`SourceDocument` in `src/hf_edu/schemas/knowledge.py`); `drive_path` is the path relative to this folder.
- Never put patient data (MIMIC notes, EHR exports) here. Patient notes are pipeline *input*, not KB content.
- Structured output of ingestion goes to `data/processed/` (also git-ignored).
