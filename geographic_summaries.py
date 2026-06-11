"""
Build geographic summary tables for Maryland: NHGIS ACS context + crash aggregates.

Requires:
  - data/crash_cost_eval.csv from crash_costs.ipynb (with spatial-join columns    GISJOIN_county, GISJOIN_tract, GISJOIN_place, or GEO_ID* equivalents).
  - data/census/nhgis0008_csv.zip (NHGIS extract).

Outputs (data/geo_summaries/):
  - census_context_{state,county,place,tract}.csv — ds272 + B08201 (AU40*) vehicle summaries
  - crash_summary_{state,county,place,tract}.csv — crash counts, injuries, fatalities, cost sums
  - merged_{state,county,place,tract}.csv — census left-joined to crash summaries on GISJOIN

Run: python geographic_summaries.py
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CENSUS_ZIP = DATA_DIR / "census" / "nhgis0008_csv.zip"
CRASH_CSV = DATA_DIR / "crash_cost_eval.csv"
OUT_DIR = DATA_DIR / "geo_summaries"

LEVEL_FILES = {
    "state": (
        "nhgis0008_csv/nhgis0008_ds272_20245_state.csv",
        "nhgis0008_csv/nhgis0008_ds273_20245_state.csv",
    ),
    "county": (
        "nhgis0008_csv/nhgis0008_ds272_20245_county.csv",
        "nhgis0008_csv/nhgis0008_ds273_20245_county.csv",
    ),
    "place": (
        "nhgis0008_csv/nhgis0008_ds272_20245_place.csv",
        "nhgis0008_csv/nhgis0008_ds273_20245_place.csv",
    ),
    "tract": (
        "nhgis0008_csv/nhgis0008_ds272_20245_tract.csv",
        "nhgis0008_csv/nhgis0008_ds273_20245_tract.csv",
    ),
}

MD_STATE_GISJOIN = "G240"

MOTORIST_INJURY_SPECS = [
    ("1", "fatal"),
    ("2", "police_severity_2_mais4"),
    ("3", "police_severity_3_mais2"),
    ("4", "police_severity_4_mais1"),
    ("5", "police_severity_5_mais0"),
    ("missing", "injury_unknown"),
]


def load_merged_census_md(zip_path: Path, path272: str, path273: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as z:
        ds272 = pd.read_csv(z.open(path272), low_memory=False)
        ds273 = pd.read_csv(z.open(path273), low_memory=False)
    md272 = ds272[ds272["STUSAB"] == "MD"].copy()
    md273 = ds273[ds273["STUSAB"] == "MD"].copy()
    au40_cols = [c for c in md273.columns if c.startswith("AU40")]
    return md272.merge(md273[["GISJOIN"] + au40_cols], on="GISJOIN", how="inner")


def add_vehicle_household_summaries(df: pd.DataFrame) -> pd.DataFrame:
    """B08201 AU40E001–006: household counts by vehicles available; derived % and vehicle stock."""
    out = df.copy()
    hh = out["AU40E001"].astype(float)
    hh_safe = hh.replace(0, np.nan)
    out["census_pct_hh_0_vehicles"] = out["AU40E002"].astype(float) / hh_safe * 100
    out["census_pct_hh_1_vehicle"] = out["AU40E003"].astype(float) / hh_safe * 100
    out["census_pct_hh_2_vehicles"] = out["AU40E004"].astype(float) / hh_safe * 100
    out["census_pct_hh_3_vehicles"] = out["AU40E005"].astype(float) / hh_safe * 100
    out["census_pct_hh_4plus_vehicles"] = out["AU40E006"].astype(float) / hh_safe * 100
    e3, e4, e5, e6 = (
        out["AU40E003"].astype(float),
        out["AU40E004"].astype(float),
        out["AU40E005"].astype(float),
        out["AU40E006"].astype(float),
    )
    out["census_est_vehicle_units_floor_4plus_bucket"] = e3 * 1 + e4 * 2 + e5 * 3 + e6 * 4
    out["census_est_vehicle_units_mid_4plus_bucket"] = e3 * 1 + e4 * 2 + e5 * 3 + e6 * 4.5
    if "AUO6E001" in out.columns:
        pop = out["AUO6E001"].astype(float).replace(0, np.nan)
        out["census_est_vehicles_per_person_mid"] = (
            out["census_est_vehicle_units_mid_4plus_bucket"] / pop
        )
        out["census_est_vehicles_per_person_floor"] = (
            out["census_est_vehicle_units_floor_4plus_bucket"] / pop
        )
    return out


def crash_cost_columns(df: pd.DataFrame) -> list[str]:
    """Every estimated_*_comp_cost_* column except `estimated_total_comp_cost_*` (same as TotalComp row)."""
    pat = re.compile(r"^estimated_.+_comp_cost_(2025|2019)usd$")
    cols = [c for c in df.columns if pat.match(c)]
    return [c for c in cols if not c.startswith("estimated_total_comp_cost_")]


def resolve_crash_gisjoin_columns(crashes: pd.DataFrame) -> dict[str, str]:
    """Map level name -> column on crash file (NHGIS `GISJOIN_*` from spatial join)."""
    mapping: dict[str, str] = {}
    for level, candidates in [
        ("county", ["GISJOIN_county"]),
        ("tract", ["GISJOIN_tract"]),
        ("place", ["GISJOIN_place"]),
    ]:
        for c in candidates:
            if c in crashes.columns:
                mapping[level] = c
                break
        else:
            raise KeyError(
                f"Crash data missing {level} join column (tried {candidates}). "
                "Run the spatial-join cell in crash_costs.ipynb, then re-export crash_cost_eval.csv."
            )
    return mapping


def aggregate_crashes(crashes: pd.DataFrame, group_col: str) -> pd.DataFrame:
    # Police crash category (`Crash Severity` in Maryland export): 1 fatal, 2 injury, 3 property damage only.
    df = crashes
    if "Crash Severity" in crashes.columns:
        df = crashes.copy()
        cs = pd.to_numeric(df["Crash Severity"], errors="coerce")
        df["_sev_property_damage"] = (cs == 3).astype(int)
        df["_sev_injury"] = (cs == 2).astype(int)
        df["_sev_fatal"] = (cs == 1).astype(int)

    cost_cols = crash_cost_columns(df)
    agg_kw: dict = {
        "crash_n_crashes": ("Reportnumber", "count"),
    }
    if "Crash Severity" in crashes.columns:
        agg_kw["crash_n_property_damage"] = ("_sev_property_damage", "sum")
        agg_kw["crash_n_injury"] = ("_sev_injury", "sum")
        agg_kw["crash_n_fatal"] = ("_sev_fatal", "sum")
    agg_kw.update(
        {
            "crash_motorists_involved": ("n_occupant_records", "sum"),
            "crash_nonmotorists_involved": ("n_nonmotorist_records", "sum"),
            "crash_motorist_fatalities": ("occupants_InjuryStatus_Occ_1_count", "sum"),
            "crash_nonmotorist_fatalities": ("nonmotorists_InjuryStatus_NM_1_count", "sum"),
        }
    )
    for code, label in MOTORIST_INJURY_SPECS:
        if code == "missing":
            oc = "occupants_InjuryStatus_Occ_missing_count"
            nm = "nonmotorists_InjuryStatus_NM_missing_count"
        else:
            oc = f"occupants_InjuryStatus_Occ_{code}_count"
            nm = f"nonmotorists_InjuryStatus_NM_{code}_count"
        if oc in crashes.columns:
            agg_kw[f"crash_motorist_injuries_{label}"] = (oc, "sum")
        if nm in crashes.columns:
            agg_kw[f"crash_nonmotorist_injuries_{label}"] = (nm, "sum")
    for c in cost_cols:
        agg_kw[f"crash_sum_{c}"] = (c, "sum")
    if "estimated_total_comp_cost_2025usd" in crashes.columns:
        agg_kw["crash_sum_estimated_total_comp_cost_2025usd"] = (
            "estimated_total_comp_cost_2025usd",
            "sum",
        )
    elif "estimated_total_comp_cost_2019usd" in crashes.columns:
        agg_kw["crash_sum_estimated_total_comp_cost_2019usd"] = (
            "estimated_total_comp_cost_2019usd",
            "sum",
        )
    grouped = df.groupby(group_col, dropna=False, sort=False).agg(**agg_kw)
    return grouped.reset_index().rename(columns={group_col: "GISJOIN"})


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    crashes = pd.read_csv(CRASH_CSV, low_memory=False)
    join_cols = resolve_crash_gisjoin_columns(crashes)

    for level, (p272, p273) in LEVEL_FILES.items():
        census = load_merged_census_md(CENSUS_ZIP, p272, p273)
        census = add_vehicle_household_summaries(census)
        c_path = OUT_DIR / f"census_context_{level}.csv"
        census.to_csv(c_path, index=False)

        if level == "state":
            ckey = pd.Series(MD_STATE_GISJOIN, index=crashes.index, dtype=object)
        elif level == "county":
            ckey = crashes[join_cols["county"]]
        elif level == "tract":
            ckey = crashes[join_cols["tract"]]
        else:
            ckey = crashes[join_cols["place"]].fillna("__NOT_IN_CENSUS_PLACE__")

        tmp = crashes.copy()
        tmp["_geo_group"] = ckey
        crash_sum = aggregate_crashes(tmp, "_geo_group")
        u_path = OUT_DIR / f"crash_summary_{level}.csv"
        crash_sum.to_csv(u_path, index=False)

        join_how = "outer" if level == "place" else "left"
        merged = census.merge(crash_sum, on="GISJOIN", how=join_how)
        crash_cols = [c for c in merged.columns if c.startswith("crash_")]
        merged[crash_cols] = merged[crash_cols].fillna(0)
        m_path = OUT_DIR / f"merged_{level}.csv"
        merged.to_csv(m_path, index=False)
        print(f"wrote {c_path.name} ({len(census)} rows), {u_path.name} ({len(crash_sum)}), {m_path.name}")


if __name__ == "__main__":
    main()
