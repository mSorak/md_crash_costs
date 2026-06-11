# Maryland Crash Costs — web app

Interactive map UI and API for the parent project. **Overview, methodology, and full data pipeline:** see the [repository README](../README.md).

**Live site:** [https://crash-cost-md.fly.dev](https://crash-cost-md.fly.dev)

---

## Prerequisites

- Python ≥ 3.11
- Node ≥ 20
- Parent project data prepared per [`../data/DATA.md`](../data/DATA.md) (`crash_cost_eval.csv`, Census shapes, `geo_summaries/`)

---

## Local development

```bash
# 1. Build data_cache/ (one-time; rerun when source CSV changes)
cd backend
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python prepare_data.py

# 2. API → http://127.0.0.1:8000
uvicorn app.main:app --reload --reload-dir app

# 3. Frontend → http://localhost:5173 (proxies /api to backend)
cd ../frontend
npm install
npm run dev
```

**Windows notes:** If `npm` is blocked by execution policy, use `npm.cmd`. Restrict `--reload` to `app/` so uvicorn does not watch `.venv/`.

**Production-like single process:**

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Layout

```text
crash_cost_app/
  backend/
    prepare_data.py      # CSV → Parquet + GeoJSON + meta.json
    app/
      main.py            # FastAPI routes
      data.py            # DuckDB aggregations
      metrics.py         # Metric registry
  frontend/
    src/
      App.tsx            # Filters, map, dashboard, site tabs
      components/        # MapView, FilterBar, ComparisonDashboard, …
      content/           # Site copy (hero, methodology, about) — edit freely
      config.ts          # Zoom thresholds, basemap URLs, colors
  data_cache/            # Generated (gitignored); see data_cache/README.md
  Dockerfile, fly.toml   # Fly.io deploy
```

---

## Architecture (short)

| Layer | Choice |
|-------|--------|
| Map | MapLibre GL + deck.gl overlays |
| UI | React, Vite, TypeScript |
| API | FastAPI + DuckDB over `crashes.parquet` |
| Prep | pandas + geopandas |

Zoom thresholds in `frontend/src/config.ts`: counties &lt; 8.5 → places → tracts ≥ 11 → crash points ≥ 11.5.

**API:** `GET /api/health`, `/api/metadata`, `/api/geo/{level}`, `/api/summary/{level}`, `/api/crashes` (bbox). Filters: `date_from`/`date_to`, `crash_types`, `nonmotorist`.

**Site copy:** `frontend/src/content/*.ts` (markdown-style links: `[text](url)`).

---

## Deploy

**[DEPLOY.md](./DEPLOY.md)** — Docker build, `fly deploy`, GitHub clone workflow. `data_cache/` must exist locally before deploy (not in git).
