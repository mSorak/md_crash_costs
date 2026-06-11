# Maryland Crash Costs — web app

**[Live site](https://crash-cost-md.fly.dev)**

React + MapLibre map and FastAPI/DuckDB API for exploring Maryland crash comprehensive costs by geography and individual crash.

---

## What’s in this folder

| Piece | Role |
|-------|------|
| `backend/` | FastAPI API, DuckDB aggregations, `prepare_data.py` |
| `frontend/` | React/Vite UI, map, filters, comparison dashboard |
| `data_cache/` | Generated map artifacts (gitignored) — Parquet + GeoJSON |
| `Dockerfile`, `fly.toml` | Production deploy to Fly.io |

**Not in git:** raw crash CSVs, `crash_cost_eval.csv`, or `data_cache/` contents. Generate `data_cache/` locally before running or deploying (see below).

---

## Prerequisites

- Python ≥ 3.11
- Node ≥ 20
- Prepared source files on disk (not included in this repo):
  - `crash_cost_eval.csv`
  - Census shape cache under `data/census/tl2024_shapes_cache/`
  - `data/geo_summaries/*.csv`

By default `prepare_data.py` looks for these in a sibling `../data/` directory (full research project layout). Override with the `CRASH_COST_DATA_DIR` environment variable pointing at your data folder.

---

## Local development

```bash
# 1. Build data_cache/ (rerun when source CSV changes)
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python prepare_data.py

# 2. API → http://127.0.0.1:8000
uvicorn app.main:app --reload --reload-dir app

# 3. Frontend → http://localhost:5173
cd ../frontend
npm install
npm run dev
```

**Windows:** use `npm.cmd` if PowerShell blocks scripts. Keep `--reload-dir app` so uvicorn does not watch `.venv/`.

**Production-like:**

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Architecture

| Layer | Choice |
|-------|--------|
| Map | MapLibre GL + deck.gl |
| UI | React, Vite, TypeScript |
| API | FastAPI + DuckDB over `crashes.parquet` |

Zoom levels (`frontend/src/config.ts`): counties → places → tracts → individual crashes.

**API:** `/api/health`, `/api/metadata`, `/api/geo/{level}`, `/api/summary/{level}`, `/api/crashes`.

**Site copy:** edit `frontend/src/content/*.ts` (markdown links: `[text](url)`).

---

## Deploy

See **[DEPLOY.md](./DEPLOY.md)**. Requires `data_cache/` on disk before `fly deploy` (baked into the Docker image, not committed to git).

---

## Data & methodology

Unit costs follow NHTSA [*The Economic and Societal Impact of Motor Vehicle Crashes, 2019 (Revised)*](https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813403). Crash records come from [Maryland State Police dashboards](https://mdsp.maryland.gov/safety-prevention/interactive-data-dashboards). Methodology text is in the live app under **Methodology & Sources**.
