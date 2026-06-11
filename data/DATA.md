# Data files (not in git)

Large or licensed inputs are **not committed** to GitHub. Reproduce them locally using the steps below.

## 1. Maryland crash exports (MDSP)

Download half-year CSV extracts from the [Maryland Department of State Police interactive data dashboards](https://mdsp.maryland.gov/safety-prevention/interactive-data-dashboards) (crash dashboards for 2024–present).

Place files under:

| Folder | Entity |
|--------|--------|
| `data/Reports/` | Crash reports |
| `data/Vehicles/` | Vehicles |
| `data/Occupants/` | Occupants |
| `data/NonMotorists/` | Non-motorists |

The notebook concatenates H1/H2 files per entity into combined files such as `reports_maryland_2024_2025.csv`.

## 2. NHTSA unit costs

Unit costs come from NHTSA [*The Economic and Societal Impact of Motor Vehicle Crashes, 2019 (Revised)*](https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813403).

This repo includes **`tables_from_report.xlsx`** (sheet `police_unit_costs_comp`, Table 1-10). Dollar values are inflated to June 2025 using a **1.26** factor ([BLS calculator](https://www.bls.gov/data/inflation_calculator.htm), June 2019 → June 2025).

## 3. Census geography & context

- **TIGER/Line 2024** shapefiles for Maryland counties, tracts, and places — see `data/census/CENSUS_DATA.md`.
- **NHGIS / ACS** tabular extracts for population and vehicle ownership — same doc.

Running the spatial-join cells in `crash_costs.ipynb` caches extracted shapes under `data/census/tl2024_shapes_cache/`.

## 4. Pipeline outputs

| Step | Command / notebook | Output |
|------|-------------------|--------|
| Cost + geography | `crash_costs.ipynb` | `data/crash_cost_eval.csv` |
| Aggregates | `python geographic_summaries.py` | `data/geo_summaries/*.csv` |
| Web app cache | `cd crash_cost_app/backend && python prepare_data.py` | `crash_cost_app/data_cache/` |

`prepare_data.py` requires `crash_cost_eval.csv`, shape cache, and `geo_summaries/` CSVs on disk before building the map.
