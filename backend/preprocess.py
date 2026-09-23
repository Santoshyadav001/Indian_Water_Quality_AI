"""
preprocess.py — Data preprocessing functions for Indian Water Quality AI project.

Stage 3 of the PROJECT_PLAN.md specification.

Rules enforced here:
  - Raw CSV (data/Indian_water_data.csv) is NEVER modified.
  - 'Dissolved - Min/Max' is treated as UNVERIFIED assumed Dissolved Oxygen (mg/L).
    Every derived column is labelled 'DO_assumed' to preserve this disclosure.
  - BDL replacement values are UNVERIFIED approximations (proxy MDL/2).
  - Min > Max anomalies are flagged but NOT corrected.
  - Saline water bodies are excluded from WQI computation via a flag column.
  - All transformations are logged to a preprocessing audit trail.
"""

from __future__ import annotations

import os
import csv
import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Column name mapping — raw CSV columns → clean internal names
# 'Dissolved' renamed to 'DO_assumed' to preserve the UNVERIFIED disclosure.
# ---------------------------------------------------------------------------

RAW_COL_NAMES: list[str] = [
    "STN code",
    "Monitoring Location",
    "Year",
    "Type Water Body",
    "State Name",
    "Temperature (C) - Min",
    "Temperature (C) - Max",
    "Dissolved - Min",           # UNVERIFIED: assumed Dissolved Oxygen (mg/L)
    "Dissolved - Max",           # UNVERIFIED: assumed Dissolved Oxygen (mg/L)
    "pH - Min",
    "pH - Max",
    "Conductivity (uS/cm) - Min",   # µ symbol may be mangled in the CSV
    "Conductivity (uS/cm) - Max",
    "BOD (mg/L) - Min",
    "BOD (mg/L) - Max",
    "NitrateN (mg/L) - Min",
    "NitrateN (mg/L) - Max",
    "Fecal Coliform (MPN/100ml) - Min",
    "Fecal Coliform (MPN/100ml) - Max",
    "Total Coliform (MPN/100ml) - Min",
    "Total Coliform (MPN/100ml) - Max",
    "Fecal - Min",               # UNVERIFIED identity — excluded from analysis
    "Fecal - Max",               # UNVERIFIED identity — excluded from analysis
]

CLEAN_COL_NAMES: list[str] = [
    "STN_code",
    "Monitoring_Location",
    "Year",
    "Water_Body_Type",
    "State_Name",
    "Temp_Min",
    "Temp_Max",
    "DO_assumed_Min",   # UNVERIFIED: assumed Dissolved Oxygen (mg/L)
    "DO_assumed_Max",   # UNVERIFIED: assumed Dissolved Oxygen (mg/L)
    "pH_Min",
    "pH_Max",
    "Conductivity_Min",
    "Conductivity_Max",
    "BOD_Min",
    "BOD_Max",
    "NitrateN_Min",
    "NitrateN_Max",
    "FC_Min",
    "FC_Max",
    "TC_Min",
    "TC_Max",
    "Fecal_unknown_Min",   # EXCLUDED — identity unverified, 32-53% missing
    "Fecal_unknown_Max",   # EXCLUDED — identity unverified, 32-53% missing
]

# BDL proxy substitution values — UNVERIFIED (see PROJECT_PLAN.md Section 15 / UV-06)
# These are half of published typical instrument MDLs, NOT confirmed CPCB lab values.
BDL_SUBSTITUTIONS: dict[str, float] = {
    "DO_assumed_Min":   0.05,   # 0.1 mg/L typical DO meter MDL / 2  [UNVERIFIED]
    "DO_assumed_Max":   0.05,   # same                                 [UNVERIFIED]
    "Conductivity_Min": 0.5,    # 1.0 µmho/cm typical MDL / 2         [UNVERIFIED]
    "Conductivity_Max": 0.5,    # same                                 [UNVERIFIED]
    "BOD_Min":          0.25,   # 0.5 mg/L typical BOD5 MDL / 2       [UNVERIFIED]
    "BOD_Max":          0.25,   # same                                 [UNVERIFIED]
    "NitrateN_Min":     0.05,   # 0.1 mg/L typical IC MDL / 2         [UNVERIFIED]
    "NitrateN_Max":     0.05,   # same                                 [UNVERIFIED]
    "FC_Min":           1.0,    # MPN lower bound 2 / 2 = 1            [UNVERIFIED]
    "FC_Max":           1.0,    # same                                 [UNVERIFIED]
    "TC_Min":           1.0,    # same as FC                           [UNVERIFIED]
    "TC_Max":           1.0,    # same                                 [UNVERIFIED]
}

# Saline water-body exclusion rule (PROJECT_PLAN.md Section 12 / Appendix A.6)
# These water body types receive WQI_applicable = False unconditionally.
SALINE_WATER_BODY_TYPES: set[str] = {"MARINE", "SEA", "BEACH"}
# CREEK is saline if Conductivity_mean > 5000 µmho/cm (checked dynamically).
CREEK_CONDUCTIVITY_THRESHOLD: float = 5000.0

# Columns excluded from analysis entirely (truncated/unverified names + high missingness)
EXCLUDED_COLS: list[str] = ["Fecal_unknown_Min", "Fecal_unknown_Max"]

# Identifier columns — never used as ML features
IDENTIFIER_COLS: list[str] = ["STN_code", "Monitoring_Location"]


# ---------------------------------------------------------------------------
# Audit log helper
# ---------------------------------------------------------------------------

class AuditLog:
    """Accumulates one row per transformation for the preprocessing audit trail."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def log(
        self,
        step: str,
        column: str,
        action: str,
        rows_affected: int,
        detail: str = "",
    ) -> None:
        self._entries.append(
            {
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                "step": step,
                "column": column,
                "action": action,
                "rows_affected": rows_affected,
                "detail": detail,
            }
        )

    def to_rows(self) -> list[dict[str, Any]]:
        return list(self._entries)


# ---------------------------------------------------------------------------
# Step 1 — Load raw data (read-only)
# ---------------------------------------------------------------------------

def load_raw_data(path: str) -> tuple[list[str], list[list[str]]]:
    """
    Load the raw CSV without modification.

    Returns (header_list, rows_list) where every value is a raw string.
    The file at ``path`` is never written to.
    """
    with open(path, "r", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)
    return header, rows


# ---------------------------------------------------------------------------
# Step 2 — Convert to dict-of-lists structure with clean column names
# ---------------------------------------------------------------------------

def rename_columns(
    raw_header: list[str],
    rows: list[list[str]],
    audit: AuditLog,
) -> dict[str, list[str]]:
    """
    Map raw column names to clean internal names defined in CLEAN_COL_NAMES.

    The mapping is positional (index-based) so it is robust to encoding
    artefacts in the µ symbol.  Returns a dict mapping clean name → list of
    raw string values (one per row).
    """
    if len(raw_header) != len(CLEAN_COL_NAMES):
        raise ValueError(
            f"Expected {len(CLEAN_COL_NAMES)} columns, found {len(raw_header)}. "
            "Check that the correct CSV file is being loaded."
        )

    data: dict[str, list[str]] = {}
    for idx, clean_name in enumerate(CLEAN_COL_NAMES):
        data[clean_name] = [row[idx] if idx < len(row) else "" for row in rows]

    audit.log(
        step="rename_columns",
        column="ALL",
        action="positional rename",
        rows_affected=len(rows),
        detail=(
            "Raw column names mapped to clean internal names. "
            "'Dissolved - Min/Max' → 'DO_assumed_Min/Max' "
            "(UNVERIFIED: assumed Dissolved Oxygen mg/L). "
            "'Fecal - Min/Max' → 'Fecal_unknown_Min/Max' (excluded from analysis)."
        ),
    )
    return data


# ---------------------------------------------------------------------------
# Step 3 — Handle BDL values
# ---------------------------------------------------------------------------

def handle_bdl(
    data: dict[str, list[str]],
    audit: AuditLog,
) -> dict[str, list[str]]:
    """
    Replace 'BDL' string values with UNVERIFIED proxy MDL/2 substitution values
    and add a companion binary flag column for each affected measurement column.

    The substitution values in BDL_SUBSTITUTIONS are NOT confirmed from CPCB
    lab documentation — they are published typical instrument MDLs used as a
    proxy (PROJECT_PLAN.md Section 15, UV-06).
    """
    n_rows = len(next(iter(data.values())))

    for col, sub_value in BDL_SUBSTITUTIONS.items():
        if col not in data:
            continue

        flag_col = f"{col}_BDL_flag"
        flags = [0] * n_rows
        count = 0

        for i, val in enumerate(data[col]):
            if val.strip().upper() == "BDL":
                data[col][i] = str(sub_value)
                flags[i] = 1
                count += 1

        data[flag_col] = [str(f) for f in flags]

        if count > 0:
            audit.log(
                step="handle_bdl",
                column=col,
                action=f"BDL → {sub_value} (UNVERIFIED proxy MDL/2)",
                rows_affected=count,
                detail=(
                    f"Substitution value {sub_value} is UNVERIFIED — it is half of "
                    f"a published typical instrument MDL, not a confirmed CPCB lab "
                    f"detection limit. BDL flag stored in column '{flag_col}'."
                ),
            )

    return data


# ---------------------------------------------------------------------------
# Step 4 — Handle dash ('-') values
# ---------------------------------------------------------------------------

def handle_dash(
    data: dict[str, list[str]],
    audit: AuditLog,
) -> dict[str, list[str]]:
    """
    Replace dash ('-') string values with empty string (treated as NaN downstream).
    Add a companion flag column.  Dash meaning is ambiguous; no numeric
    substitution is applied.
    """
    measurement_cols = [
        c for c in data
        if c not in IDENTIFIER_COLS + ["Year", "Water_Body_Type", "State_Name"]
        and not c.endswith("_BDL_flag")
        and not c.endswith("_dash_flag")
        and not c.endswith("_minmax_anomaly")
    ]

    for col in measurement_cols:
        flag_col = f"{col}_dash_flag"
        n_rows = len(data[col])
        flags = [0] * n_rows
        count = 0

        for i, val in enumerate(data[col]):
            if val.strip() == "-":
                data[col][i] = ""   # treat as missing
                flags[i] = 1
                count += 1

        data[flag_col] = [str(f) for f in flags]

        if count > 0:
            audit.log(
                step="handle_dash",
                column=col,
                action="dash → NaN (empty string)",
                rows_affected=count,
                detail=(
                    "Dash value meaning is ambiguous (not measured / not applicable). "
                    "Treated as missing. No numeric substitution applied. "
                    f"Flag stored in '{flag_col}'."
                ),
            )

    return data


# ---------------------------------------------------------------------------
# Step 5 — Flag Min > Max anomalies (do NOT correct values)
# ---------------------------------------------------------------------------

def flag_minmax_anomalies(
    data: dict[str, list[str]],
    audit: AuditLog,
) -> dict[str, list[str]]:
    """
    Detect rows where the Min value is numerically greater than the Max value
    for each paired measurement column.  Flag such rows with an anomaly column.

    Values are NOT corrected — the plan requires source verification before any
    correction (PROJECT_PLAN.md Section 17).

    Note: (Min + Max) / 2 is unaffected by a Min/Max swap, so WQI computation
    using the midpoint is not impacted.
    """
    param_pairs: list[tuple[str, str, str]] = [
        ("Temp_Min",         "Temp_Max",         "Temp"),
        ("DO_assumed_Min",   "DO_assumed_Max",    "DO_assumed"),
        ("pH_Min",           "pH_Max",            "pH"),
        ("Conductivity_Min", "Conductivity_Max",  "Conductivity"),
        ("BOD_Min",          "BOD_Max",           "BOD"),
        ("NitrateN_Min",     "NitrateN_Max",      "NitrateN"),
        ("FC_Min",           "FC_Max",            "FC"),
        ("TC_Min",           "TC_Max",            "TC"),
        ("Fecal_unknown_Min","Fecal_unknown_Max",  "Fecal_unknown"),
    ]

    n_rows = len(next(iter(data.values())))

    for col_min, col_max, param_name in param_pairs:
        if col_min not in data or col_max not in data:
            continue

        flag_col = f"{param_name}_minmax_anomaly"
        flags = [0] * n_rows
        count = 0

        for i in range(n_rows):
            raw_min = data[col_min][i]
            raw_max = data[col_max][i]
            # Values may be float (post-parse) or string (pre-parse)
            try:
                v_min = float(raw_min) if raw_min is not None else None
                v_max = float(raw_max) if raw_max is not None else None
                if v_min is not None and v_max is not None and v_min > v_max:
                    flags[i] = 1
                    count += 1
            except (ValueError, TypeError):
                pass  # non-numeric — skip

        data[flag_col] = [str(f) for f in flags]

        if count > 0:
            audit.log(
                step="flag_minmax_anomalies",
                column=f"{col_min}/{col_max}",
                action=f"flagged {count} rows where Min > Max",
                rows_affected=count,
                detail=(
                    f"Values NOT corrected. Source verification (CPCB original reports) "
                    f"required before any correction. Flag stored in '{flag_col}'. "
                    f"Note: WQI midpoint computation is unaffected by Min/Max swap."
                ),
            )

    return data


# ---------------------------------------------------------------------------
# Step 6 — Convert measurement columns to float (None for missing/empty)
# ---------------------------------------------------------------------------

def _parse_float(val: str) -> float | None:
    """Return float or None for empty/non-numeric strings."""
    v = val.strip()
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def parse_numeric_columns(
    data: dict[str, list[str]],
    audit: AuditLog,
) -> dict[str, list[float | None]]:
    """
    Parse all measurement columns (those that should be numeric) from strings
    to float | None.  Categorical and identifier columns remain as strings.
    """
    string_cols = {
        "STN_code", "Monitoring_Location", "Year",
        "Water_Body_Type", "State_Name",
    }
    flag_pattern_suffixes = ("_BDL_flag", "_dash_flag", "_minmax_anomaly")

    parsed: dict[str, list] = {}
    for col, values in data.items():
        if col in string_cols or any(col.endswith(s) for s in flag_pattern_suffixes):
            parsed[col] = values  # keep as strings
        else:
            parsed[col] = [_parse_float(v) for v in values]

    audit.log(
        step="parse_numeric",
        column="ALL measurement columns",
        action="string → float | None",
        rows_affected=len(next(iter(data.values()))),
        detail="Empty strings and non-numeric values converted to None (NaN equivalent).",
    )
    return parsed


# ---------------------------------------------------------------------------
# Step 7 — Impute missing values using within-group median
# ---------------------------------------------------------------------------

def impute_missing(
    data: dict[str, list],
    group_col: str,
    target_cols: list[str],
    audit: AuditLog,
) -> dict[str, list]:
    """
    For each column in ``target_cols``, impute None values using the median
    of rows sharing the same value in ``group_col`` (e.g. Water_Body_Type).

    An imputed-flag companion column is added.
    If no non-None values exist in a group, the global median is used.
    Imputation statistics are computed on all available rows (no train/test
    split at this preprocessing stage — imputation is for WQI computation
    only; ML imputation will be re-applied post-split).
    """
    group_values = data[group_col]
    n_rows = len(group_values)

    # Build group → sorted non-None values mapping for each column
    for col in target_cols:
        if col not in data:
            continue

        col_vals = data[col]

        # Collect non-None values per group
        group_map: dict[str, list[float]] = {}
        for i in range(n_rows):
            if col_vals[i] is not None:
                grp = group_values[i]
                group_map.setdefault(grp, []).append(col_vals[i])

        # Compute group medians
        def _median(lst: list[float]) -> float:
            s = sorted(lst)
            m = len(s) // 2
            return s[m] if len(s) % 2 == 1 else (s[m - 1] + s[m]) / 2.0

        group_medians: dict[str, float] = {
            g: _median(v) for g, v in group_map.items() if v
        }
        all_vals = [v for v in col_vals if v is not None]
        global_median = _median(all_vals) if all_vals else 0.0

        flag_col = f"{col}_imputed_flag"
        flags = [0] * n_rows
        count = 0

        for i in range(n_rows):
            if col_vals[i] is None:
                grp = group_values[i]
                fill = group_medians.get(grp, global_median)
                data[col][i] = fill
                flags[i] = 1
                count += 1

        data[flag_col] = [str(f) for f in flags]

        if count > 0:
            audit.log(
                step="impute_missing",
                column=col,
                action=f"None → group median (group={group_col})",
                rows_affected=count,
                detail=(
                    f"Imputed {count} missing values using median of same "
                    f"'{group_col}' group. Imputation flag stored in '{flag_col}'. "
                    "Note: for ML, imputation will be re-applied on training data only."
                ),
            )

    return data


# ---------------------------------------------------------------------------
# Step 8 — Add WQI applicability flag
# ---------------------------------------------------------------------------

def flag_wqi_applicability(
    data: dict[str, list],
    audit: AuditLog,
) -> dict[str, list]:
    """
    Add a WQI_applicable column (string '1' or '0').

    WQI_applicable = '0' (False) when:
      - Water_Body_Type is MARINE, SEA, or BEACH, OR
      - Water_Body_Type is CREEK AND Conductivity_mean > 5000 µmho/cm

    Rationale: BIS IS:10500-2012 and CPCB DBU standards apply to freshwater;
    saline conductivity values make WQI computation meaningless for these rows.
    (PROJECT_PLAN.md Section 12 / Appendix A.6)
    """
    n_rows = len(data["Water_Body_Type"])
    applicable = []
    count_excluded = 0

    for i in range(n_rows):
        wb_type = data["Water_Body_Type"][i].strip().upper()

        if wb_type in SALINE_WATER_BODY_TYPES:
            applicable.append("0")
            count_excluded += 1
            continue

        if wb_type == "CREEK":
            # Compute Conductivity_mean to check salinity
            c_min = data["Conductivity_Min"][i]
            c_max = data["Conductivity_Max"][i]
            if c_min is not None and c_max is not None:
                c_mean = (c_min + c_max) / 2.0
            elif c_min is not None:
                c_mean = c_min
            elif c_max is not None:
                c_mean = c_max
            else:
                c_mean = 0.0

            if c_mean > CREEK_CONDUCTIVITY_THRESHOLD:
                applicable.append("0")
                count_excluded += 1
                continue

        applicable.append("1")

    data["WQI_applicable"] = applicable

    audit.log(
        step="flag_wqi_applicability",
        column="WQI_applicable",
        action="set WQI_applicable flag",
        rows_affected=count_excluded,
        detail=(
            f"{count_excluded} rows flagged WQI_applicable=0: "
            f"MARINE/SEA/BEACH (unconditional) or CREEK with "
            f"Conductivity_mean > {CREEK_CONDUCTIVITY_THRESHOLD} µmho/cm. "
            "BIS IS:10500-2012 freshwater standards are inapplicable to saline water."
        ),
    )
    return data


# ---------------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------------

def save_dict_as_csv(data: dict[str, list], path: str) -> None:
    """Write the data dict as a CSV file.  Creates parent directories if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cols = list(data.keys())
    n_rows = len(data[cols[0]])
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(cols)
        for i in range(n_rows):
            writer.writerow([data[c][i] for c in cols])


def save_audit_log(audit: AuditLog, path: str) -> None:
    """Write the audit log to a CSV file."""
    entries = audit.to_rows()
    if not entries:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ["timestamp", "step", "column", "action", "rows_affected", "detail"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
