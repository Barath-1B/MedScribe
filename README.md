# OCR Clinical Text Analysis

A FastAPI + React app that turns handwritten clinical notes into structured, human-verified data, and measures how OCR errors "snowball" through an NLP pipeline. Local models only — no cloud LLM.

Two things live here, sharing OCR + metrics infrastructure:

- **Clinical scribe** ("MedScribe" — the name still shows up in the login page, `MEDSCRIBE_*` env vars, and the `ocr_clinical.db` filename) — capture a note image → OCR with per-token confidence → extract structured medication fields → flag low-confidence fields for human review → verify → patient-history rollup. Auth-gated, audited.
- **OCR error-analysis** (the original project) — measures how OCR errors amplify through a 4-stage NLP pipeline (OCR → spell correction → summarization → topic classification), recomputing CER/WER against ground truth at every stage. Public, no auth.

Extraction is transparent rules + a drug gazetteer, not a black box — every field carries a confidence score and can be audited.

## Features

**Clinical scribe**
- Patient records with visit history
- Note capture via TrOCR (handwriting) or Tesseract (fallback), with per-field confidence
- Review queue that flags low-confidence extracted fields for a human to verify or correct
- Append-only audit log of who created/verified/changed what

**OCR analysis**
- Batch OCR + accuracy metrics (CER/WER) over bundled handwriting datasets
- 4-stage pipeline runner with a "snowball" view of how errors amplify stage to stage
- Degradation curves across injected error rates, per-document error breakdown, and a document inspector (OCR vs. ground truth diff)
- Live progress via Server-Sent Events on cold-cache runs

## Tech stack

**Backend** — FastAPI, SQLAlchemy + Alembic, SQLite (default) / Postgres, bcrypt + PyJWT, Transformers + PyTorch (TrOCR), pytesseract, OpenCV, symspellpy, python-Levenshtein

**Frontend** — React 18, React Router 6, Recharts, Vite. No UI kit, no state library — page-local state only.

## Project structure

```
backend/
  app/
    routes/       # thin HTTP layer (auth, patients, review, analysis, pipeline_results, ...)
    services/      # DB-backed orchestration (clinical_service, analysis_service, pipeline_service)
    pipeline/       # compute stages: ocr, extraction, spell_correction, summarizer, classifier, runner, metrics
    data/          # rxnorm_drugs.txt gazetteer
  alembic/         # migrations
  run.py           # dev entrypoint
frontend/
  src/
    pages/         # one page per nav route
    components/    # shared UI (Navbar, DataTable, KpiCard, AuthImage, ...)
    api.js         # all HTTP/SSE calls go through here
```

## Getting started

**Prerequisites**: Python 3.12 (matches the Docker image; no hard pin in `requirements.txt`), Node 18+. Tesseract is required as the OCR fallback — a Windows binary is bundled at `Tesseract/` (gitignored); on Linux/Docker install `tesseract-ocr` via your package manager.

### Backend

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # or source .venv/bin/activate on Linux/macOS
pip install -r requirements.txt
python run.py
```

Serves on `http://localhost:8000`. Tables are auto-created on startup in dev (no need to run Alembic locally). The first request that needs handwriting OCR downloads the TrOCR model (~1GB) to `.hf_cache/`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Serves on `http://localhost:5173` and proxies `/api` to `http://localhost:8000`.

### First-run bootstrap

The clinical-scribe routes (`/api/patients`, `/api/review`) require a login. The **first** `POST /api/auth/register` becomes an `admin` automatically; every registration after that needs an admin Bearer token. Easiest path: register your first user from the app's Login page (register tab) before touching Patients or Review.


## API overview

| Prefix | Auth | Purpose |
|---|---|---|
| `/api/auth` | — | register / login / me |
| `/api/patients` | required | patient CRUD + history rollup |
| `/api/review` | required | note capture, review queue, verify |
| `/api/analysis` | public | dataset-1 OCR accuracy + KPIs (SSE stream available) |
| `/api/pipeline` | public | 4-stage pipeline results for dataset-1 (SSE stream available) |
| `/api/degradation` | public | aggregated snowball/degradation curves |
| `/api/notes` | public | ground-truth notes for experiments |
| `/api/experiments` | public | run the pipeline across a sweep of injected error rates |
| `/api/documents` | public | dataset image/diff/gallery endpoints |
| `/api/results` | public | CSV export |
| `/api/health` | — | liveness check |

See [CLAUDE.md](CLAUDE.md) for the full architecture writeup (pipeline internals, caching gotchas, OCR engine fallback behavior).

## Datasets

Only `ds-FUNSD` (printed forms) ships in git. `ds-HF-MedicalRecords` and `ds-DoctorHandwritingBD` feed the handwriting analysis flow but are gitignored (too large) — each has its own `SOURCE.txt`/`download.py` to fetch it locally. A few other `ds-*` folders exist at the repo root but aren't wired into the current pipeline.

## Docker

`backend/Dockerfile` builds a deploy image (installs `tesseract-ocr`, runs `alembic upgrade head` then `uvicorn` on start) but is **not build-tested** — verify `docker build` yourself before relying on it. `MEDSCRIBE_DATABASE_URL` and `MEDSCRIBE_JWT_SECRET` must be provided at container runtime; mount a volume for `HF_HOME` if you don't want to re-download TrOCR on every container start.

## Notes

- No automated test suite. `test_trocr.py`, `check_db.py`, and `backend/eval_extraction.py` are ad-hoc scripts, run manually, not CI-wired.
- The dataset OCR cache auto-detects garbage results (e.g. Tesseract run on handwriting) and transparently re-OCRs everything with TrOCR — the first request after that can be slow.
- `CLAUDE.md` is the primary reference for contributors going deeper than this README.
