# Geographic summaries

CSV outputs are produced by running from the project root:

```bash
python geographic_summaries.py
```

**Input**

- `data/crash_cost_eval.csv` — must include NHGIS **`GISJOIN_county`**, **`GISJOIN_tract`**, and **`GISJOIN_place`** from the spatial-join step in `crash_costs.ipynb`.
- `data/census/nhgis0008_csv.zip` — NHGIS ACS tables (see `data/census/CENSUS_DATA.md`).

**Outputs** (per geographic level: `state`, `county`, `place`, `tract`)

| File | Contents |
|------|----------|
| `census_context_<level>.csv` | Maryland rows: **ds272** (population, commute, income, housing units, …) plus **ds273** **B08201** (`AU40*`). Derived fields: **`census_pct_hh_*_vehicles`**, **`census_est_vehicle_units_*`** (4+ bucket uses4 or 4.5 vehicles per household), **`census_est_vehicles_per_person_*`** when **AUO6E001** (total population) is present. |
| `crash_summary_<level>.csv` | **`crash_n_crashes`**, **`crash_n_property_damage`**, **`crash_n_injury`**, **`crash_n_fatal`** (from report **`Crash Severity`**: 3 / 2 / 1 in the Maryland extract), involvement totals, **person fatalities** (**`crash_motorist_fatalities`** / **`crash_nonmotorist_fatalities`**, injury code 1), **injury counts by police severity code**, **`crash_sum_*`** cost columns, plus **`crash_sum_estimated_total_comp_cost_*`**. |
| `merged_<level>.csv` | **`census_context_*` left join** `crash_summary_*` on **`GISJOIN`**. **Place** uses an **outer** join so a row **`__NOT_IN_CENSUS_PLACE__`** captures crashes outside any Census place boundary. |

**Join key**

Use **`GISJOIN`** to link these files to NHGIS tabular extracts and to TIGER/NHGIS shapefiles.
