"""Inspect Vehicles_070125_123125v2.csv vs broken original."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
SUFFIX = "070125_123125"
VEH_COL = "ReportNumber Veh"


def norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def main() -> None:
    reports = pd.read_csv(
        DATA / "Reports" / f"Reports_{SUFFIX}.csv",
        usecols=["Reportnumber"],
        dtype=str,
    )
    rep_set = set(norm(reports["Reportnumber"]))

    old = pd.read_csv(
        DATA / "Vehicles" / f"Vehicles_{SUFFIX}.csv",
        usecols=[VEH_COL],
        dtype=str,
    )
    new = pd.read_csv(
        DATA / "Vehicles" / f"Vehicles_{SUFFIX}v2.csv",
        dtype=str,
        low_memory=False,
    )

    print("=== File shape ===")
    print(f"Reports_{SUFFIX}: {len(reports):,} rows")
    print(f"Old Vehicles_{SUFFIX}: {len(old):,} rows, cols={len(old.columns)}")
    print(f"v2 Vehicles_{SUFFIX}v2: {len(new):,} rows, cols={len(new.columns)}")
    print(f"v2 has {VEH_COL}: {VEH_COL in new.columns}")
    print(f"v2 has Reportnumber: {'Reportnumber' in new.columns}")

    old_rid = norm(old[VEH_COL])
    new_rid = norm(new[VEH_COL]) if VEH_COL in new.columns else norm(new["Reportnumber"])
    old_ids = set(old_rid)
    new_ids = set(new_rid)

    old_per = old_rid.groupby(old_rid).size()
    new_per = new_rid.groupby(new_rid).size()

    print("\n=== H2 2025 batch coverage ===")
    covered_old = len(rep_set & old_ids)
    covered_new = len(rep_set & new_ids)
    print(f"Reports with >=1 vehicle (old): {covered_old:,} ({100 * covered_old / len(rep_set):.1f}%)")
    print(f"Reports with >=1 vehicle (v2):  {covered_new:,} ({100 * covered_new / len(rep_set):.1f}%)")
    print(f"Still missing in v2: {len(rep_set - new_ids):,}")
    print(f"Orphan vehicle IDs in v2 (not in Reports): {len(new_ids - rep_set):,}")

    print("\n=== Vehicles per report (covered reports only) ===")
    for label, per in [("old", old_per), ("v2", new_per)]:
        print(f"  {label}: median={per.median():.1f} mean={per.mean():.2f} max={per.max()}")

    for s in ["010124_063124", "070124_123124", "010125_063125"]:
        v = pd.read_csv(
            DATA / "Vehicles" / f"Vehicles_{s}.csv",
            usecols=[VEH_COL],
            dtype=str,
        )
        c = norm(v[VEH_COL]).groupby(norm(v[VEH_COL])).size()
        print(f"  ref {s}: median={c.median():.1f} mean={c.mean():.2f} rows={len(v):,}")

    print("\n=== Example MCP296500BT ===")
    rid = "MCP296500BT"
    print(f"  old vehicles: {old_per.get(rid, 0)}")
    print(f"  v2 vehicles:  {new_per.get(rid, 0)}")

    # ReportNumber Veh vs Reportnumber consistency in v2
    if VEH_COL in new.columns and "Reportnumber" in new.columns:
        a = norm(new["Reportnumber"])
        b = norm(new[VEH_COL])
        mismatch = (a != b).sum()
        print(f"\n=== v2 Reportnumber vs ReportNumber Veh ===")
        print(f"  mismatched rows: {mismatch:,} / {len(new):,}")

    # Compare v2 column set to a good half-year file
    ref = pd.read_csv(
        DATA / "Vehicles" / f"Vehicles_010125_063125.csv",
        nrows=0,
    ).columns.tolist()
    v2_cols = new.columns.tolist()
    only_ref = set(ref) - set(v2_cols)
    only_v2 = set(v2_cols) - set(ref)
    print("\n=== Column parity vs 2025 H1 reference ===")
    print(f"  columns in reference not in v2: {sorted(only_ref) or '(none)'}")
    print(f"  columns in v2 not in reference: {sorted(only_v2) or '(none)'}")

    # Simulate full combined dataset zero-vehicle rate
    all_rep = pd.read_csv(
        DATA / "Reports" / "reports_maryland_2024_2025.csv",
        usecols=["Reportnumber", "LOD Crash Date"],
        dtype={"Reportnumber": str},
    )
    all_rep["_rid"] = norm(all_rep["Reportnumber"])
    all_rep["d"] = pd.to_datetime(all_rep["LOD Crash Date"], errors="coerce")

    parts: list[pd.Series] = []
    for s in ["010124_063124", "070124_123124", "010125_063125"]:
        v = pd.read_csv(
            DATA / "Vehicles" / f"Vehicles_{s}.csv",
            usecols=[VEH_COL],
            dtype=str,
        )
        parts.append(norm(v[VEH_COL]))
    parts.append(new_rid)
    sim = pd.concat(parts, ignore_index=True)
    sim_counts = sim.groupby(sim).size()
    all_rep["n_veh"] = all_rep["_rid"].map(sim_counts).fillna(0).astype(int)

    h2 = (all_rep["d"] >= "2025-07-01") & (all_rep["d"] <= "2025-12-31")
    print("\n=== Simulated full dataset (3 good batches + v2) ===")
    zv = (all_rep["n_veh"] == 0).sum()
    print(f"Zero-vehicle reports overall: {zv:,} ({100 * zv / len(all_rep):.2f}%)")
    print(f"  H2 2025 zero-veh: {(h2 & (all_rep.n_veh == 0)).sum():,}")
    print(f"  Other periods zero-veh: {(~h2 & (all_rep.n_veh == 0)).sum():,}")

    # Current broken combined for contrast
    cur = pd.read_csv(
        DATA / "Vehicles" / "vehicles_maryland_2024_2025.csv",
        usecols=[VEH_COL],
        dtype=str,
    )
    cur_counts = norm(cur[VEH_COL]).groupby(norm(cur[VEH_COL])).size()
    all_rep["n_veh_cur"] = all_rep["_rid"].map(cur_counts).fillna(0).astype(int)
    print("\n=== Current combined file (broken H2 batch) ===")
    print(f"Zero-vehicle reports: {(all_rep.n_veh_cur == 0).sum():,} ({100 * (all_rep.n_veh_cur == 0).mean():.2f}%)")


if __name__ == "__main__":
    main()
