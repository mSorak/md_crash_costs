# data_cache (generated, not in git)

Map-ready artifacts for the web app. **Not committed to GitHub** (see `.gitignore`).

Generate locally before running the app or building the Docker image:

```bash
cd backend
# use your venv / pip install -r requirements.txt first
python prepare_data.py
```

Expected files:

- `crashes.parquet`
- `meta.json`
- `geo/county.geojson`, `geo/place.geojson`, `geo/tract.geojson`

`prepare_data.py` reads `crash_cost_eval.csv`, Census shapes, and
`geo_summaries/` from a data directory (default: sibling `../data/`, or set
`CRASH_COST_DATA_DIR`). Source data is not in this git repo. Re-run when inputs
change.

For Fly.io deploys, keep this folder on your machine; `fly deploy` uploads it
into the Docker build context even though it is not in git.
