"""
Stage 4 — EDA and Visualisation
Indian Water Quality Analytics Project

DISCLOSURES (preserved per project rules):
  1. 'DO_assumed' is an UNVERIFIED assumed Dissolved Oxygen interpretation of
     the column labelled 'Dissolved' in the raw dataset. This has not been
     independently confirmed from the dataset source.
  2. WQI is a MODIFIED/CUSTOM index (Modified Weighted Arithmetic WQI based on
     Brown 1970), adapted to Indian BIS IS:10500-2012 standards. It is NOT a
     standard government or globally recognised index.
  3. WQI uses (Min + Max) / 2 as a range-midpoint approximation, NOT a true
     annual mean. Actual annual means are not available in this dataset.

Generates 11 charts (V01–V11) and saves them to report_images/.
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")

# ── paths ──────────────────────────────────────────────────────────────────────
OUT_DIR = "report_images"
os.makedirs(OUT_DIR, exist_ok=True)

WQI_PATH  = "data/processed/wqi_scores.csv"
PROC_PATH = "data/processed/water_quality_processed.csv"

wqi = pd.read_csv(WQI_PATH)
df  = pd.read_csv(PROC_PATH)

# Rows where WQI was actually computed
wqi_valid = wqi[wqi["WQI_applicable"] == 1].copy()

# ── colour palette (consistent across charts) ─────────────────────────────────
CAT_ORDER  = ["Good", "Poor", "Very Poor", "Unsuitable for Drinking"]
CAT_COLORS = {
    "Good":                    "#2ecc71",
    "Poor":                    "#f39c12",
    "Very Poor":               "#e74c3c",
    "Unsuitable for Drinking": "#8e44ad",
}

STYLE = "seaborn-v0_8-whitegrid"
plt.rcParams.update({
    "font.family":   "DejaVu Sans",
    "axes.titlesize":  13,
    "axes.labelsize":  11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.dpi":      150,
})

FOOTNOTE_DO  = ("* 'Dissolved Oxygen (assumed)' is an UNVERIFIED interpretation of the 'Dissolved' column "
                "in the raw dataset.")
FOOTNOTE_WQI = ("† WQI is a modified custom index (Brown 1970, BIS IS:10500-2012). "
                "Values are (Min+Max)/2 midpoint approximations, not true annual means.")


def save(fig, filename):
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  Saved: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# V01 — WQI Distribution (histogram + KDE)
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V01 — WQI Distribution …")
scores = wqi_valid["WQI_score"].dropna()

fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(scores, bins=25, color="#3b82d4", edgecolor="white", alpha=0.75,
        density=True, label="Histogram (density)")

kde_x = np.linspace(scores.min() - 5, scores.max() + 10, 400)
kde   = stats.gaussian_kde(scores)
ax.plot(kde_x, kde(kde_x), color="#c0392b", linewidth=2, label="KDE")

ax.axvline(scores.mean(),   color="#2c3e50", linestyle="--", linewidth=1.4,
           label=f"Mean = {scores.mean():.1f}")
ax.axvline(scores.median(), color="#7c5cd8", linestyle=":",  linewidth=1.4,
           label=f"Median = {scores.median():.1f}")

# Category boundary lines (from project plan)
for boundary, label in [(50, "Good/Poor"), (75, "Poor/V.Poor"), (100, "V.Poor/Unsuitable")]:
    ax.axvline(boundary, color="grey", linestyle="-.", linewidth=0.9, alpha=0.7)
    ax.text(boundary + 0.5, ax.get_ylim()[1] * 0.01, label, fontsize=7,
            color="grey", rotation=90, va="bottom")

ax.set_xlabel("WQI Score")
ax.set_ylabel("Density")
ax.set_title("V01 — Distribution of WQI Scores\n(n = 160 stations with computable WQI)")
ax.legend(fontsize=9)
fig.text(0.01, -0.04, FOOTNOTE_WQI, fontsize=7, color="#57606a", wrap=True)
save(fig, "V01_wqi_distribution.png")


# ══════════════════════════════════════════════════════════════════════════════
# V02 — WQI Category Counts (bar chart)
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V02 — WQI Category Counts …")
cat_counts = wqi_valid["WQI_category"].value_counts().reindex(CAT_ORDER).dropna()

fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(cat_counts.index,
              cat_counts.values,
              color=[CAT_COLORS[c] for c in cat_counts.index],
              edgecolor="white", linewidth=0.8)

for bar, val in zip(bars, cat_counts.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
            str(val), ha="center", va="bottom", fontsize=10, fontweight="bold")

ax.set_xlabel("WQI Category")
ax.set_ylabel("Number of Stations")
ax.set_title("V02 — WQI Category Distribution\n(n = 160 stations with computable WQI)")
ax.set_ylim(0, cat_counts.max() * 1.15)
ax.tick_params(axis="x", labelsize=9)
fig.text(0.01, -0.04, FOOTNOTE_WQI, fontsize=7, color="#57606a", wrap=True)
save(fig, "V02_wqi_category_counts.png")


# ══════════════════════════════════════════════════════════════════════════════
# V03 — WQI by State with 95 % CI
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V03 — WQI by State …")
state_grp = (wqi_valid.dropna(subset=["WQI_score"])
             .groupby("State_Name")["WQI_score"])

state_stats = state_grp.agg(
    mean="mean", std="std", count="count"
).reset_index()
state_stats["se"]    = state_stats["std"] / np.sqrt(state_stats["count"])
# t-critical for 95 % CI; use t=1.96 for n>30, exact for small n
state_stats["ci95"] = state_stats.apply(
    lambda r: stats.t.ppf(0.975, max(r["count"] - 1, 1)) * r["se"], axis=1
)
state_stats = state_stats.sort_values("mean", ascending=False)

fig, ax = plt.subplots(figsize=(10, 6))
colors = ["#e74c3c" if m > 75 else "#f39c12" if m > 50 else "#2ecc71"
          for m in state_stats["mean"]]
ax.bar(state_stats["State_Name"], state_stats["mean"],
       color=colors, edgecolor="white", linewidth=0.7, label="Mean WQI")
ax.errorbar(state_stats["State_Name"], state_stats["mean"],
            yerr=state_stats["ci95"], fmt="none",
            ecolor="#2c3e50", elinewidth=1.5, capsize=4, capthick=1.5,
            label="95% CI")

ax.axhline(50,  color="#2ecc71", linestyle="--", linewidth=0.9, alpha=0.7)
ax.axhline(75,  color="#f39c12", linestyle="--", linewidth=0.9, alpha=0.7)
ax.axhline(100, color="#e74c3c", linestyle="--", linewidth=0.9, alpha=0.7)

for i, row in state_stats.reset_index(drop=True).iterrows():
    ax.text(i, row["mean"] + row["ci95"] + 0.8,
            f'n={int(row["count"])}', ha="center", fontsize=7, color="#57606a")

ax.set_xlabel("State")
ax.set_ylabel("Mean WQI Score")
ax.set_title("V03 — Mean WQI Score by State (with 95% Confidence Intervals)\n"
             "Dashed lines: 50 (Good/Poor), 75 (Poor/Very Poor), 100 (Very Poor/Unsuitable)")
ax.legend(fontsize=9)
plt.xticks(rotation=35, ha="right")
fig.text(0.01, -0.06, FOOTNOTE_WQI, fontsize=7, color="#57606a", wrap=True)
fig.tight_layout()
save(fig, "V03_wqi_by_state.png")


# ══════════════════════════════════════════════════════════════════════════════
# V04 — WQI by Water Body Type (box plot)
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V04 — WQI by Water Body Type …")
wb_scores = wqi_valid.dropna(subset=["WQI_score"])
wb_order  = (wb_scores.groupby("Water_Body_Type")["WQI_score"]
             .median().sort_values(ascending=False).index.tolist())

fig, ax = plt.subplots(figsize=(11, 6))
sns.boxplot(data=wb_scores, x="Water_Body_Type", y="WQI_score",
            order=wb_order, palette="Set2", width=0.55,
            flierprops=dict(marker="o", markersize=4, alpha=0.5),
            ax=ax)

# Annotate n per group
for i, wb in enumerate(wb_order):
    n = (wb_scores["Water_Body_Type"] == wb).sum()
    ax.text(i, wb_scores["WQI_score"].max() + 2, f"n={n}",
            ha="center", fontsize=7.5, color="#57606a")

ax.axhline(50,  color="#2ecc71", linestyle="--", linewidth=0.9, alpha=0.7)
ax.axhline(75,  color="#f39c12", linestyle="--", linewidth=0.9, alpha=0.7)
ax.axhline(100, color="#e74c3c", linestyle="--", linewidth=0.9, alpha=0.7)

ax.set_xlabel("Water Body Type")
ax.set_ylabel("WQI Score")
ax.set_title("V04 — WQI Score Distribution by Water Body Type\n"
             "Dashed lines: 50 (Good/Poor), 75 (Poor/Very Poor), 100 (Very Poor/Unsuitable)")
plt.xticks(rotation=25, ha="right")
fig.text(0.01, -0.06, FOOTNOTE_WQI, fontsize=7, color="#57606a", wrap=True)
fig.tight_layout()
save(fig, "V04_wqi_by_water_body_type.png")


# ══════════════════════════════════════════════════════════════════════════════
# V05 — Parameter Correlation Heatmap
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V05 — Parameter Correlation Heatmap …")
corr_cols = {
    "DO (assumed)":    "DO_assumed_mean",
    "pH":              "pH_mean",
    "BOD":             "BOD_mean",
    "Conductivity":    "Conductivity_mean",
    "Nitrate-N":       "NitrateN_mean",
    "Fecal Coliform":  "FC_mean",
    "Total Coliform":  "TC_mean",
    "WQI Score":       "WQI_score",
}
corr_data = wqi_valid[list(corr_cols.values())].copy()
corr_data.columns = list(corr_cols.keys())
corr_matrix = corr_data.corr(method="spearman")

mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f",
            cmap="RdYlGn_r", vmin=-1, vmax=1,
            linewidths=0.5, linecolor="white",
            annot_kws={"size": 9}, ax=ax)
ax.set_title("V05 — Spearman Correlation Matrix of Water Quality Parameters\n"
             "(lower triangle shown; WQI included for reference)")
plt.xticks(rotation=30, ha="right")
plt.yticks(rotation=0)
fig.text(0.01, -0.04, FOOTNOTE_DO + "  " + FOOTNOTE_WQI,
         fontsize=7, color="#57606a", wrap=True)
fig.tight_layout()
save(fig, "V05_parameter_correlation.png")


# ══════════════════════════════════════════════════════════════════════════════
# V06 — Assumed DO vs BOD, coloured by WQI category
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V06 — DO (assumed) vs BOD …")
scatter_data = wqi_valid.dropna(subset=["WQI_score", "WQI_category",
                                         "DO_assumed_mean", "BOD_mean"])

fig, ax = plt.subplots(figsize=(8, 6))
for cat in CAT_ORDER:
    sub = scatter_data[scatter_data["WQI_category"] == cat]
    ax.scatter(sub["DO_assumed_mean"], sub["BOD_mean"],
               c=CAT_COLORS[cat], label=cat, alpha=0.75,
               edgecolors="white", linewidth=0.4, s=60, zorder=3)

ax.set_xlabel("Dissolved Oxygen — assumed* (mg/L)")
ax.set_ylabel("BOD (mg/L)  [midpoint approximation†]")
ax.set_title("V06 — Assumed Dissolved Oxygen vs BOD\nColoured by WQI Category")
ax.legend(title="WQI Category", fontsize=9, title_fontsize=9)
fig.text(0.01, -0.06, FOOTNOTE_DO + "\n" + FOOTNOTE_WQI,
         fontsize=7, color="#57606a", wrap=True)
fig.tight_layout()
save(fig, "V06_do_vs_bod.png")


# ══════════════════════════════════════════════════════════════════════════════
# V07 — Fecal Coliform vs Total Coliform (log–log scale)
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V07 — FC vs TC (log scale) …")
fc_tc = wqi_valid.dropna(subset=["FC_mean", "TC_mean"]).copy()
fc_tc = fc_tc[fc_tc["FC_mean"] > 0]
fc_tc = fc_tc[fc_tc["TC_mean"] > 0]

# Map WQI_category to color; NaN rows get grey
colors_v07 = [CAT_COLORS.get(c, "#aaaaaa") for c in fc_tc["WQI_category"]]

fig, ax = plt.subplots(figsize=(8, 6))
sc = ax.scatter(fc_tc["FC_mean"], fc_tc["TC_mean"],
                c=colors_v07, alpha=0.72,
                edgecolors="white", linewidth=0.4, s=55)

# 1:1 reference line
lims = [min(fc_tc["FC_mean"].min(), fc_tc["TC_mean"].min()),
        max(fc_tc["FC_mean"].max(), fc_tc["TC_mean"].max())]
ax.plot(lims, lims, "k--", linewidth=1.0, alpha=0.5, label="1 : 1 line")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Fecal Coliform — mean (MPN/100 mL)  [log scale]")
ax.set_ylabel("Total Coliform — mean (MPN/100 mL)  [log scale]")
ax.set_title("V07 — Fecal Coliform vs Total Coliform\n(logarithmic axes, midpoint approximations†)")

# Custom legend patches
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=CAT_COLORS[c], label=c)
                   for c in CAT_ORDER if c in fc_tc["WQI_category"].values]
legend_elements.append(Patch(facecolor="#aaaaaa", label="WQI not computed"))
legend_elements.append(plt.Line2D([0], [0], color="black", linestyle="--",
                                   linewidth=1, label="1:1 line"))
ax.legend(handles=legend_elements, title="WQI Category", fontsize=8, title_fontsize=8)

fig.text(0.01, -0.04, FOOTNOTE_WQI, fontsize=7, color="#57606a", wrap=True)
fig.tight_layout()
save(fig, "V07_fc_vs_tc.png")


# ══════════════════════════════════════════════════════════════════════════════
# V08 — Missing Value Heatmap (raw parameter columns)
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V08 — Missing Value Heatmap …")
param_cols = [
    "Temp_Min", "Temp_Max",
    "DO_assumed_Min", "DO_assumed_Max",
    "pH_Min", "pH_Max",
    "Conductivity_Min", "Conductivity_Max",
    "BOD_Min", "BOD_Max",
    "NitrateN_Min", "NitrateN_Max",
    "FC_Min", "FC_Max",
    "TC_Min", "TC_Max",
    "Fecal_unknown_Min", "Fecal_unknown_Max",
]

rename_map = {
    "Temp_Min": "Temp Min", "Temp_Max": "Temp Max",
    "DO_assumed_Min": "DO* Min", "DO_assumed_Max": "DO* Max",
    "pH_Min": "pH Min", "pH_Max": "pH Max",
    "Conductivity_Min": "Cond Min", "Conductivity_Max": "Cond Max",
    "BOD_Min": "BOD Min", "BOD_Max": "BOD Max",
    "NitrateN_Min": "NitrateN Min", "NitrateN_Max": "NitrateN Max",
    "FC_Min": "FC Min", "FC_Max": "FC Max",
    "TC_Min": "TC Min", "TC_Max": "TC Max",
    "Fecal_unknown_Min": "Fecal? Min", "Fecal_unknown_Max": "Fecal? Max",
}

miss_df = df[param_cols].rename(columns=rename_map)
miss_pct = miss_df.isnull().mean() * 100
miss_matrix = miss_df.isnull().astype(int)

fig, axes = plt.subplots(1, 2, figsize=(13, 6),
                          gridspec_kw={"width_ratios": [3, 1]})

# Left: row-level missingness pattern (first 60 rows for readability)
sample = miss_matrix.head(60)
sns.heatmap(sample, cmap=["#f7f8fa", "#e74c3c"],
            cbar=False, linewidths=0.3, linecolor="#e5e7eb",
            ax=axes[0], xticklabels=True, yticklabels=False)
axes[0].set_title("Row-level Missingness Pattern (first 60 rows)")
axes[0].set_xlabel("Parameter")
axes[0].set_ylabel("Station-Year rows")
axes[0].tick_params(axis="x", rotation=45, labelsize=8)

# Right: % missing bar
colors_miss = ["#e74c3c" if p > 0 else "#2ecc71" for p in miss_pct.values]
axes[1].barh(miss_pct.index, miss_pct.values, color=colors_miss, edgecolor="white")
for i, v in enumerate(miss_pct.values):
    if v > 0:
        axes[1].text(v + 0.5, i, f"{v:.0f}%", va="center", fontsize=8)
axes[1].set_xlim(0, 120)
axes[1].set_xlabel("% Missing (all 194 rows)")
axes[1].set_title("% Missing per Column")
axes[1].tick_params(axis="y", labelsize=8)

fig.suptitle("V08 — Missing Value Analysis (Processed Dataset, n=194 station-years)",
             fontsize=12, y=1.01)
fig.text(0.01, -0.04, "* DO (assumed) = UNVERIFIED interpretation of 'Dissolved' column.",
         fontsize=7, color="#57606a")
fig.tight_layout()
save(fig, "V08_missing_values.png")


# ══════════════════════════════════════════════════════════════════════════════
# V09 — Temporal Trend for the 26 multi-year stations
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V09 — Temporal Trend (multi-year stations) …")

stn_year_counts = wqi.groupby("STN_code")["Year"].nunique()
multi_stns = stn_year_counts[stn_year_counts > 1].index.tolist()
multi_data = wqi[wqi["STN_code"].isin(multi_stns)].copy()

fig, axes = plt.subplots(1, 2, figsize=(13, 6))

# ── Left: individual station lines (grey) + aggregate trend ──
ax_l = axes[0]
year_agg = multi_data.groupby("Year")["WQI_score"].agg(["mean", "std", "count"]).reset_index()
year_agg["ci"] = year_agg.apply(
    lambda r: stats.t.ppf(0.975, max(r["count"] - 1, 1)) * r["std"] / np.sqrt(r["count"]),
    axis=1
)

for stn in multi_stns:
    stn_sub = multi_data[multi_data["STN_code"] == stn].dropna(subset=["WQI_score"])
    if len(stn_sub) < 2:
        continue
    ax_l.plot(stn_sub["Year"], stn_sub["WQI_score"],
              color="grey", alpha=0.3, linewidth=1.0, marker="o", markersize=3)

ax_l.plot(year_agg["Year"], year_agg["mean"],
          color="#e74c3c", linewidth=2.5, marker="D", markersize=7,
          label="Mean WQI (multi-year stations)", zorder=5)
ax_l.fill_between(year_agg["Year"],
                  year_agg["mean"] - year_agg["ci"],
                  year_agg["mean"] + year_agg["ci"],
                  alpha=0.2, color="#e74c3c", label="95% CI")

ax_l.set_xlabel("Year")
ax_l.set_ylabel("WQI Score")
ax_l.set_title("Individual Station Trends\n(grey lines) + Mean ± 95% CI (red)")
ax_l.legend(fontsize=8)
ax_l.set_xticks(sorted(multi_data["Year"].unique()))

# ── Right: year-wise category composition ──
ax_r = axes[1]
year_cat = (multi_data.dropna(subset=["WQI_category"])
            .groupby(["Year", "WQI_category"])
            .size().unstack(fill_value=0))
year_cat = year_cat.reindex(columns=CAT_ORDER, fill_value=0)
bottom = np.zeros(len(year_cat))
for cat in CAT_ORDER:
    if cat in year_cat.columns:
        vals = year_cat[cat].values
        ax_r.bar(year_cat.index, vals, bottom=bottom,
                 color=CAT_COLORS[cat], label=cat, edgecolor="white", width=0.5)
        bottom += vals
ax_r.set_xlabel("Year")
ax_r.set_ylabel("Number of Multi-year Stations")
ax_r.set_title("WQI Category Composition\n(multi-year stations by year)")
ax_r.legend(title="Category", fontsize=8, title_fontsize=8)
ax_r.set_xticks(sorted(multi_data["Year"].unique()))

fig.suptitle("V09 — Temporal WQI Trends: 26 Multi-Year Monitoring Stations (2021–2023)",
             fontsize=12, y=1.02)
fig.text(0.01, -0.04, FOOTNOTE_WQI, fontsize=7, color="#57606a", wrap=True)
fig.tight_layout()
save(fig, "V09_temporal_trend.png")


# ══════════════════════════════════════════════════════════════════════════════
# V10 — Top 10 Most Polluted Stations
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V10 — Top 10 Most Polluted Stations …")
top10_polluted = (wqi_valid.dropna(subset=["WQI_score"])
                  .nlargest(10, "WQI_score")
                  .sort_values("WQI_score", ascending=True))

labels = [f"{row['Monitoring_Location'][:40]}\n({row['State_Name']}, {int(row['Year'])})"
          for _, row in top10_polluted.iterrows()]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(labels, top10_polluted["WQI_score"],
               color=[CAT_COLORS.get(c, "#aaaaaa")
                      for c in top10_polluted["WQI_category"]],
               edgecolor="white", height=0.65)

for bar, val, cat in zip(bars, top10_polluted["WQI_score"], top10_polluted["WQI_category"]):
    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}  ({cat})", va="center", fontsize=8.5)

ax.set_xlabel("WQI Score (higher = more polluted)")
ax.set_title("V10 — Top 10 Most Polluted Monitoring Stations\n"
             "(Ranked by Modified Custom WQI Score†, higher score = worse water quality)")
ax.set_xlim(0, top10_polluted["WQI_score"].max() * 1.35)
ax.axvline(100, color="#8e44ad", linestyle="--", linewidth=1.0, alpha=0.8,
           label="Score = 100 (Unsuitable boundary)")
ax.legend(fontsize=8)
fig.text(0.01, -0.04, FOOTNOTE_WQI, fontsize=7, color="#57606a", wrap=True)
fig.tight_layout()
save(fig, "V10_top_10_polluted_stations.png")


# ══════════════════════════════════════════════════════════════════════════════
# V11 — Top 10 Cleanest Stations
# ══════════════════════════════════════════════════════════════════════════════
print("Generating V11 — Top 10 Cleanest Stations …")
top10_clean = (wqi_valid.dropna(subset=["WQI_score"])
               .nsmallest(10, "WQI_score")
               .sort_values("WQI_score", ascending=False))

labels_clean = [f"{row['Monitoring_Location'][:40]}\n({row['State_Name']}, {int(row['Year'])})"
                for _, row in top10_clean.iterrows()]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(labels_clean, top10_clean["WQI_score"],
               color=[CAT_COLORS.get(c, "#aaaaaa")
                      for c in top10_clean["WQI_category"]],
               edgecolor="white", height=0.65)

for bar, val, cat in zip(bars, top10_clean["WQI_score"], top10_clean["WQI_category"]):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}  ({cat})", va="center", fontsize=8.5)

ax.set_xlabel("WQI Score (lower = cleaner)")
ax.set_title("V11 — Top 10 Cleanest Monitoring Stations\n"
             "(Ranked by Modified Custom WQI Score†, lower score = better water quality)")
ax.set_xlim(0, top10_clean["WQI_score"].max() * 1.35)
ax.axvline(50, color="#2ecc71", linestyle="--", linewidth=1.0, alpha=0.8,
           label="Score = 50 (Good boundary)")
ax.legend(fontsize=8)
fig.text(0.01, -0.04, FOOTNOTE_WQI, fontsize=7, color="#57606a", wrap=True)
fig.tight_layout()
save(fig, "V11_top_10_cleanest_stations.png")


# ══════════════════════════════════════════════════════════════════════════════
# EDA FINDINGS SUMMARY (printed to stdout)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("KEY EDA FINDINGS")
print("="*65)

scores_all = wqi_valid["WQI_score"].dropna()
print(f"\n1. WQI score range: {scores_all.min():.2f} – {scores_all.max():.2f}")
print(f"   Mean = {scores_all.mean():.2f}, Median = {scores_all.median():.2f}, "
      f"SD = {scores_all.std():.2f}")

cat_pct = wqi_valid["WQI_category"].value_counts(normalize=True) * 100
print(f"\n2. Category split (n=160):")
for cat in CAT_ORDER:
    if cat in cat_pct.index:
        print(f"   {cat:<30} {cat_counts.get(cat, 0):3d} stations "
              f"({cat_pct.get(cat, 0):.1f}%)")

worst_state = wqi_valid.dropna(subset=["WQI_score"]).groupby("State_Name")["WQI_score"].mean().idxmax()
best_state  = wqi_valid.dropna(subset=["WQI_score"]).groupby("State_Name")["WQI_score"].mean().idxmin()
print(f"\n3. Worst mean WQI state : {worst_state} "
      f"({wqi_valid[wqi_valid['State_Name']==worst_state]['WQI_score'].mean():.2f})")
print(f"   Best  mean WQI state : {best_state}  "
      f"({wqi_valid[wqi_valid['State_Name']==best_state]['WQI_score'].mean():.2f})")

worst_wb = wqi_valid.dropna(subset=["WQI_score"]).groupby("Water_Body_Type")["WQI_score"].median().idxmax()
best_wb  = wqi_valid.dropna(subset=["WQI_score"]).groupby("Water_Body_Type")["WQI_score"].median().idxmin()
print(f"\n4. Water body with highest median WQI: {worst_wb}")
print(f"   Water body with lowest  median WQI: {best_wb}")

corr_bod_do = wqi_valid[["DO_assumed_mean","BOD_mean"]].corr(method="spearman").iloc[0,1]
print(f"\n5. Spearman r (DO assumed vs BOD) = {corr_bod_do:.3f}")

fc_tc_corr = wqi_valid[["FC_mean","TC_mean"]].corr(method="spearman").iloc[0,1]
print(f"   Spearman r (FC vs TC)           = {fc_tc_corr:.3f}")

fc_range = wqi_valid["FC_mean"]
print(f"\n6. Fecal Coliform range: {fc_range.min():.1f} – {fc_range.max():,.0f} MPN/100 mL")
print(f"   (6-order-of-magnitude spread, necessitating log scale)")

multi_agg = multi_data.groupby("Year")["WQI_score"].mean()
years_sorted = sorted(multi_agg.index)
if len(years_sorted) >= 2:
    delta = multi_agg[years_sorted[-1]] - multi_agg[years_sorted[0]]
    print(f"\n7. Multi-year stations mean WQI: "
          f"{multi_agg[years_sorted[0]]:.2f} ({years_sorted[0]}) -> "
          f"{multi_agg[years_sorted[-1]]:.2f} ({years_sorted[-1]})  "
          f"Delta = {delta:+.2f}")

worst_stn = wqi_valid.dropna(subset=["WQI_score"]).nlargest(1,"WQI_score").iloc[0]
best_stn  = wqi_valid.dropna(subset=["WQI_score"]).nsmallest(1,"WQI_score").iloc[0]
print(f"\n8. Single highest WQI: {worst_stn['Monitoring_Location']} "
      f"({worst_stn['State_Name']}, {int(worst_stn['Year'])}) "
      f"= {worst_stn['WQI_score']:.2f} [{worst_stn['WQI_category']}]")
print(f"   Single lowest  WQI: {best_stn['Monitoring_Location']} "
      f"({best_stn['State_Name']}, {int(best_stn['Year'])}) "
      f"= {best_stn['WQI_score']:.2f} [{best_stn['WQI_category']}]")

not_computed = (wqi["WQI_applicable"] == 0).sum()
print(f"\n9. Rows where WQI could not be computed: {not_computed} / 194 "
      f"({not_computed/194*100:.1f}%)")
print(f"   Primary reason: missing FC/TC coliform data (BEACH/MARINE/SEA sites)")

miss_fecal_unk = df["Fecal_unknown_Min"].isna().sum()
print(f"\n10. 'Fecal_unknown' column missingness: "
      f"Min={miss_fecal_unk}/194 ({miss_fecal_unk/194*100:.1f}%); "
      f"Max={df['Fecal_unknown_Max'].isna().sum()}/194 "
      f"({df['Fecal_unknown_Max'].isna().sum()/194*100:.1f}%) — "
      f"column excluded from WQI (ambiguous parameter identity).")

print("\n" + "="*65)
print("All 11 charts saved to report_images/")
print("="*65)
