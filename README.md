# Maryland Crash Costs

**[Live map → crash-cost-md.fly.dev](https://crash-cost-md.fly.dev)**

An interactive map of police-reported motor vehicle crash **comprehensive costs** in Maryland (2024–2025), built from Maryland State Police crash exports and national unit-cost tables from NHTSA. Explore how the burden varies by county, community, census tract, and individual crash — filter by date and crash type, compare places in the dashboard, and read methodology on the site.

Personal research project by [Matt Sorak](https://perfectnumbers.substack.com/). Not affiliated with any state agency.

---

## What this repo contains

| Part | Location | Role |
|------|----------|------|
| **Web app** | [`crash_cost_app/`](crash_cost_app/) | React + MapLibre map, FastAPI + DuckDB API, Fly.io deploy |
| **Cost pipeline** | [`crash_costs.ipynb`](crash_costs.ipynb) | Merge MDSP exports, apply NHTSA unit costs, spatial join to Census |
| **Geo summaries** | [`geographic_summaries.py`](geographic_summaries.py) | County / place / tract crash + census context tables |
| **Unit costs** | [`tables_from_report.xlsx`](tables_from_report.xlsx) | NHTSA Table 1-10 (comprehensive police-reported costs) |
| **Analysis scripts** | [`scripts/`](scripts/), [`blog/`](blog/) | Optional blog / research figures |

**Raw crash CSVs and the evaluated crash table are not in git** (size + MDSP terms). See [`data/DATA.md`](data/DATA.md) for how to obtain and rebuild them.

---

## How it works

### 1. Crash-level costs

For each police report in Maryland (2024–2025 H1/H2 exports):

1. **Reports**, **vehicles**, **occupants**, and **non-motorists** are merged on report number.
2. Maryland police **injury status codes** (1–5) are mapped to NHTSA **MAIS-based** unit-cost columns (Fatal, MAIS0–MAIS4).
3. **Property-damage-only** crashes (severity code 3) use per-vehicle costs only; injury crashes use person-based columns.
4. Components (medical, congestion, economic, QALYs, etc.) sum to **comprehensive cost** per crash in **June 2025 USD**.

Details match the site’s [Methodology](https://crash-cost-md.fly.dev) tab and the notebook.

### 2. Geography

Each crash point is joined to 2024 TIGER/Line **county**, **census tract**, and **place** boundaries. NHGIS / ACS summaries add **population** and **vehicle ownership** context for per-capita metrics.

### 3. Web app

```
crash_cost_eval.csv + Census shapes + geo_summaries
        │  prepare_data.py
        ▼
data_cache/  (Parquet + GeoJSON + meta.json)
        │  FastAPI + DuckDB
        ▼
React map  (choropleth → zoom to tracts → crash points)
```

- **Choropleth** metrics include comprehensive cost per capita, fatalities/injuries per 10,000, medical cost, vehicles per person, and more.
- **Filters**: date range, crash type, pedestrian/cyclist involvement.
- **Comparison dashboard**: chart up to 10 selected geographies.

Stack: MapLibre + deck.gl, React/Vite/TypeScript, FastAPI, DuckDB over Parquet. See [`crash_cost_app/README.md`](crash_cost_app/README.md) for developer setup.

---

## Quick start (web app only)

If you already have `data/crash_cost_eval.csv` and related files per [`data/DATA.md`](data/DATA.md):

```bash
# 1. Build map cache
cd crash_cost_app/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python prepare_data.py

# 2. API
uvicorn app.main:app --reload --reload-dir app

# 3. Frontend (separate terminal)
cd ../frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Production build + Docker: [`crash_cost_app/DEPLOY.md`](crash_cost_app/DEPLOY.md).

---

## Full pipeline (from raw MDSP exports)

1. Download crash CSVs from [MDSP dashboards](https://mdsp.maryland.gov/safety-prevention/interactive-data-dashboards) into `data/Reports/`, `Vehicles/`, `Occupants/`, `NonMotorists/`.
2. Run **`crash_costs.ipynb`** → writes `data/crash_cost_eval.csv`.
3. Run **`python geographic_summaries.py`** → writes `data/geo_summaries/*.csv`.
4. Run **`prepare_data.py`** → writes `crash_cost_app/data_cache/`.
5. Run or deploy the web app.

Census file inventory: [`data/census/CENSUS_DATA.md`](data/census/CENSUS_DATA.md). Geo summary columns: [`data/geo_summaries/README.md`](data/geo_summaries/README.md).

---

## Deploy

The public site runs on [Fly.io](https://fly.io) at **https://crash-cost-md.fly.dev**. Deploy steps (Docker, `fly deploy`, baked-in `data_cache/`): **[`crash_cost_app/DEPLOY.md`](crash_cost_app/DEPLOY.md)**.

---

## Citation & caveats

**Unit costs:** National Highway Traffic Safety Administration. [*The Economic and Societal Impact of Motor Vehicle Crashes, 2019 (Revised)*](https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813403).

**Crash data:** Maryland Department of State Police via [interactive dashboards](https://mdsp.maryland.gov/safety-prevention/interactive-data-dashboards).

**Caveats**

- Maryland injury codes are mapped approximately to NHTSA MAIS-based averages.
- Comprehensive costs include **QALY-valued** losses, not only out-of-pocket spending.
- Unit costs are population averages; individual crashes vary widely.
- Property-damage-only crashes do not receive person-based cost lines in this implementation.

---

## License

Code in this repository is provided for research and transparency. Crash data remains subject to MDSP access terms; NHTSA report and tables retain their original publication terms.
