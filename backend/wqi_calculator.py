"""
wqi_calculator.py — Modified Weighted Arithmetic WQI computation functions.

Stage 3 of the PROJECT_PLAN.md specification.

METHODOLOGY LABEL: MODIFIED / CUSTOM INDEX
  Base formula: Brown et al. (1970). "A Water Quality Index — Do We Dare?"
                Water and Sewage Works, 117, 339–343.
  Indian reference: Tyagi et al. (2013). American Journal of Water Resources,
                    1(3), 34–38. DOI: 10.12691/ajwr-1-3-3.
  The exact parametrisation (Si values, sub-index adaptations, classification
  thresholds) is project-specific and NOT identical to any single published index.

REQUIRED DISCLOSURE in every output:
  "WQI values are computed using the arithmetic midpoint of the reported annual
   parameter range [(Min + Max) / 2] as the representative annual concentration.
   This is an approximation; the true annual mean WQI would require individual
   sample measurements. WQI scores are indicative only."
"""

from __future__ import annotations

import math
from typing import Any

# ---------------------------------------------------------------------------
# WQI parameter configuration
# (PROJECT_PLAN.md Section 9, Standard Values table)
# ---------------------------------------------------------------------------

# S_i — permissible standard values
# Source: BIS IS:10500-2012 (drinking water) and CPCB DBU criteria (IS:2296-1982)
WQI_STANDARDS: dict[str, float] = {
    "DO_assumed":   6.0,      # CPCB Class B river minimum (mg/L)
    "pH":           8.5,      # BIS IS:10500-2012 upper permissible limit
    # pH sub-index uses deviation from ideal (7.0); S_i here is the upper limit
    "BOD":          3.0,      # CPCB Class B/C river standard (mg/L)
    "Conductivity": 300.0,    # BIS IS:10500-2012 acceptable limit (µmho/cm)
    "NitrateN":     10.2,     # BIS IS:10500-2012: 45 mg/L as NO3 = 10.2 mg/L as N
    "FC":           500.0,    # CPCB Class B bathing water (MPN/100ml)
    "TC":           5000.0,   # CPCB Class C raw water for treatment (MPN/100ml)
}

# V_ideal_i — ideal (pure water) values
WQI_IDEALS: dict[str, float] = {
    "DO_assumed":   14.6,   # max DO saturation at 0°C (~sea level)
    "pH":           7.0,    # neutral pH; also the reference for deviation formula
    "BOD":          0.0,
    "Conductivity": 0.0,
    "NitrateN":     0.0,
    "FC":           0.0,
    "TC":           0.0,
}

# Columns in the processed dataset that hold the Min and Max for each parameter
PARAM_COL_MAP: dict[str, tuple[str, str]] = {
    "DO_assumed":   ("DO_assumed_Min",   "DO_assumed_Max"),
    "pH":           ("pH_Min",           "pH_Max"),
    "BOD":          ("BOD_Min",          "BOD_Max"),
    "Conductivity": ("Conductivity_Min", "Conductivity_Max"),
    "NitrateN":     ("NitrateN_Min",     "NitrateN_Max"),
    "FC":           ("FC_Min",           "FC_Max"),
    "TC":           ("TC_Min",           "TC_Max"),
}

# WQI classification thresholds (PROJECT_PLAN.md Section 9 / Tyagi et al. 2013)
# UNVERIFIED: exact thresholds not confirmed against the original paper.
WQI_CATEGORIES: list[tuple[float, float, str]] = [
    (0.0,   25.0,  "Excellent"),
    (25.0,  50.0,  "Good"),
    (50.0,  75.0,  "Poor"),
    (75.0,  100.0, "Very Poor"),
    (100.0, float("inf"), "Unsuitable for Drinking"),
]


# ---------------------------------------------------------------------------
# Step 1 — Compute annual mean for each WQI parameter
# ---------------------------------------------------------------------------

def compute_annual_means(
    data: dict[str, list],
) -> dict[str, list[float | None]]:
    """
    For each WQI parameter, compute the annual representative concentration as:
        C_i = (Min_i + Max_i) / 2

    If only one of Min/Max is available, that value is used.
    If neither is available, returns None for that row.

    DISCLOSURE: This is the range midpoint, NOT the arithmetic mean of all
    individual samples taken during the year.
    """
    means: dict[str, list[float | None]] = {}
    n_rows = len(next(iter(data.values())))

    for param, (col_min, col_max) in PARAM_COL_MAP.items():
        col_means: list[float | None] = []
        for i in range(n_rows):
            v_min = data[col_min][i] if col_min in data else None
            v_max = data[col_max][i] if col_max in data else None

            if v_min is not None and v_max is not None:
                col_means.append((v_min + v_max) / 2.0)
            elif v_min is not None:
                col_means.append(v_min)
            elif v_max is not None:
                col_means.append(v_max)
            else:
                col_means.append(None)

        means[f"{param}_mean"] = col_means

    return means


# ---------------------------------------------------------------------------
# Step 2 — Compute unit weights W_i = K / S_i
# ---------------------------------------------------------------------------

def compute_unit_weights() -> dict[str, float]:
    """
    W_i = K / S_i   where   K = 1 / Σ(1 / S_i)

    This assigns higher weight to parameters with stricter (smaller) standards,
    following the Brown (1970) / Tyagi (2013) weighted arithmetic approach.

    Returns a dict mapping parameter name → W_i value.
    """
    sum_inv_s = sum(1.0 / s for s in WQI_STANDARDS.values())
    k = 1.0 / sum_inv_s

    weights: dict[str, float] = {
        param: k / s for param, s in WQI_STANDARDS.items()
    }
    return weights


# ---------------------------------------------------------------------------
# Step 3 — Compute sub-index Q_i for each parameter
# ---------------------------------------------------------------------------

def compute_sub_index(
    param: str,
    c_i: float,
) -> float:
    """
    Compute the sub-index quality rating Q_i for a single parameter and value.

    Standard formula: Q_i = ((C_i - V_ideal) / (S_i - V_ideal)) * 100
    Capped to [0, 200] to prevent extreme values from distorting WQI.

    Special cases (PROJECT_PLAN.md Section 9):
      - DO (assumed):  beneficial parameter — inverted formula:
          Q_DO = (C_DO / S_DO) * 100, capped at 100 (better = higher DO)
      - pH:  absolute-deviation formula:
          Q_pH = |C_pH - 7.0| / |S_pH - 7.0| * 100 = |C_pH - 7.0| / 1.5 * 100
    """
    s_i = WQI_STANDARDS[param]
    v_ideal = WQI_IDEALS[param]

    if param == "DO_assumed":
        # Higher DO = better quality; Q_DO = (C_DO / S_DO) * 100, capped at 100
        q = (c_i / s_i) * 100.0
        return min(q, 100.0)

    if param == "pH":
        # Absolute deviation from neutral (7.0)
        # |S_pH - 7.0| = |8.5 - 7.0| = 1.5
        ph_deviation_from_ideal = abs(c_i - v_ideal)
        ph_standard_deviation = abs(s_i - v_ideal)   # = 1.5
        q = (ph_deviation_from_ideal / ph_standard_deviation) * 100.0
        return min(q, 200.0)   # cap at 200 to handle extreme pH values

    # Standard formula for all other parameters
    denominator = s_i - v_ideal
    if denominator == 0:
        return 0.0
    q = ((c_i - v_ideal) / denominator) * 100.0
    return max(0.0, min(q, 200.0))   # cap negative Q at 0, cap upper at 200


# ---------------------------------------------------------------------------
# Step 4 — Compute WQI score for all rows
# ---------------------------------------------------------------------------

def compute_wqi(
    means: dict[str, list[float | None]],
    wqi_applicable: list[str],
    weights: dict[str, float],
) -> tuple[list[float | None], list[str]]:
    """
    Compute WQI = Σ(Q_i * W_i) / Σ(W_i) for each row.

    Only computed for rows where WQI_applicable == '1' AND all 7 parameter
    means are non-None.

    Returns:
      wqi_scores  — list of float or None (None if not computable)
      wqi_reasons — list of strings explaining why WQI is None where applicable
    """
    n_rows = len(wqi_applicable)
    params = list(WQI_STANDARDS.keys())
    sum_w = sum(weights.values())

    wqi_scores: list[float | None] = []
    wqi_reasons: list[str] = []

    for i in range(n_rows):
        if wqi_applicable[i] != "1":
            wqi_scores.append(None)
            wqi_reasons.append("saline_water_body_excluded")
            continue

        # Check all parameters are available
        missing_params = [
            p for p in params
            if means.get(f"{p}_mean", [None] * (i + 1))[i] is None
        ]
        if missing_params:
            wqi_scores.append(None)
            wqi_reasons.append(f"missing_parameters: {','.join(missing_params)}")
            continue

        # Compute weighted sum of sub-indices
        weighted_sum = 0.0
        for param in params:
            c_i = means[f"{param}_mean"][i]
            q_i = compute_sub_index(param, c_i)
            w_i = weights[param]
            weighted_sum += q_i * w_i

        wqi = weighted_sum / sum_w
        wqi_scores.append(round(wqi, 4))
        wqi_reasons.append("computed")

    return wqi_scores, wqi_reasons


# ---------------------------------------------------------------------------
# Step 5 — Classify WQI into categories
# ---------------------------------------------------------------------------

def classify_wqi(wqi_scores: list[float | None]) -> list[str]:
    """
    Map each WQI score to a quality category string using the thresholds
    defined in WQI_CATEGORIES.

    Returns 'N/A' for rows where WQI score is None.

    Classification thresholds (PROJECT_PLAN.md Section 9 / Tyagi et al. 2013):
      0–25:    Excellent
      25–50:   Good
      50–75:   Poor
      75–100:  Very Poor
      > 100:   Unsuitable for Drinking
    """
    categories: list[str] = []
    for score in wqi_scores:
        if score is None:
            categories.append("N/A")
            continue
        assigned = "Unsuitable for Drinking"
        for low, high, label in WQI_CATEGORIES:
            if low <= score < high:
                assigned = label
                break
        categories.append(assigned)
    return categories


# ---------------------------------------------------------------------------
# Summary statistics helper
# ---------------------------------------------------------------------------

def wqi_summary_stats(
    wqi_scores: list[float | None],
    wqi_categories: list[str],
) -> dict[str, Any]:
    """
    Compute basic descriptive statistics on the computed WQI scores
    for reporting purposes.
    """
    valid = [s for s in wqi_scores if s is not None]
    if not valid:
        return {"count": 0}

    valid_sorted = sorted(valid)
    n = len(valid_sorted)
    mean = sum(valid_sorted) / n
    mid = n // 2
    median = valid_sorted[mid] if n % 2 == 1 else (valid_sorted[mid - 1] + valid_sorted[mid]) / 2.0
    variance = sum((x - mean) ** 2 for x in valid_sorted) / (n - 1) if n > 1 else 0.0
    std = math.sqrt(variance)

    from collections import Counter
    cat_counts = dict(Counter(wqi_categories))

    return {
        "count": n,
        "min": round(valid_sorted[0], 4),
        "max": round(valid_sorted[-1], 4),
        "mean": round(mean, 4),
        "median": round(median, 4),
        "std": round(std, 4),
        "q1": round(valid_sorted[n // 4], 4),
        "q3": round(valid_sorted[3 * n // 4], 4),
        "category_counts": cat_counts,
    }
