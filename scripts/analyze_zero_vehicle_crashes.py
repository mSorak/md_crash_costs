"""Extended zero-vehicle crash analysis: impact descriptions, dates, batch coverage."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
PERIOD_SUFFIXES = ["010124_063124", "070124_123124", "010125_063125", "070125_123125"]


def norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def load_combined() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    reports = pd.read_csv(DATA / "Reports/reports_maryland_2024_2025.csv", dtype=str, low_memory=False)
    vehicles = pd.read_csv(DATA / "Vehicles/vehicles_maryland_2024_2025.csv", dtype=str, low_memory=False)
    occupants = pd.read_csv(DATA / "Occupants/occupants_maryland_2024_2025.csv", dtype=str, low_memory=False)
    reports["_rid"] = norm(reports["Reportnumber"])
    vehicles["_rid"] = norm(vehicles["ReportNumber Veh"])
    occupants["_rid"] = norm(occupants["ReportNumber Occ"])
    veh_per = vehicles.groupby("_rid", observed=False).size()
    reports["n_veh"] = reports["_rid"].map(veh_per).fillna(0).astype(int)
    reports["crash_date"] = pd.to_datetime(reports["LOD Crash Date"], errors="coerce")
    if reports["crash_date"].isna().all():
        reports["crash_date"] = pd.to_datetime(reports["Crashdate"], errors="coerce")
    reports["severity"] = pd.to_numeric(reports["Crash Severity"], errors="coerce")
    return reports, vehicles, occupants


def period_for_date(d: pd.Timestamp) -> str | None:
    if pd.isna(d):
        return None
    y, m = d.year, d.month
    if y == 2024 and 1 <= m <= 6:
        return "010124_063124"
    if y == 2024 and 7 <= m <= 12:
        return "070124_123124"
    if y == 2025 and 1 <= m <= 6:
        return "010125_063125"
    if y == 2025 and 7 <= m <= 12:
        return "010125_123125" if False else "070125_123125"
    return "out_of_range"


def audit_half_year_files(reports: pd.DataFrame, vehicles: pd.DataFrame) -> None:
    print("=" * 70)
    print("HALF-YEAR FILE COVERAGE vs CRASH DATE")
    print("=" * 70)

    rep_sets: dict[str, set[str]] = {}
    veh_sets: dict[str, set[str]] = {}
    for suffix in PERIOD_SUFFIXES:
        rp = DATA / "Reports" / f"Reports_{suffix}.csv"
        vp = DATA / "Vehicles" / f"Vehicles_{suffix}.csv"
        if rp.exists():
            rep_sets[suffix] = set(norm(pd.read_csv(rp, usecols=["Reportnumber"], dtype=str)["Reportnumber"]))
        if vp.exists():
            veh_sets[suffix] = set(norm(pd.read_csv(vp, usecols=["ReportNumber Veh"], dtype=str)["ReportNumber Veh"]))

    reports = reports.copy()
    reports["expected_period"] = reports["crash_date"].map(period_for_date)

    for label, mask in [("all", slice(None)), ("zero_veh", reports.n_veh == 0), ("has_veh", reports.n_veh > 0)]:
        sub = reports[mask]
        print(f"\n--- {label} ({len(sub):,} reports) ---")
        print("By expected half-year period:")
        for p in PERIOD_SUFFIXES + ["out_of_range", None]:
            n = (sub["expected_period"] == p).sum() if p else sub["expected_period"].isna().sum()
            if n:
                print(f"  {p or 'missing_date'}: {n:,}")

    # Is report in the half-year file matching its crash date?
    def in_expected_reports(row) -> bool:
        p = row["expected_period"]
        if not p or p == "out_of_range" or p not in rep_sets:
            return False
        return row["_rid"] in rep_sets[p]

    def in_expected_vehicles(row) -> bool:
        p = row["expected_period"]
        if not p or p == "out_of_range" or p not in veh_sets:
            return False
        return row["_rid"] in veh_sets[p]

    reports["in_expected_report_file"] = reports.apply(in_expected_reports, axis=1)
    reports["in_expected_vehicle_file"] = reports.apply(in_expected_vehicles, axis=1)

    zv = reports[reports.n_veh == 0]
    hv = reports[reports.n_veh > 0]
    print("\nReport ID present in half-year Reports file matching crash date:")
    print(f"  zero-veh: {zv.in_expected_report_file.mean()*100:.1f}%")
    print(f"  has-veh: {hv.in_expected_report_file.mean()*100:.1f}%")
    print("Report ID present in half-year Vehicles file matching crash date:")
    print(f"  zero-veh: {zv.in_expected_vehicle_file.mean()*100:.1f}%")
    print(f"  has-veh: {hv.in_expected_vehicle_file.mean()*100:.1f}%")

    # Vehicle in ANY half-year file vs expected period only
    all_veh = set().union(*veh_sets.values()) if veh_sets else set()
    zv_any = zv["_rid"].isin(all_veh).mean() * 100
    print(f"Zero-veh reports with vehicle row in ANY half-year file: {zv_any:.2f}%")

    # Reports in combined but missing from expected period vehicle file
    missing_veh_wrong_period = zv[~zv.in_expected_vehicle_file & zv.in_expected_report_file]
    print(f"Zero-veh: in correct Reports half-year but not in matching Vehicles half-year: {len(missing_veh_wrong_period):,}")

    # Cross-period: vehicle exists but in different period file than crash date
    def veh_periods(rid: str) -> list[str]:
        return [p for p, s in veh_sets.items() if rid in s]

    cross = 0
    for _, row in zv[zv.in_expected_report_file].head(5000).iterrows():
        ps = veh_periods(row["_rid"])
        if ps and row["expected_period"] not in ps:
            cross += 1
    print(f"(Sample 5000 zero-veh) vehicle in different half-year than crash date: {cross}")

    # Row counts per half-year file
    print("\nHalf-year file row counts:")
    for suffix in PERIOD_SUFFIXES:
        rp = DATA / "Reports" / f"Reports_{suffix}.csv"
        vp = DATA / "Vehicles" / f"Vehicles_{suffix}.csv"
        nr = len(pd.read_csv(rp, usecols=["Reportnumber"])) if rp.exists() else 0
        nv = len(pd.read_csv(vp, usecols=["ReportNumber Veh"])) if vp.exists() else 0
        print(f"  {suffix}: reports={nr:,}  vehicles={nv:,}")

    return reports


def analyze_collision_impact(reports: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("COLLISION IMPACT DESCRIPTION (Reports)")
    print("=" * 70)

    zv = reports[reports.n_veh == 0]
    hv = reports[reports.n_veh > 0]

    for col in ["CollisionImpact Description", "FirstHarmEvent Description", "SecondHarmEvent Description"]:
        if col not in reports.columns:
            continue
        print(f"\n--- {col} ---")
        print("Zero-vehicle top values:")
        vc = zv[col].fillna("(missing)").value_counts().head(15)
        for val, n in vc.items():
            print(f"  {n:6,}  ({100*n/len(zv):5.1f}%)  {val}")
        print("Has-vehicle top values (for contrast):")
        vc2 = hv[col].fillna("(missing)").value_counts().head(8)
        for val, n in vc2.items():
            print(f"  {n:6,}  ({100*n/len(hv):5.1f}%)  {val}")

    print("\n--- FirstHarmEvent Description: zero-veh vs has-veh (selected) ---")
    if "FirstHarmEvent Description" in reports.columns:
        top = zv["FirstHarmEvent Description"].value_counts().head(12).index
        rows = []
        for val in top:
            z = (zv["FirstHarmEvent Description"] == val).mean() * 100
            h = (hv["FirstHarmEvent Description"] == val).mean() * 100
            rows.append((val, z, h))
        for val, z, h in rows:
            print(f"  {z:5.1f}% zero-veh vs {h:5.1f}% has-veh — {val}")

    print("\n--- CollisionImpact Description by severity (zero-veh only) ---")
    for sev, name in [(1, "Fatal"), (2, "Injury"), (3, "PDO")]:
        sub = zv[zv.severity == sev]
        if len(sub) == 0:
            continue
        top = sub["CollisionImpact Description"].fillna("(missing)").value_counts().head(6)
        print(f"\n  Severity {sev} ({name}), n={len(sub):,}:")
        for val, n in top.items():
            print(f"    {n:5,} ({100*n/len(sub):4.1f}%) {val}")


def analyze_dates(reports: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("CRASH DATE DISTRIBUTION")
    print("=" * 70)

    zv = reports[reports.n_veh == 0].copy()
    hv = reports[reports.n_veh > 0].copy()
    zv["month"] = zv["crash_date"].dt.to_period("M")
    hv["month"] = hv["crash_date"].dt.to_period("M")

    zv_rate = zv.groupby("month").size() / reports.groupby(reports.crash_date.dt.to_period("M")).size()
    zv_rate = zv_rate.dropna().sort_index()

    print("\nZero-vehicle share by month (% of that month's reports):")
    for period, rate in zv_rate.items():
        print(f"  {period}: {rate*100:.1f}%")

    print(f"\nOverall zero-veh rate: {len(zv)/len(reports)*100:.1f}%")
    print(f"Mean monthly zero-veh rate: {zv_rate.mean()*100:.1f}%  std: {zv_rate.std()*100:.1f}%")

    # Boundary dates (half-year cutoffs)
    for cutoff in ["2024-06-30", "2024-07-01", "2024-12-31", "2025-01-01", "2025-06-30", "2025-07-01"]:
        d = pd.Timestamp(cutoff)
        window = reports[(reports.crash_date >= d - pd.Timedelta(days=7)) & (reports.crash_date <= d + pd.Timedelta(days=7))]
        if len(window):
            rate = (window.n_veh == 0).mean() * 100
            print(f"  ±7 days around {cutoff}: zero-veh rate {rate:.1f}% (n={len(window):,})")


def main() -> None:
    reports, vehicles, occupants = load_combined()
    reports = audit_half_year_files(reports, vehicles)
    analyze_collision_impact(reports)
    analyze_dates(reports)

    # MCP296500BT
    rid = "MCP296500BT"
    row = reports[reports._rid == rid]
    if len(row):
        r = row.iloc[0]
        print("\n" + "=" * 70)
        print(f"EXAMPLE {rid}")
        print("=" * 70)
        for c in ["CollisionImpact Description", "FirstHarmEvent Description", "SecondHarmEvent Description", "crash_date", "severity", "n_veh"]:
            print(f"  {c}: {r.get(c)}")


if __name__ == "__main__":
    main()
