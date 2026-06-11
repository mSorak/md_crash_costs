"""Post-rebuild sanity checks for vehicle linkage and key examples."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
CACHE = Path(__file__).resolve().parent.parent / "crash_cost_app" / "data_cache"


def norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def main() -> None:
    veh = pd.read_csv(DATA / "Vehicles/vehicles_maryland_2024_2025.csv", usecols=["ReportNumber Veh"], dtype=str)
    eval_df = pd.read_csv(
        DATA / "crash_cost_eval.csv",
        usecols=["Reportnumber", "n_vehicle_records", "n_occupant_records", "estimated_total_comp_cost_2025usd", "LOD Crash Date", "Crash Severity"],
        dtype={"Reportnumber": str},
        low_memory=False,
    )
    eval_df["_rid"] = norm(eval_df["Reportnumber"])
    eval_df["d"] = pd.to_datetime(eval_df["LOD Crash Date"], errors="coerce")

    veh_counts = norm(veh["ReportNumber Veh"]).groupby(norm(veh["ReportNumber Veh"])).size()
    eval_df["n_veh"] = eval_df["_rid"].map(veh_counts).fillna(0).astype(int)

    print("=== Combined vehicles file ===")
    print(f"  rows: {len(veh):,}")
    print(f"  unique reports: {veh['ReportNumber Veh'].astype(str).str.strip().nunique():,}")

    print("\n=== crash_cost_eval.csv ===")
    print(f"  rows: {len(eval_df):,}")
    zv = (eval_df["n_vehicle_records"] == 0).sum()
    print(f"  n_vehicle_records == 0: {zv:,} ({100 * zv / len(eval_df):.3f}%)")

    h2 = (eval_df["d"] >= "2025-07-01") & (eval_df["d"] <= "2025-12-31")
    print(f"  H2 2025 zero-veh: {(h2 & (eval_df.n_vehicle_records == 0)).sum():,}")
    print(f"  pre-Jul 2025 zero-veh: {(~h2 & (eval_df.n_vehicle_records == 0)).sum():,}")

    pdo = eval_df[eval_df["Crash Severity"].astype(str) == "3"]
    pdo_zero_cost = (pdo["estimated_total_comp_cost_2025usd"].fillna(0) == 0).sum()
    print(f"  PDO crashes with $0 total cost: {pdo_zero_cost:,} ({100 * pdo_zero_cost / len(pdo):.1f}% of PDO)")

    rid = "MCP296500BT"
    row = eval_df[eval_df._rid == rid]
    if len(row):
        r = row.iloc[0]
        print(f"\n=== {rid} ===")
        print(f"  vehicles: {int(r.n_vehicle_records)}")
        print(f"  occupants: {int(r.n_occupant_records)}")
        print(f"  total cost: ${float(r.estimated_total_comp_cost_2025usd):,.0f}")

    pq = pd.read_parquet(CACHE / "crashes.parquet", columns=["report_number", "n_vehicle_records", "cost_total"])
    pq_zv = (pq["n_vehicle_records"].fillna(0) == 0).sum()
    print(f"\n=== data_cache/crashes.parquet ===")
    print(f"  rows: {len(pq):,}")
    print(f"  zero vehicles: {pq_zv:,}")

    ex = pq[pq["report_number"] == rid]
    if len(ex):
        print(f"  {rid} cost_total: ${ex.iloc[0].cost_total:,.0f}, vehicles: {int(ex.iloc[0].n_vehicle_records)}")

    ok = zv <= 20 and (h2 & (eval_df.n_vehicle_records == 0)).sum() <= 10
    print(f"\n{'PASS' if ok else 'CHECK NEEDED'}: rebuild sanity")


if __name__ == "__main__":
    main()
