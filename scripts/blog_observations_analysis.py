"""County-level metrics for blog observations (rural + general trends)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

METRO_COUNTIES = {
    "Montgomery",
    "Prince George's",
    "Frederick",
    "Charles",
    "Calvert",
    "Howard",
    "Anne Arundel",
    "Baltimore",
    "Harford",
    "Baltimore City",
    "Carroll",
}
EASTERN_SHORE = {
    "Kent",
    "Queen Anne's",
    "Talbot",
    "Caroline",
    "Dorchester",
    "Wicomico",
    "Somerset",
    "Worcester",
}
WESTERN_MD = {"Allegany", "Garrett", "Washington"}


def load_counties() -> pd.DataFrame:
    df = pd.read_csv(DATA / "geo_summaries" / "merged_county.csv")
    df["GEOID"] = df["TL_GEO_ID"].astype(str)
    df["pop"] = pd.to_numeric(df["AUO6E001"], errors="coerce")
    df["total_cost"] = pd.to_numeric(
        df["crash_sum_estimated_total_comp_cost_2025usd"], errors="coerce"
    )
    df["n_crashes"] = pd.to_numeric(df["crash_n_crashes"], errors="coerce")
    df["n_fatal"] = pd.to_numeric(df["crash_n_fatal"], errors="coerce")
    df["fatalities"] = (
        pd.to_numeric(df["crash_motorist_fatalities"], errors="coerce").fillna(0)
        + pd.to_numeric(df["crash_nonmotorist_fatalities"], errors="coerce").fillna(0)
    )
    df["qaly_cost"] = pd.to_numeric(
        df["crash_sum_estimated_QALYs_comp_cost_2025usd"], errors="coerce"
    )
    df["econ_cost"] = pd.to_numeric(
        df["crash_sum_estimated_Total_Economic_comp_cost_2025usd"], errors="coerce"
    )
    df["med_cost"] = pd.to_numeric(
        df["crash_sum_estimated_Medical_comp_cost_2025usd"], errors="coerce"
    )
    df["prop_cost"] = pd.to_numeric(
        df["crash_sum_estimated_PropDamage_comp_cost_2025usd"], errors="coerce"
    )
    df["vpp"] = pd.to_numeric(df["census_est_vehicles_per_person_mid"], errors="coerce")

    inj_cols = [
        "crash_motorist_injuries_police_severity_2_mais4",
        "crash_motorist_injuries_police_severity_3_mais2",
        "crash_motorist_injuries_police_severity_4_mais1",
        "crash_nonmotorist_injuries_police_severity_2_mais4",
        "crash_nonmotorist_injuries_police_severity_3_mais2",
        "crash_nonmotorist_injuries_police_severity_4_mais1",
    ]
    df["injuries"] = sum(
        pd.to_numeric(df[c], errors="coerce").fillna(0) for c in inj_cols
    )

    eval_df = pd.read_csv(
        DATA / "crash_cost_eval.csv",
        usecols=[
            "GEOID_county",
            "Non-Motorist Crash",
            "Motorcycle Crash",
            "ImpairedCrash",
            "Crash Severity",
            "estimated_total_comp_cost_2025usd",
            "Crashhour",
        ],
        dtype={"GEOID_county": str},
        low_memory=False,
    )
    eval_df["nm"] = (
        eval_df["Non-Motorist Crash"].astype(str).str.strip().str.lower() == "yes"
    )
    eval_df["moto"] = (
        eval_df["Motorcycle Crash"].astype(str).str.strip().str.lower() == "yes"
    )
    eval_df["impaired"] = (
        eval_df["ImpairedCrash"].astype(str).str.strip().str.lower() == "yes"
    )
    eval_df["cost"] = pd.to_numeric(
        eval_df["estimated_total_comp_cost_2025usd"], errors="coerce"
    ).fillna(0)
    eval_df["is_fatal"] = pd.to_numeric(eval_df["Crash Severity"], errors="coerce") == 1

    for col, src in [
        ("pct_crashes_nm", "nm"),
        ("pct_crashes_moto", "moto"),
        ("pct_crashes_impaired", "impaired"),
    ]:
        df[col] = df["GEOID"].map(eval_df.groupby("GEOID_county")[src].mean() * 100)

    fatal_cost = eval_df.groupby("GEOID_county").apply(
        lambda g: 100 * g.loc[g["is_fatal"], "cost"].sum() / g["cost"].sum()
        if g["cost"].sum() > 0
        else np.nan,
        include_groups=False,
    )
    df["pct_cost_fatal"] = df["GEOID"].map(fatal_cost)

    df["cost_pc"] = df["total_cost"] / df["pop"]
    df["fatal_per_10k"] = 10000 * df["fatalities"] / df["pop"]
    df["inj_per_10k"] = 10000 * df["injuries"] / df["pop"]
    df["crashes_per_10k"] = 10000 * df["n_crashes"] / df["pop"]
    df["pct_fatal_crashes"] = 100 * df["n_fatal"] / df["n_crashes"]
    df["cost_per_crash"] = df["total_cost"] / df["n_crashes"]
    df["qaly_share"] = 100 * df["qaly_cost"] / df["total_cost"]
    df["prop_share"] = 100 * df["prop_cost"] / df["total_cost"]
    df["region"] = np.where(df["COUNTY"].isin(METRO_COUNTIES), "Metro", "Non-metro")

    return df, eval_df


def weighted(sub: pd.DataFrame, num: str, denom: str = "pop") -> float:
    return sub[num].sum() / sub[denom].sum()


def main() -> None:
    df, eval_df = load_counties()

    md_cost_pc = weighted(df, "total_cost")
    print(f"Maryland avg comprehensive cost per capita: ${md_cost_pc:,.0f} (${md_cost_pc/1000:.1f}k)\n")

    print("=== TOP 10 counties by per-capita comprehensive cost ===")
    for _, r in df.nlargest(10, "cost_pc").iterrows():
        print(
            f"  {r['COUNTY']:20s} ${r['cost_pc']/1000:5.1f}k | "
            f"fatal/10k={r['fatal_per_10k']:.2f} | inj/10k={r['inj_per_10k']:.1f} | "
            f"$/crash=${r['cost_per_crash']:,.0f} | QALY={r['qaly_share']:.0f}% | "
            f"NM={r['pct_crashes_nm']:.1f}% | vpp={r['vpp']:.2f}"
        )

    print("\n=== METRO vs NON-METRO ===")
    for label, mask in [
        ("Metro", df["region"] == "Metro"),
        ("Non-metro", df["region"] == "Non-metro"),
    ]:
        sub = df[mask]
        print(
            f"{label} ({len(sub)} counties): "
            f"cost_pc=${weighted(sub,'total_cost')/1000:.1f}k, "
            f"fatal/10k={weighted(sub,'fatalities')*10000:.2f}, "
            f"inj/10k={weighted(sub,'injuries')*10000:.1f}, "
            f"$/crash=${sub['total_cost'].sum()/sub['n_crashes'].sum():,.0f}, "
            f"QALY share={sub['qaly_cost'].sum()/sub['total_cost'].sum()*100:.0f}%, "
            f"NM crash%={eval_df[eval_df['GEOID_county'].isin(sub['GEOID'])]['nm'].mean()*100:.1f}%"
        )

    print("\n=== NON-METRO counties (rural / small-town Maryland) ===")
    for _, r in df[df["region"] == "Non-metro"].sort_values("cost_pc", ascending=False).iterrows():
        print(
            f"  {r['COUNTY']:18s} pop={r['pop']:6,.0f} "
            f"${r['cost_pc']/1000:5.1f}k fatal/10k={r['fatal_per_10k']:.2f} "
            f"$/crash=${r['cost_per_crash']:,.0f} QALY={r['qaly_share']:.0f}% "
            f"moto={r['pct_crashes_moto']:.1f}% impaired={r['pct_crashes_impaired']:.1f}%"
        )

    print("\n=== EASTERN SHORE ===")
    shore = df[df["COUNTY"].isin(EASTERN_SHORE)].sort_values("cost_pc", ascending=False)
    print(f"Shore mean cost_pc: ${shore['cost_pc'].mean()/1000:.1f}k vs state ${md_cost_pc/1000:.1f}k")
    print(shore[["COUNTY", "cost_pc", "fatal_per_10k", "cost_per_crash", "qaly_share"]].to_string(index=False))

    print("\n=== WESTERN MARYLAND ===")
    print(df[df["COUNTY"].isin(WESTERN_MD)].sort_values("cost_pc", ascending=False).to_string(index=False))

    print("\n=== CORRELATIONS with per-capita cost ===")
    metrics = [
        "cost_pc", "fatal_per_10k", "inj_per_10k", "cost_per_crash",
        "qaly_share", "pct_crashes_nm", "pct_crashes_moto", "pct_crashes_impaired",
        "vpp", "crashes_per_10k", "pop",
    ]
    print(df[metrics].corr()["cost_pc"].sort_values(ascending=False).to_string())

    print("\n=== STATEWIDE COMPOSITION ===")
    total_cost = eval_df["cost"].sum()
    fatal_cost = eval_df.loc[eval_df["is_fatal"], "cost"].sum()
    nm_cost = eval_df.loc[eval_df["nm"], "cost"].sum()
    print(f"Crashes: {len(eval_df):,}")
    print(f"Fatal crashes: {eval_df['is_fatal'].sum():,} ({100*eval_df['is_fatal'].mean():.2f}%)")
    print(f"Fatal crash share of costs: {100*fatal_cost/total_cost:.1f}%")
    print(f"Non-motorist crashes: {100*eval_df['nm'].mean():.1f}% of crashes, {100*nm_cost/total_cost:.1f}% of costs")
    print(f"Motorcycle: {100*eval_df['moto'].mean():.1f}% of crashes")
    print(f"Impaired: {100*eval_df['impaired'].mean():.1f}% of crashes")

    print("\n=== OTHER NOTABLE COUNTIES ===")
    print("Highest QALY share:")
    print(df.nlargest(5, "qaly_share")[["COUNTY", "qaly_share", "fatal_per_10k", "cost_pc"]].to_string(index=False))
    print("Highest cost per crash:")
    print(df.nlargest(5, "cost_per_crash")[["COUNTY", "cost_per_crash", "n_crashes", "pct_fatal_crashes"]].to_string(index=False))
    print("Highest motorcycle share:")
    print(df.nlargest(5, "pct_crashes_moto")[["COUNTY", "pct_crashes_moto", "cost_pc"]].to_string(index=False))

    # Low-pop high cost
    rural_high = df[(df["pop"] < 80_000) & (df["cost_pc"] > md_cost_pc)].sort_values("cost_pc", ascending=False)
    print(f"\nCounties under 80k pop with above-state avg cost_pc: {len(rural_high)}")
    print(rural_high[["COUNTY", "pop", "cost_pc", "fatal_per_10k", "cost_per_crash"]].to_string(index=False))


if __name__ == "__main__":
    main()
