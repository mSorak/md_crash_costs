"""
Blog analysis: share of comprehensive crash costs from pedestrian/cyclist
(non-motorist) crashes, by Maryland census tract.

Produces a stacked bar chart of tracts binned by % share, with Baltimore City
tracts highlighted in the choropleth dark red.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "blog" / "figures"

# Matches crash_cost_app/frontend/src/config.ts CHOROPLETH_RAMP
CHOROPLETH_LIGHT = (254 / 255, 232 / 255, 200 / 255)
CHOROPLETH_DARK_RED = (153 / 255, 0, 0)

BALTIMORE_CITY_GEOID = "24510"

# Left-inclusive, right-exclusive except last bucket (50%+).
BUCKET_EDGES = [0, 0.0001, 5, 10, 15, 20, 25, 30, 40, 50, 100.0001]
BUCKET_LABELS = [
    "0%",
    ">0–5%",
    "5–10%",
    "10–15%",
    "15–20%",
    "20–25%",
    "25–30%",
    "30–40%",
    "40–50%",
    "50%+",
]


def load_tract_shares() -> pd.DataFrame:
    cols = [
        "GEOID_tract",
        "GEOID_county",
        "NAMELSAD_tract",
        "Non-Motorist Crash",
        "estimated_total_comp_cost_2025usd",
    ]
    df = pd.read_csv(
        DATA / "crash_cost_eval.csv",
        usecols=cols,
        dtype={"GEOID_tract": str, "GEOID_county": str, "NAMELSAD_tract": str},
        low_memory=False,
    )
    df = df.dropna(subset=["GEOID_tract", "estimated_total_comp_cost_2025usd"])
    df["cost"] = pd.to_numeric(df["estimated_total_comp_cost_2025usd"], errors="coerce").fillna(0)
    df["is_nonmotorist"] = (
        df["Non-Motorist Crash"].astype(str).str.strip().str.lower() == "yes"
    )
    df["nm_cost"] = np.where(df["is_nonmotorist"], df["cost"], 0.0)

    tract = (
        df.groupby("GEOID_tract", as_index=False)
        .agg(
            total_comp_cost=("cost", "sum"),
            nonmotorist_comp_cost=("nm_cost", "sum"),
            GEOID_county=("GEOID_county", "first"),
            tract_name=("NAMELSAD_tract", "first"),
        )
    )
    tract = tract[tract["total_comp_cost"] > 0].copy()
    tract["pct_nonmotorist_cost"] = (
        100.0 * tract["nonmotorist_comp_cost"] / tract["total_comp_cost"]
    )
    tract["is_baltimore_city"] = tract["GEOID_county"] == BALTIMORE_CITY_GEOID
    return tract


def assign_bucket(pct: float) -> str:
    for i in range(len(BUCKET_LABELS)):
        lo, hi = BUCKET_EDGES[i], BUCKET_EDGES[i + 1]
        if lo <= pct < hi:
            return BUCKET_LABELS[i]
    return BUCKET_LABELS[-1]


def plot_stacked_histogram(tract: pd.DataFrame) -> Path:
    tract = tract.copy()
    tract["bucket"] = tract["pct_nonmotorist_cost"].map(assign_bucket)
    tract["bucket"] = pd.Categorical(tract["bucket"], categories=BUCKET_LABELS, ordered=True)

    counts = (
        tract.groupby(["bucket", "is_baltimore_city"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reindex(BUCKET_LABELS, fill_value=0)
    )
    other = counts.get(False, pd.Series(0, index=BUCKET_LABELS)).to_numpy()
    balt = counts.get(True, pd.Series(0, index=BUCKET_LABELS)).to_numpy()
    totals = other + balt

    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(BUCKET_LABELS))
    width = 0.78

    ax.bar(
        x,
        other,
        width,
        label="Other Maryland tracts",
        color=CHOROPLETH_LIGHT,
        edgecolor="#c4b8a8",
        linewidth=0.6,
        zorder=2,
    )
    ax.bar(
        x,
        balt,
        width,
        bottom=other,
        label="Baltimore City tracts",
        color=CHOROPLETH_DARK_RED,
        edgecolor="#6b0000",
        linewidth=0.6,
        zorder=3,
    )

    for i, (o, b, t) in enumerate(zip(other, balt, totals)):
        if t == 0:
            continue
        ax.text(
            i,
            t + 4,
            str(int(t)),
            ha="center",
            va="bottom",
            fontsize=9,
            color="#44403c",
        )
        if b > 0:
            share = 100.0 * b / t
            ax.text(
                i,
                o + b / 2,
                f"{share:.0f}%",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if b >= 8 else "#44403c",
                fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(BUCKET_LABELS, rotation=0)
    ax.set_xlabel(
        "Share of tract comprehensive crash costs from pedestrian/cyclist crashes",
        fontsize=11,
    )
    ax.set_ylabel("Number of census tracts", fontsize=11)
    ax.set_title(
        "Maryland census tracts by non-motorist crash cost share\n"
        "(Baltimore City highlighted)",
        fontsize=13,
        pad=12,
    )
    ax.set_ylim(0, max(totals) * 1.12 + 10)
    ax.yaxis.grid(True, linestyle="--", alpha=0.35, zorder=0)
    ax.set_axisbelow(True)

    n_tracts = len(tract)
    n_balt = int(tract["is_baltimore_city"].sum())
    balt_pct_mean = tract.loc[tract["is_baltimore_city"], "pct_nonmotorist_cost"].mean()
    md_pct_mean = tract.loc[~tract["is_baltimore_city"], "pct_nonmotorist_cost"].mean()
    note = (
        f"There are {n_tracts:,} Census Tracts in Maryland with crash costs in 2024–2025. 13.6% of those tracts are in Baltimore City."
        #f"Baltimore City: {n_balt} tracts (mean {balt_pct_mean:.1f}% non-motorist cost share); "
        #f"rest of state: mean {md_pct_mean:.1f}%."
    )
    fig.text(0.12, 0.01, note, fontsize=9, color="#57534e", wrap=True)

    legend_handles = [
        mpatches.Patch(facecolor=CHOROPLETH_LIGHT, edgecolor="#c4b8a8", label="Other Maryland tracts"),
        mpatches.Patch(facecolor=CHOROPLETH_DARK_RED, edgecolor="#6b0000", label="Baltimore City tracts"),
    ]
    ax.legend(handles=legend_handles, loc="upper right", framealpha=0.95)

    fig.tight_layout(rect=[0, 0.06, 1, 1])
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / "tract_nonmotorist_cost_share_histogram.png"
    svg = OUT / "tract_nonmotorist_cost_share_histogram.svg"
    fig.savefig(png, dpi=200, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png


def main() -> None:
    tract = load_tract_shares()
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "tract_nonmotorist_cost_share.csv"
    tract.sort_values("pct_nonmotorist_cost", ascending=False).to_csv(csv_path, index=False)

    png = plot_stacked_histogram(tract)

    balt = tract[tract["is_baltimore_city"]]
    print(f"Wrote tract table: {csv_path}")
    print(f"Wrote figure: {png}")
    print(f"Tracts: {len(tract)} | Baltimore City: {len(balt)}")
    print(f"Baltimore City mean non-motorist cost share: {balt['pct_nonmotorist_cost'].mean():.1f}%")
    print(f"Maryland (excl. Baltimore City) mean: {tract.loc[~tract['is_baltimore_city'], 'pct_nonmotorist_cost'].mean():.1f}%")
    print("\nTop 10 Baltimore City tracts by non-motorist cost share:")
    top = balt.nlargest(10, "pct_nonmotorist_cost")[
        ["GEOID_tract", "tract_name", "pct_nonmotorist_cost", "total_comp_cost", "nonmotorist_comp_cost"]
    ]
    print(top.to_string(index=False))


if __name__ == "__main__":
    main()
