"""Audit report ↔ vehicle ↔ occupant linkage in Maryland crash CSVs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
REPORT_ID = "Reportnumber"
VEH_REPORT = "ReportNumber Veh"
OCC_REPORT = "ReportNumber Occ"
NM_REPORT = "ReportNumber NM"


def norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def main() -> None:
    reports = pd.read_csv(DATA / "Reports/reports_maryland_2024_2025.csv", dtype=str, low_memory=False)
    vehicles = pd.read_csv(DATA / "Vehicles/vehicles_maryland_2024_2025.csv", dtype=str, low_memory=False)
    occupants = pd.read_csv(DATA / "Occupants/occupants_maryland_2024_2025.csv", dtype=str, low_memory=False)
    nm = pd.read_csv(DATA / "NonMotorists/nonmotorists_maryland_2024_2025.csv", dtype=str, low_memory=False)

    reports["_rid"] = norm(reports[REPORT_ID])
    vehicles["_rid"] = norm(vehicles[VEH_REPORT])
    occupants["_rid"] = norm(occupants[OCC_REPORT])
    nm["_rid"] = norm(nm[NM_REPORT])

    report_set = set(reports["_rid"])
    veh_report_set = set(vehicles["_rid"].dropna())
    occ_report_set = set(occupants["_rid"].dropna())
    nm_report_set = set(nm["_rid"].dropna())

    print("=" * 70)
    print("ROW COUNTS")
    print("=" * 70)
    print(f"Reports rows: {len(reports):,}  unique IDs: {len(report_set):,}")
    print(f"Vehicle rows: {len(vehicles):,}  unique report IDs: {len(veh_report_set):,}")
    print(f"Occupant rows: {len(occupants):,}  unique report IDs: {len(occ_report_set):,}")
    print(f"NonMotorist rows: {len(nm):,}  unique report IDs: {len(nm_report_set):,}")

    veh_per_report = vehicles.groupby("_rid", observed=False).size()
    reports["n_veh"] = reports["_rid"].map(veh_per_report).fillna(0).astype(int)
    sev = pd.to_numeric(reports["Crash Severity"], errors="coerce")
    reports["severity"] = sev

    zero_veh = (reports["n_veh"] == 0).sum()
    print("\n" + "=" * 70)
    print("REPORT <-> VEHICLE")
    print("=" * 70)
    print(f"Reports with 0 vehicle records: {zero_veh:,} ({100 * zero_veh / len(reports):.1f}%)")
    print(f"Reports with >=1 vehicle: {(reports['n_veh'] > 0).sum():,}")

    orphan_veh_ids = veh_report_set - report_set
    orphan_rows = len(vehicles[vehicles["_rid"].isin(orphan_veh_ids)])
    print(f"Vehicle report IDs NOT in Reports: {len(orphan_veh_ids):,} IDs, {orphan_rows:,} rows")

    missing_in_veh = report_set - veh_report_set
    print(f"Report IDs with no vehicle rows: {len(missing_in_veh):,}")

    print("\nZero-vehicle reports by severity:")
    for code, desc in [(1, "Fatal"), (2, "Injury"), (3, "PDO")]:
        n = ((reports["n_veh"] == 0) & (reports["severity"] == code)).sum()
        print(f"  {code} {desc}: {n:,}")

    zv = reports[reports["n_veh"] == 0].copy()
    occ_on = occupants.groupby("_rid").size()
    nm_on = nm.groupby("_rid").size()
    zv["n_occ"] = zv["_rid"].map(occ_on).fillna(0).astype(int)
    zv["n_nm"] = zv["_rid"].map(nm_on).fillna(0).astype(int)

    print("\n" + "=" * 70)
    print("ZERO-VEHICLE REPORTS: OTHER ENTITIES")
    print("=" * 70)
    print(f"  0 occupants AND 0 nonmotorists: {((zv.n_occ == 0) & (zv.n_nm == 0)).sum():,}")
    print(f"  occupants only: {((zv.n_occ > 0) & (zv.n_nm == 0)).sum():,}")
    print(f"  nonmotorists only: {((zv.n_occ == 0) & (zv.n_nm > 0)).sum():,}")
    print(f"  both: {((zv.n_occ > 0) & (zv.n_nm > 0)).sum():,}")

    print("\n" + "=" * 70)
    print("ORPHAN OCC / NM (not in Reports)")
    print("=" * 70)
    print(f"Occupant IDs not in Reports: {len(occ_report_set - report_set):,}")
    print(f"NonMotorist IDs not in Reports: {len(nm_report_set - report_set):,}")

    print("\n" + "=" * 70)
    print("ID NORMALIZATION")
    print("=" * 70)
    print(f"Reports with whitespace in ID: {(reports[REPORT_ID] != reports[REPORT_ID].str.strip()).sum()}")
    print(f"Vehicles with whitespace in ID: {(vehicles[VEH_REPORT] != vehicles[VEH_REPORT].str.strip()).sum()}")

    veh_by_prefix: dict[str, set[str]] = {}
    for vid in veh_report_set:
        if len(vid) >= 10:
            veh_by_prefix.setdefault(vid[:10], set()).add(vid)
    prefix_multi = {p: ids for p, ids in veh_by_prefix.items() if len(ids) > 1}

    zv_near = sum(
        1
        for rid in missing_in_veh
        if len(rid) >= 10 and rid[:10] in prefix_multi and (prefix_multi[rid[:10]] - {rid})
    )
    print(f"Zero-vehicle reports sharing 10-char prefix with a vehicle ID: {zv_near:,} / {len(missing_in_veh):,}")

    print("\nExamples (report ID -> vehicle IDs with same prefix):")
    shown = 0
    for rid in sorted(missing_in_veh):
        if len(rid) >= 10 and rid[:10] in prefix_multi:
            alts = sorted(prefix_multi[rid[:10]] - {rid})[:3]
            if alts:
                print(f"  {rid} -> {alts}")
                shown += 1
                if shown >= 8:
                    break

    print("\n" + "=" * 70)
    print("PERIOD FILE COVERAGE (vehicles in half-year files but not combined match?)")
    print("=" * 70)
    for half in ["Reports_010124_063124.csv", "Reports_070124_123124.csv"]:
        p = DATA / "Reports" / half
        if p.exists():
            h = pd.read_csv(p, usecols=[REPORT_ID], dtype=str)
            print(f"  {half}: {len(h):,} rows")

    print("\n" + "=" * 70)
    print("SAMPLE ZERO-VEHICLE PDO WITH OCCUPANTS")
    print("=" * 70)
    pdo_zv_occ = zv[(zv.severity == 3) & (zv.n_occ > 0)].head(10)
    for _, r in pdo_zv_occ.iterrows():
        county = r.get("Crash County Description", "?")
        if isinstance(county, str):
            county = county[:35]
        print(f"  {r['_rid']}  occ={r['n_occ']} nm={r['n_nm']}  county={county}")

    print("\n" + "=" * 70)
    print("SAMPLE ORPHAN VEHICLE REPORT IDS")
    print("=" * 70)
    for oid in sorted(orphan_veh_ids)[:10]:
        print(f"  {oid}")


if __name__ == "__main__":
    main()
