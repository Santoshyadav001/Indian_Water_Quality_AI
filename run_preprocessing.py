"""
run_preprocessing.py -- Stage 3 pipeline runner.

Executes the full preprocessing and WQI computation pipeline as specified in
PROJECT_PLAN.md (Tier 2 scope).

Usage:
    python run_preprocessing.py

Outputs (all in data/processed/):
    water_quality_processed.csv   -- cleaned dataset with all flag columns
    wqi_scores.csv                -- WQI scores, categories, parameter means
    preprocessing_audit_log.csv   -- log of every transformation applied

The raw CSV (data/Indian_water_data.csv) is NEVER modified.
"""

import os
import sys

# Ensure the project root is on the path so backend imports work regardless
# of the working directory.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from backend.preprocess import (
    AuditLog,
    BDL_SUBSTITUTIONS,
    EXCLUDED_COLS,
    load_raw_data,
    rename_columns,
    handle_bdl,
    handle_dash,
    flag_minmax_anomalies,
    parse_numeric_columns,
    impute_missing,
    flag_wqi_applicability,
    save_dict_as_csv,
    save_audit_log,
)
from backend.wqi_calculator import (
    compute_annual_means,
    compute_unit_weights,
    compute_wqi,
    classify_wqi,
    wqi_summary_stats,
    WQI_STANDARDS,
    WQI_IDEALS,
    WQI_CATEGORIES,
    compute_sub_index,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_DATA_PATH = os.path.join(ROOT_DIR, "data", "Indian_water_data.csv")
PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")
PROCESSED_CSV  = os.path.join(PROCESSED_DIR, "water_quality_processed.csv")
WQI_CSV        = os.path.join(PROCESSED_DIR, "wqi_scores.csv")
AUDIT_LOG_CSV  = os.path.join(PROCESSED_DIR, "preprocessing_audit_log.csv")

# ---------------------------------------------------------------------------
# WQI parameter columns for imputation (the 14 Min/Max columns used in WQI)
# ---------------------------------------------------------------------------

WQI_IMPUTATION_TARGETS = [
    "DO_assumed_Min", "DO_assumed_Max",
    "pH_Min",         "pH_Max",
    "BOD_Min",        "BOD_Max",
    "Conductivity_Min", "Conductivity_Max",
    "NitrateN_Min",   "NitrateN_Max",
    "FC_Min",         "FC_Max",
    "TC_Min",         "TC_Max",
]

# Also impute Temperature (used as ML feature, not WQI component)
TEMP_IMPUTATION_TARGETS = ["Temp_Min", "Temp_Max"]

# ---------------------------------------------------------------------------
# Guard: confirm raw file has not changed
# ---------------------------------------------------------------------------

def _hash_file(path: str) -> str:
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline() -> None:
    print("=" * 70)
    print("STAGE 3 -- Preprocessing and WQI Computation")
    print("Indian Water Quality AI Project")
    print("=" * 70)
    print()

    # Record hash of raw file BEFORE anything
    raw_hash_before = _hash_file(RAW_DATA_PATH)
    print(f"Raw file hash (before): {raw_hash_before}")
    print(f"Raw file: {RAW_DATA_PATH}")
    print()

    audit = AuditLog()

    # ------------------------------------------------------------------
    # 1. Load
    # ------------------------------------------------------------------
    print("Step 1: Loading raw data ...")
    raw_header, raw_rows = load_raw_data(RAW_DATA_PATH)
    print(f"  Loaded {len(raw_rows)} rows x {len(raw_header)} columns")
    audit.log("load", "ALL", "read raw CSV (read-only)", len(raw_rows),
              f"Path: {RAW_DATA_PATH}")

    # ------------------------------------------------------------------
    # 2. Rename columns
    # ------------------------------------------------------------------
    print("Step 2: Renaming columns ...")
    data = rename_columns(raw_header, raw_rows, audit)
    print("  Columns mapped. 'Dissolved' -> 'DO_assumed' (UNVERIFIED).")

    # ------------------------------------------------------------------
    # 3. Handle BDL
    # ------------------------------------------------------------------
    print("Step 3: Handling BDL values (UNVERIFIED proxy MDL/2 substitution) ...")
    data = handle_bdl(data, audit)
    bdl_total = sum(
        int(v) for col in data
        if col.endswith("_BDL_flag")
        for v in data[col]
    )
    print(f"  Total BDL values substituted: {bdl_total}")

    # ------------------------------------------------------------------
    # 4. Handle dash values
    # ------------------------------------------------------------------
    print("Step 4: Handling dash ('-') values -> NaN ...")
    data = handle_dash(data, audit)

    # ------------------------------------------------------------------
    # 5. Parse strings -> float | None
    # ------------------------------------------------------------------
    print("Step 5: Parsing numeric columns ...")
    data = parse_numeric_columns(data, audit)

    # ------------------------------------------------------------------
    # 6. Flag Min > Max anomalies (do NOT correct)
    # ------------------------------------------------------------------
    print("Step 6: Flagging Min > Max anomalies (values NOT corrected) ...")
    data = flag_minmax_anomalies(data, audit)
    anomaly_cols = [c for c in data if c.endswith("_minmax_anomaly")]
    total_anomaly_rows = 0
    for ac in anomaly_cols:
        n = sum(int(v) for v in data[ac])
        if n > 0:
            param = ac.replace("_minmax_anomaly", "")
            print(f"    {param}: {n} rows where Min > Max (flagged)")
            total_anomaly_rows += n
    print(f"  Total anomaly flags set: {total_anomaly_rows}")

    # ------------------------------------------------------------------
    # 7. Impute missing values (group-median per Water_Body_Type)
    # ------------------------------------------------------------------
    print("Step 7: Imputing missing values (group median by Water_Body_Type) ...")
    data = impute_missing(
        data,
        group_col="Water_Body_Type",
        target_cols=WQI_IMPUTATION_TARGETS + TEMP_IMPUTATION_TARGETS,
        audit=audit,
    )
    imputed_total = sum(
        int(v) for col in data
        if col.endswith("_imputed_flag")
        for v in data[col]
    )
    print(f"  Total values imputed: {imputed_total}")

    # ------------------------------------------------------------------
    # 8. Flag WQI applicability
    # ------------------------------------------------------------------
    print("Step 8: Flagging WQI applicability (saline exclusion) ...")
    data = flag_wqi_applicability(data, audit)
    n_applicable = sum(1 for v in data["WQI_applicable"] if v == "1")
    n_excluded   = sum(1 for v in data["WQI_applicable"] if v == "0")
    print(f"  WQI_applicable=1 (freshwater): {n_applicable} rows")
    print(f"  WQI_applicable=0 (saline/excluded): {n_excluded} rows")

    # ------------------------------------------------------------------
    # 9. Save processed dataset
    # ------------------------------------------------------------------
    print("Step 9: Saving processed dataset ...")

    # Exclude the raw excluded columns from the output
    # (retain them as 'Fecal_unknown' to preserve the record, but clearly labelled)
    save_dict_as_csv(data, PROCESSED_CSV)
    n_cols_out = len(data)
    n_rows_out = len(next(iter(data.values())))
    print(f"  Saved: {PROCESSED_CSV}")
    print(f"  Dimensions: {n_rows_out} rows x {n_cols_out} columns")

    # ------------------------------------------------------------------
    # 10. Compute annual parameter means for WQI
    # ------------------------------------------------------------------
    print("Step 10: Computing annual parameter means (Min+Max)/2 ...")
    means = compute_annual_means(data)
    for param, mean_col in [(p, f"{p}_mean") for p in WQI_STANDARDS]:
        valid = sum(1 for v in means[mean_col] if v is not None)
        print(f"    {mean_col}: {valid} non-null values")

    # ------------------------------------------------------------------
    # 11. Compute unit weights
    # ------------------------------------------------------------------
    print("Step 11: Computing unit weights W_i = K/S_i ...")
    weights = compute_unit_weights()
    sum_w = sum(weights.values())
    print(f"  K (proportionality constant) = {1.0 / sum(1.0/s for s in WQI_STANDARDS.values()):.6f}")
    for param, w in sorted(weights.items(), key=lambda x: -x[1]):
        print(f"    W_{param} = {w:.6f}")

    # ------------------------------------------------------------------
    # 12. Compute WQI scores
    # ------------------------------------------------------------------
    print("Step 12: Computing WQI scores ...")
    wqi_applicable = data["WQI_applicable"]
    wqi_scores, wqi_reasons = compute_wqi(means, wqi_applicable, weights)

    n_computed = sum(1 for s in wqi_scores if s is not None)
    n_saline   = sum(1 for r in wqi_reasons if r == "saline_water_body_excluded")
    n_missing  = sum(1 for r in wqi_reasons if r.startswith("missing_parameters"))
    print(f"  WQI computed: {n_computed} rows")
    print(f"  WQI=None (saline excluded): {n_saline} rows")
    print(f"  WQI=None (missing parameters): {n_missing} rows")

    # ------------------------------------------------------------------
    # 13. Classify WQI
    # ------------------------------------------------------------------
    print("Step 13: Classifying WQI scores into categories ...")
    wqi_categories = classify_wqi(wqi_scores)
    from collections import Counter
    cat_counts = Counter(c for c in wqi_categories if c != "N/A")
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {cat}: {cnt}")

    # ------------------------------------------------------------------
    # 14. Summary statistics
    # ------------------------------------------------------------------
    stats = wqi_summary_stats(wqi_scores, wqi_categories)
    print()
    print("  WQI score summary (computed rows only):")
    print(f"    n={stats['count']}  min={stats['min']}  max={stats['max']}")
    print(f"    mean={stats['mean']}  median={stats['median']}  std={stats['std']}")
    print(f"    Q1={stats['q1']}  Q3={stats['q3']}")

    # ------------------------------------------------------------------
    # 15. Build and save WQI scores CSV
    # ------------------------------------------------------------------
    print()
    print("Step 14: Saving WQI scores CSV ...")

    # Build WQI output: identifiers + metadata + parameter means + WQI columns
    wqi_data: dict[str, list] = {}

    # Identifiers
    for col in ["STN_code", "Monitoring_Location", "Year", "Water_Body_Type", "State_Name"]:
        wqi_data[col] = data[col]

    # WQI applicability
    wqi_data["WQI_applicable"] = data["WQI_applicable"]

    # Parameter means
    for param in WQI_STANDARDS:
        col = f"{param}_mean"
        wqi_data[col] = [
            str(round(v, 4)) if v is not None else ""
            for v in means[col]
        ]

    # WQI score and category
    wqi_data["WQI_score"] = [
        str(round(s, 4)) if s is not None else ""
        for s in wqi_scores
    ]
    wqi_data["WQI_category"] = wqi_categories
    wqi_data["WQI_reason"]   = wqi_reasons

    # Anomaly flags for WQI-relevant params
    for col in ["Conductivity_minmax_anomaly", "FC_minmax_anomaly"]:
        if col in data:
            wqi_data[col] = data[col]

    # Imputation flags for WQI params
    for param in WQI_STANDARDS:
        for suffix in ["Min", "Max"]:
            flag_col = f"{param if param != 'DO_assumed' else 'DO_assumed'}_{suffix}_imputed_flag"
            # Handle the DO_assumed naming
            if param == "DO_assumed":
                flag_col = f"DO_assumed_{suffix}_imputed_flag"
            else:
                flag_col = f"{param}_{suffix}_imputed_flag"
            if flag_col in data:
                wqi_data[flag_col] = data[flag_col]

    save_dict_as_csv(wqi_data, WQI_CSV)
    print(f"  Saved: {WQI_CSV}")
    print(f"  Rows: {len(wqi_data['WQI_score'])}")

    # ------------------------------------------------------------------
    # 16. Save audit log
    # ------------------------------------------------------------------
    print("Step 15: Saving preprocessing audit log ...")

    # Log the WQI computation itself
    audit.log(
        "compute_wqi",
        "WQI_score",
        f"Modified Weighted Arithmetic WQI -- Brown (1970) / project-specific parametrisation",
        n_computed,
        (
            "MODIFIED/CUSTOM INDEX: formula structure from Brown (1970); Si values, "
            "sub-index adaptations, and classification thresholds are project-specific. "
            "DISCLOSURE: WQI uses (Min+Max)/2 as annual representative value -- "
            "this is a range-midpoint approximation, not a true annual mean. "
            f"Standards: {WQI_STANDARDS}. "
            f"Ideals: {WQI_IDEALS}."
        ),
    )
    save_audit_log(audit, AUDIT_LOG_CSV)
    print(f"  Saved: {AUDIT_LOG_CSV}")
    print(f"  Audit entries: {len(audit.to_rows())}")

    # ------------------------------------------------------------------
    # 17. Confirm raw file is unchanged
    # ------------------------------------------------------------------
    raw_hash_after = _hash_file(RAW_DATA_PATH)
    print()
    print(f"Raw file hash (after):  {raw_hash_after}")
    if raw_hash_before == raw_hash_after:
        print("[OK] Raw data file is UNCHANGED.")
    else:
        print("[ERROR] ERROR: Raw data file hash changed! Investigate immediately.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 18. Final summary
    # ------------------------------------------------------------------
    print()
    print("=" * 70)
    print("STAGE 3 COMPLETE -- Files created:")
    print(f"  {PROCESSED_CSV}")
    print(f"  {WQI_CSV}")
    print(f"  {AUDIT_LOG_CSV}")
    print()
    print("Key numbers:")
    print(f"  Raw rows:               {len(raw_rows)}")
    print(f"  Freshwater rows (WQI):  {n_applicable}")
    print(f"  Saline rows (excluded): {n_excluded}")
    print(f"  WQI scores computed:    {n_computed}")
    print(f"  WQI=None (missing par): {n_missing}")
    print(f"  BDL substitutions:      {bdl_total} (UNVERIFIED proxy values)")
    print(f"  Imputed values:         {imputed_total} (group-median)")
    print(f"  Min>Max flags:          {total_anomaly_rows} (NOT corrected)")
    print()
    print("DISCLOSURE:")
    print("  - 'DO_assumed' columns are UNVERIFIED assumed Dissolved Oxygen (mg/L).")
    print("  - WQI is a MODIFIED index; not identical to any single published standard.")
    print("  - WQI uses (Min+Max)/2 as annual representative -- range-midpoint approximation.")
    print("  - BDL substitution values are UNVERIFIED proxy MDL/2.")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()
