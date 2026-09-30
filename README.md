# HF Discharge Education

AI-generated, patient-friendly discharge education for **heart failure** patients (SNUH Team 6).
A discharge note goes in. The pipeline retrieves evidence from a curated knowledge base of
guidelines and education materials and produces a structured Korean education guide
(식이 / 재활 / 복약 / 주의사항), rendered as HTML.

> Research prototype. Output is a **draft for clinician review**, not clinical advice.
> Never commit patient data (MIMIC notes, EHR exports) or the raw PDFs.

```
discharge note ──▶ ① extract (LLM) ──▶ ② retrieve (KB) ──▶ ③ generate (LLM) ──▶ ④ HTML
                    ClinicalContext      RetrievedChunk[]     EducationMaterial
```

See [docs/architecture.md](docs/architecture.md) for the design and
[docs/db_contract.md](docs/db_contract.md) for the DB ↔ LLM rules.

## Quickstart

Uses **conda + pip** only (these are what the deployment workstation allows).

```bash
conda env create -f environment.yml      # creates `hf-edu`, pip-installs requirements + this package
conda activate hf-edu
cp .env.example .env

pytest -q                                # no GPU / LLM needed (fake LLM)
```

Update an existing env after pulling: `pip install -r requirements.txt -r requirements-dev.txt -e .`

### Run the API

```bash
# Without a GPU (canned demo responses):
LLM_FAKE=1 uvicorn hf_edu.api.main:app --reload

# With a real model: start local vLLM first (docs/local_llm.md), then
uvicorn hf_edu.api.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs (use `--port 8080` for uvicorn if vLLM already uses 8000)
- Example:

```bash
python - <<'PY' > /tmp/note.json
import json; print(json.dumps({"text": open("data/samples/discharge_note_synthetic_01.txt").read()}))
PY
curl -s -X POST localhost:8080/v1/education/html -H 'Content-Type: application/json' \
     -d @/tmp/note.json > education.html
```

| Endpoint | In → Out |
|---|---|
| `GET /health` | liveness |
| `GET /llm/status` | configured endpoint, served models |
| `POST /v1/extract` | `DischargeNote` → `ClinicalContext` |
| `POST /v1/education` | `DischargeNote` → `{context, retrieved_chunk_ids, material}` |
| `POST /v1/education/html` | `DischargeNote` → `text/html` |

## Demo (no LLM, no install)

Open `demo/index.html` in a browser. Pick one of three synthetic discharge notes and step through
extract → retrieve → generate → the final patient HTML. The LLM outputs are hand-written fixtures
(`demo/fixtures/`); retrieval, citation checks and HTML rendering are the real code.

Regenerate after changing the pipeline, template, KB seed or fixtures (fails if a fixture no longer
fits the pipeline): `python demo/build_demo.py`

Hosted on GitHub Pages by `.github/workflows/pages.yml` whenever `demo/index.html` changes on
`main` (or on manual dispatch). One-time setup: Settings → Pages → Source: **GitHub Actions**.
The page is public even while the repo is private (private-repo Pages needs a paid plan).

## LLM configuration

| | `LLM_BASE_URL` |
|---|---|
| Dev (local vLLM) | `http://localhost:8000/v1` |
| Deployment | `https://llm.snuh.org/llm` |

Details, model choice and the SNUH checklist: [docs/local_llm.md](docs/local_llm.md).

## Repository layout

```
data/raw/            raw RAG PDFs from the Shared Drive (git-ignored; see data/raw/README.md)
data/processed/      future structured chunks (git-ignored)
data/samples/        synthetic discharge note(s) for development
docs/                architecture, DB contract, LLM setup
scripts/             serve_vllm.sh, smoke_llm.py
src/hf_edu/
  config.py          env-driven settings
  schemas/           Pydantic models: note, knowledge (DB), education (output)
  llm/               OpenAI-compatible client + fake client
  kb/                KnowledgeStore protocol, dummy store + seed data, ingestion stub
  pipeline/          extract → retrieve → generate, prompts
  render/            Jinja2 HTML template
  api/               FastAPI app
tests/
```

## Where to start (by team)

- **DB/RAG:** implement `kb/ingest.py` and a real `KnowledgeStore` following `docs/db_contract.md`.
  Swap it in `api/main.py:get_store`.
- **Clinical team:** review topics and `TriggerCode` (`schemas/common.py`), tag chunks, review prompts
  (`pipeline/prompts.py`).
- **Generation:** prompt iteration against real MIMIC notes. Do this only in the approved research
  environment; notes never enter this repo.
- **Frontend/HTML:** `render/templates/education.html.j2`.
- **Evaluation:** not started (누락 / 근거 일치 / 가독성; 1차 평가 10월말).
