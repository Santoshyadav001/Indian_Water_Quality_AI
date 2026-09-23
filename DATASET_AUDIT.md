# Dataset Audit Report
**Project:** AICTE | IBM SkillsBuild Data Analytics with AI Internship 2026  
**Audit Date:** 2025  
**Auditor:** Dataset Audit Stage (pre-modelling)  
**Status:** ✅ Complete — awaiting approval before any further step

---

## 1. Dataset File Information

| Item | Detail |
|---|---|
| **Actual filename** | `Indian_water_data.csv` |
| **Location** | `data/Indian_water_data.csv` |
| **Note** | The file is NOT named `data.csv` — the actual name is `Indian_water_data.csv` |
| **Format** | CSV (comma-separated values) |
| **Encoding** | UTF-8 with BOM (`utf-8-sig`) |
| **Encoding note** | The µ symbol in "µmho/cm" is corrupted to `��` under utf-8-sig but reads as `¬µ` under latin-1; this is a cosmetic encoding artefact and does not affect numeric data |

---

## 2. Dataset Dimensions

| Metric | Value |
|---|---|
| **Total rows (data records)** | **194** |
| **Total columns** | **23** |
| **Duplicate rows** | **0** (all 194 rows are unique) |

---

## 3. Column Names and Data Types

| # | Column Name | Inferred Type | Notes |
|---|---|---|---|
| 0 | `STN code` | Numeric (integer) | Station identifier — acts as an ID, not a measurement |
| 1 | `Monitoring Location` | String / Categorical | Free-text location name; 181 unique values out of 194 rows |
| 2 | `Year` | Numeric (integer) | Year of measurement; values: 2021, 2022, 2023 |
| 3 | `Type Water Body` | String / Categorical | 11 unique categories |
| 4 | `State Name` | String / Categorical | 17 unique Indian states |
| 5 | `Temperature (C) - Min` | Numeric (float) | Minimum temperature in °C |
| 6 | `Temperature (C) - Max` | Numeric (float) | Maximum temperature in °C |
| 7 | `Dissolved - Min` | Numeric (float) + BDL | **Truncated name** — almost certainly "Dissolved Oxygen (mg/L) - Min" |
| 8 | `Dissolved - Max` | Numeric (float) | **Truncated name** — almost certainly "Dissolved Oxygen (mg/L) - Max" |
| 9 | `pH - Min` | Numeric (float) | Minimum pH |
| 10 | `pH - Max` | Numeric (float) | Maximum pH |
| 11 | `Conductivity (µmho/cm) - Min` | Numeric (float) + BDL | Electrical conductivity minimum; µ symbol is encoding-corrupted |
| 12 | `Conductivity (µmho/cm) - Max` | Numeric (float) | Electrical conductivity maximum |
| 13 | `BOD (mg/L) - Min` | Numeric (float) + BDL | Biochemical Oxygen Demand minimum |
| 14 | `BOD (mg/L) - Max` | Numeric (float) | Biochemical Oxygen Demand maximum |
| 15 | `NitrateN (mg/L) - Min` | Numeric (float) + BDL | Nitrate-Nitrogen minimum |
| 16 | `NitrateN (mg/L) - Max` | Numeric (float) | Nitrate-Nitrogen maximum |
| 17 | `Fecal Coliform (MPN/100ml) - Min` | Numeric (float) + BDL | Fecal Coliform minimum |
| 18 | `Fecal Coliform (MPN/100ml) - Max` | Numeric (float) + BDL | Fecal Coliform maximum |
| 19 | `Total Coliform (MPN/100ml) - Min` | Numeric (float) + dash | Total Coliform minimum |
| 20 | `Total Coliform (MPN/100ml) - Max` | Numeric (float) | Total Coliform maximum |
| 21 | `Fecal - Min` | Numeric (float) + BDL + dash | **Truncated name** — likely a second/different Fecal measurement |
| 22 | `Fecal - Max` | Numeric (float) + BDL + dash | **Truncated name** — as above |

> **⚠ Truncated column names:** Columns 7/8 (`Dissolved - Min/Max`) and columns 21/22 (`Fecal - Min/Max`) have names that are clearly cut off. The full intended names cannot be determined from the file alone. The original data source should be consulted to confirm.

---

## 4. First 5 Rows

| STN code | Monitoring Location | Year | Type Water Body | State Name | Temp Min | Temp Max | Dissolved Min | Dissolved Max | pH Min | pH Max | Cond Min | Cond Max | BOD Min | BOD Max | NitrateN Min | NitrateN Max | FC Min | FC Max | TC Min | TC Max | Fecal Min | Fecal Max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4085 | RIVER JUMAR AT BIT MESRA, RANCHI | 2022 | RIVER | JHARKHAND | 12 | 29 | 3.3 | 5.2 | 6.5 | 6.6 | — | — | 2 | 2.9 | — | — | — | — | — | — | — | — |
| 2396 | RIVER JUMAR AT KANKE DAM | 2022 | RIVER | JHARKHAND | 12 | 26 | 5.9 | 7.2 | 7.5 | 7.6 | — | — | 1.9 | 3.2 | — | — | — | — | — | — | — | — |
| 2401 | RIVER AJAY AT MASANJORE DAM | 2022 | RIVER | JHARKHAND | 17 | 36 | 5.8 | 6.6 | 7.5 | 7.8 | 94 | 318 | 1.3 | 1.6 | — | — | — | — | — | — | — | — |
| 3554 | RIVER KONAR NEAR SWANG COAL WASHERY, BOKARO | 2022 | RIVER | JHARKHAND | 19 | 34 | 7.4 | 7.8 | 7.3 | 7.6 | — | — | 1.8 | 2.7 | — | — | — | — | — | — | — | — |
| 2390 | RIVER KONAR AT TENUGHAT DAM | 2022 | RIVER | JHARKHAND | 16 | 33 | 7.4 | 8.0 | 7.4 | 7.8 | — | — | 1.3 | 2.0 | — | — | — | — | — | — | — | — |

---

## 5. Missing Values

| Column | Missing Count | Missing % | Notes |
|---|---|---|---|
| STN code | 0 | 0.0% | Complete |
| Monitoring Location | 0 | 0.0% | Complete |
| Year | 0 | 0.0% | Complete |
| Type Water Body | 0 | 0.0% | Complete |
| State Name | 0 | 0.0% | Complete |
| Temperature (C) - Min | 2 | 1.0% | Minimal |
| Temperature (C) - Max | 2 | 1.0% | Minimal |
| Dissolved - Min | 1 | 0.5% | Minimal; also 1 BDL value |
| Dissolved - Max | 1 | 0.5% | Minimal |
| pH - Min | 0 | 0.0% | Complete |
| pH - Max | 0 | 0.0% | Complete |
| Conductivity (µmho/cm) - Min | 13 | 6.7% | Also 1 BDL value |
| Conductivity (µmho/cm) - Max | 13 | 6.7% | |
| BOD (mg/L) - Min | 13 | 6.7% | Also 11 BDL values |
| BOD (mg/L) - Max | 15 | 7.7% | |
| NitrateN (mg/L) - Min | 13 | 6.7% | Also 2 BDL values |
| NitrateN (mg/L) - Max | 13 | 6.7% | |
| Fecal Coliform (MPN/100ml) - Min | 13 | 6.7% | Also 3 BDL values |
| Fecal Coliform (MPN/100ml) - Max | 13 | 6.7% | Also 1 BDL value |
| Total Coliform (MPN/100ml) - Min | 14 | 7.2% | Also 1 dash (`-`) value |
| Total Coliform (MPN/100ml) - Max | 15 | 7.7% | |
| **Fecal - Min** | **62** | **32.0%** | Also 18 BDL + 7 dash values (effectively ~45% unusable) |
| **Fecal - Max** | **102** | **52.6%** | Also 18 BDL + 7 dash values (effectively ~68% unusable) |

**BDL ("Below Detection Limit")** occurs in 8 columns and represents a valid measurement outcome (the parameter was present but below instrument sensitivity). These are **not** the same as missing data and must be handled carefully during pre-processing.

**Dash (`-`)** values occur in columns 19, 21, 22 and appear to mean "not measured" or "not applicable."

---

## 6. Duplicate Rows

**Zero duplicate rows** found. All 194 rows are unique.

---

## 7. Categorical Columns — Unique Value Counts

| Column | Unique Values | Values |
|---|---|---|
| `STN code` | 168 | (station IDs — 26 stations appear in 2 years) |
| `Monitoring Location` | 181 | (free-text location names) |
| `Year` | 3 | 2021, 2022, 2023 |
| `Type Water Body` | 11 | BEACH, CANAL, CREEK, DRAIN, LAKE, MARINE, POND, RIVER, SEA, STP, WATER TREATMENT PLANT (RAW WATER) |
| `State Name` | 17 | ANDHRA PRADESH, ASSAM, DELHI, GOA, GUJARAT, HARYANA, HIMACHAL PRADESH, JHARKHAND, MADHYA PRADESH, MAHARASHTRA, ODISHA, PUNJAB, RAJASTHAN, TAMIL NADU, TELANGANA, UTTAR PRADESH, UTTARAKHAND |

**Rows per year:** 2021: 44 | 2022: 53 | 2023: 97  
**Rows per state (top 5):** Himachal Pradesh: 49 | Assam: 46 | Andhra Pradesh: 37 | Goa: 16 | Jharkhand: 12

---

## 8. Numerical Columns — Descriptive Statistics

All statistics computed on numeric-parseable values only (BDL and dash values excluded).

| Column | n | Min | Max | Mean | Median | Std Dev | Q1 | Q3 |
|---|---|---|---|---|---|---|---|---|
| Temperature (C) - Min | 192 | 1.0 | 28.0 | 18.42 | 21.0 | 6.75 | 13.0 | 23.0 |
| Temperature (C) - Max | 192 | 8.0 | 39.0 | 27.46 | 29.0 | 6.59 | 24.0 | 32.0 |
| Dissolved - Min | 192 | 0.3 | 9.4 | 5.51 | 5.3 | 2.10 | 4.5 | 7.1 |
| Dissolved - Max | 193 | 1.1 | 13.6 | 7.66 | 7.8 | 1.81 | 6.7 | 8.6 |
| pH - Min | 194 | 5.7 | 8.5 | 7.13 | 7.1 | 0.45 | 6.8 | 7.4 |
| pH - Max | 194 | 6.6 | 11.2 | 8.00 | 8.0 | 0.46 | 7.7 | 8.3 |
| Conductivity (µmho/cm) - Min | 180 | 32.0 | 38,200 | 4,546.8 | 219.0 | 10,484.7 | 111.0 | 960.0 |
| Conductivity (µmho/cm) - Max | 181 | 4.0 | 61,900 | 11,457.0 | 680.0 | 21,392.2 | 201.0 | 3,040.0 |
| BOD (mg/L) - Min | 170 | 1.0 | 32.0 | 2.42 | 1.8 | 3.82 | 1.0 | 2.1 |
| BOD (mg/L) - Max | 179 | 1.0 | 90.0 | 5.20 | 2.6 | 10.57 | 1.9 | 3.0 |
| NitrateN (mg/L) - Min | 179 | 0.3 | 5.5 | 0.68 | 0.42 | 0.74 | 0.3 | 0.7 |
| NitrateN (mg/L) - Max | 181 | 0.3 | 17.0 | 2.76 | 1.8 | 2.99 | 1.15 | 2.9 |
| Fecal Coliform (MPN/100ml) - Min | 178 | 2 | 110,000 | 1,526.6 | 21.5 | 9,928.6 | 3.0 | 300.0 |
| Fecal Coliform (MPN/100ml) - Max | 180 | 2 | 14,000,000 | 80,678.9 | 170.0 | 1,043,597.2 | 21.0 | 620.0 |
| Total Coliform (MPN/100ml) - Min | 179 | 2 | 790,000 | 4,842.1 | 75.0 | 59,021.4 | 26.0 | 700.0 |
| Total Coliform (MPN/100ml) - Max | 179 | 2 | 14,000,000 | 85,279.1 | 910.0 | 1,047,617.2 | 210.0 | 1,600.0 |
| Fecal - Min | 107 | 2.0 | 460.0 | 54.6 | 13.0 | 75.9 | 2.0 | 95.0 |
| Fecal - Max | 67 | 2.0 | 1,100.0 | 191.9 | 210.0 | 167.2 | 94.0 | 240.0 |

---

## 9. Suspicious, Invalid, or Impossible Values

| Issue | Severity | Details |
|---|---|---|
| **Truncated column names** | ⚠ Medium | Columns 7/8 (`Dissolved - Min/Max`) and 21/22 (`Fecal - Min/Max`) are cut off. Full names unknown from the file alone. |
| **Encoding corruption** | Low | `µmho/cm` renders as `��mho/cm` under UTF-8 — cosmetic only, no data affected. |
| **Conductivity Min > Max (5 rows)** | ⚠ Medium | Rows 56–59 (Andhra Pradesh) and Row 65 (Gujarat). These are data recording errors or transposed values. Notable: Row 65 has Min=212, Max=4 — very likely a column swap. |
| **Fecal Coliform Min > Max (10 rows)** | ⚠ Medium | Found in Assam (2 rows), Himachal Pradesh (6 rows), and Punjab (2 rows). Min values exceed Max values — likely data entry errors. |
| **Conductivity Max = 4 µmho/cm** | ⚠ Medium | Row 65 (Gujarat, CANAL): Max=4 while Min=212. Almost certainly a Min/Max swap error. |
| **Coliform values of 14,000,000 MPN/100ml** | ⚠ Review needed | Row 136 (Delhi, Agra Canal): Both FC Max and TC Max = 14,000,000. Extremely high but potentially real for highly polluted urban canals. Should be verified against source. |
| **BOD Max = 90 mg/L** | ⚠ Review needed | Row 163 (Himachal Pradesh, drain). Very high BOD for wastewater drain — plausible but extreme. |
| **Conductivity >10,000 µmho/cm** | ✅ Contextually valid | High values are all from MARINE, SEA, BEACH, and some CANAL rows in Andhra Pradesh and Goa — expected for saline/marine water bodies. Not an error. |
| **BDL values in measurement columns** | ⚠ Handling required | Must not be treated as 0 or as missing. Standard options: replace with `detection_limit / 2`, or flag as a binary indicator. |

---

## 10. Outlier Summary (IQR ×1.5 Method)

| Column | Outlier Count | Notes |
|---|---|---|
| Temperature (C) - Min | 0 | Clean |
| Temperature (C) - Max | 3 | Values 8–11°C — possible Himalayan/winter readings |
| Dissolved - Min | 9 | Low values (0.3 mg/L) — severely hypoxic/polluted sites |
| Dissolved - Max | 9 | Mix of very low and very high values |
| pH - Min | 2 | 5.7 (mildly acidic) and 8.5 (mildly alkaline) — borderline |
| pH - Max | 2 | 6.6 (low) and 11.2 (very alkaline — possible STP/industrial) |
| Conductivity - Min | 29 | Driven by saline coastal stations |
| Conductivity - Max | 38 | Same cause — not errors |
| BOD - Min | 13 | Highly polluted drains and canals |
| BOD - Max | 30 | Highly polluted drains and canals |
| NitrateN - Min | 13 | Elevated nitrate — agricultural/sewage runoff |
| NitrateN - Max | 21 | Same |
| Fecal Coliform - Min | 16 | Highly polluted stations (STP outlets, canals) |
| Fecal Coliform - Max | 21 | Same; extreme outlier at 14,000,000 MPN/100ml |
| Total Coliform - Min | 8 | 1 extreme outlier: 790,000 |
| Total Coliform - Max | 16 | Extreme outlier: 14,000,000 |
| Fecal - Min | 2 | Values of 460 |
| Fecal - Max | 5 | Values up to 1,100 |

> **Note:** For Conductivity, outliers are contextually valid (coastal/saline water bodies). For Coliform and BOD, outliers reflect genuine extreme pollution and should be **retained**, not removed.

---

## 11. Date/Time Columns

**No datetime columns are present.** The `Year` column contains integer years (2021, 2022, 2023) only. No month, day, or timestamp information is available. This limits time-series analysis to annual granularity at best.

---

## 12. Geographic / Location Columns

| Column | Nature |
|---|---|
| `State Name` | Indian state — 17 states covered |
| `Monitoring Location` | Free-text description; includes river names, dam names, bridge names, city/district references |
| `Type Water Body` | Water body type (River, Canal, Lake, Marine, etc.) |

**No latitude/longitude columns are present.** Geographic analysis is limited to state-level and water-body-type aggregations unless external geo-coding is applied to station names.

---

## 13. Water-Quality Measurement Variables

All measurement columns represent **annual range summaries** (Min and Max observed values at a station over the year), not individual spot measurements.

| Parameter | Column Indices | WHO/BIS Relevance |
|---|---|---|
| **Temperature (°C)** | 5, 6 | Affects DO saturation and biological activity |
| **Dissolved Oxygen (mg/L)** *(name truncated)* | 7, 8 | Critical for aquatic life; <4 mg/L = hypoxic |
| **pH** | 9, 10 | BIS drinking standard: 6.5–8.5 |
| **Electrical Conductivity (µmho/cm)** | 11, 12 | Indicator of dissolved salts/TDS |
| **BOD (mg/L)** | 13, 14 | Organic pollution indicator; BIS Class B river: ≤3 mg/L |
| **Nitrate-N (mg/L)** | 15, 16 | Nutrient pollution; WHO limit: 11.3 mg/L as N |
| **Fecal Coliform (MPN/100ml)** | 17, 18 | Sewage/pathogen contamination |
| **Total Coliform (MPN/100ml)** | 19, 20 | General microbial contamination |
| **Fecal - Min/Max** *(name truncated)* | 21, 22 | Unknown — possibly a second fecal indicator; 52.6% missing |

---

## 14. Target / Label for Machine Learning

### Finding: No Pre-Existing Target Label

The dataset **does not contain any explicit quality label, water quality class, grade, rating, or status column**. There is no "Good/Poor", "Class I/II/III", "Potable/Non-potable", or "WQI score" column present.

### Constructable Targets (if engineering is approved)

A target variable would need to be **derived/engineered** from the measurement columns using a standard index. Two legitimate options exist:

| Option | Description | Feasibility |
|---|---|---|
| **BOD-based class** | Apply Central Pollution Control Board (CPCB) Designated Best Use (DBU) classification: BOD ≤ 2 = Class A/B, ≤ 3 = Class C, ≤ 6 = Class D, > 6 = Class E | Feasible using BOD columns alone; simple rule-based label |
| **Water Quality Index (WQI)** | Compute a weighted index from DO, pH, BOD, Conductivity, Nitrate, Fecal Coliform, Total Coliform per standard formulas (e.g., NSF-WQI or BIS-WQI), then classify into Good/Medium/Poor/Very Poor | More holistic; requires handling of BDL values and missing data (~7% per column) |
| **Potability binary flag** | Binary: pH in 6.5–8.5 AND BOD ≤ 3 AND FC ≤ 10 AND TC ≤ 50 (BIS IS:10500 drinking water limits) | Oversimplifies; also many rows are rivers/drains not intended for drinking |

### Recommendation

**WQI-based regression or classification** is the most scientifically defensible approach for this dataset, provided the engineering methodology is documented and transparent.

---

## 15. Potential Input Features

If a WQI or CPCB-class target is derived, the following columns are candidate features:

| Feature | Type | Notes |
|---|---|---|
| `State Name` | Categorical | 17 classes — encode as label or one-hot |
| `Type Water Body` | Categorical | 11 classes — strong domain signal |
| `Year` | Ordinal | 3 values — may capture temporal trend |
| `Temperature (C) - Min/Max` | Numeric | Low missing rate |
| `Dissolved - Min/Max` | Numeric | 1 missing + 1 BDL; rename/confirm first |
| `pH - Min/Max` | Numeric | Complete — 0 missing |
| `Conductivity - Min/Max` | Numeric | 6.7% missing; large saline outliers |
| `BOD - Min/Max` | Numeric | 6.7–7.7% missing; 11 BDL |
| `NitrateN - Min/Max` | Numeric | 6.7% missing; 2 BDL |
| `Fecal Coliform - Min/Max` | Numeric | 6.7% missing; 4 BDL |
| `Total Coliform - Min/Max` | Numeric | 7.2–7.7% missing; 1 dash |
| `Fecal - Min/Max` | Numeric | **⚠ 32–53% missing** — very high; risky to use |

**Excluded from features:** `STN code` (ID), `Monitoring Location` (free text, 181 unique values), `Year` (can be kept as ordinal if temporal generalisation matters).

---

## 16. Target Leakage Risks

| Risk | Columns Involved | Assessment |
|---|---|---|
| **If BOD-based class is the target** | BOD Min/Max used to create the label | Using BOD as a feature AND as the basis for the label is **direct leakage**. BOD columns must be excluded from features if a BOD-class target is used. |
| **If WQI is the target** | All measurement columns contribute to WQI formula | All measurement columns used in the WQI calculation would be direct leakage if also used as features. The standard ML approach is: compute WQI as the target, then use a subset of the same columns as features (representing a model that estimates WQI from partial measurements). This is methodologically acceptable but must be explicitly documented. |
| **`Monitoring Location` and `STN code`** | Columns 0, 1 | These are location identifiers. If the same station appears in train and test splits, the model may memorise station-level patterns rather than learn generalised water chemistry relationships. **Split by station** (not by random row) to avoid location leakage. |
| **`Year` column** | Column 2 | Only 3 years present. If 2021/2022 rows from the same station appear in both train and test, information leakage exists. |

---

## A. Dataset Summary

- **File:** `data/Indian_water_data.csv` — 194 rows × 23 columns, no duplicate rows
- **Coverage:** 17 Indian states, 11 water body types, years 2021–2023
- **Nature:** Annual water quality monitoring data; each row = one station × one year, reporting Min and Max of 9 physical/chemical/biological parameters
- **Source likely:** India's Central Pollution Control Board (CPCB) National Water Quality Monitoring Programme (NWMP)
- **Dataset size is very small** (194 rows) — constrains complex ML architectures; simpler models (Random Forest, Gradient Boosting, Logistic Regression) are appropriate

---

## B. Data-Quality Issues

| # | Issue | Impact | Action Required |
|---|---|---|---|
| 1 | Two column names are truncated (`Dissolved` and `Fecal`) | Cannot confirm what is being measured | Verify against CPCB source before analysis |
| 2 | µ symbol encoding corruption in column names | Cosmetic; no data loss | Fix column name in preprocessing |
| 3 | BDL ("Below Detection Limit") in 8 columns (1–11 occurrences each) | Cannot treat as 0 or NaN without justification | Use `detection_limit / 2` substitution or add binary BDL indicator column |
| 4 | Dash (`-`) values in 3 columns | Meaning unclear (not measured vs. zero) | Treat as NaN during preprocessing; document assumption |
| 5 | Conductivity Min > Max in 5 rows | Data entry error (likely transposed values) | Swap values if confirmed, or flag as suspect |
| 6 | Fecal Coliform Min > Max in 10 rows | Data entry error | Swap values if confirmed, or exclude rows |
| 7 | Columns 21/22 (`Fecal - Min/Max`) have 32–53% missing | Near-unusable for modelling | Exclude from model or analyse separately |
| 8 | Extreme coliform values (14,000,000 MPN/100ml) in 2 cells | Potential outlier or real pollution; distorts mean | Verify against source; apply log-transform |
| 9 | Highly imbalanced state coverage | Himachal Pradesh (49), Assam (46) vs. Uttar Pradesh (1), Odisha (1) | Account for class imbalance in state-level analysis |
| 10 | No latitude/longitude data | Limits geospatial mapping | Would require external geocoding |

---

## C. Possible Analytical Questions

1. **Which Indian states have the worst water quality by BOD and Coliform levels?**
2. **Which water body types (rivers vs. drains vs. lakes) show highest pollution levels?**
3. **Has water quality improved, stayed the same, or worsened between 2021–2023?** (limited to 26 multi-year stations)
4. **Which parameters co-vary most strongly with BOD (a key pollution indicator)?**
5. **Which stations consistently exceed BIS/WHO limits for drinking water across multiple parameters?**
6. **Can a WQI score be computed for each station, and what are the worst/best stations?**
7. **Is there a geographic pattern — do Himalayan rivers (Himachal Pradesh, Uttarakhand) show better water quality than plains rivers?**
8. **Do STPs and Water Treatment Plants show different parameter profiles compared to natural water bodies?**

---

## D. Candidate ML Targets (Supported by Data)

**No ready-made target exists in the data.** The following are constructable, with conditions:

| Target | Type | Construction Method | Conditions |
|---|---|---|---|
| **WQI Score (continuous)** | Regression | Compute a weighted index from DO, pH, BOD, Conductivity, Nitrate, FC, TC using NSF-WQI or BIS formula | Requires handling BDL and missing values first; well-documented engineering step |
| **WQI Category (ordinal)** | Multi-class classification | Bin WQI score into Excellent / Good / Medium / Poor / Very Poor | Same as above; derived from the regression target |
| **CPCB-class (BOD-based)** | Multi-class classification | Apply CPCB DBU classification rules to BOD columns | BOD columns then **cannot** be used as features (leakage) |

**Both of the first two targets are most defensible** for an analytics project, as WQI uses multiple parameters rather than a single variable.

---

## E. Target-Leakage Risks

1. **Direct feature-target overlap:** Any column used to compute the target (WQI or CPCB class) must be carefully documented. Using those same raw values as model features is technically valid for a "WQI estimator" framing but must be stated explicitly.
2. **Station-level leakage:** 26 stations appear in 2 years. If the same station is in both train and test sets, the model may overfit to station identity rather than water chemistry. **Use station-stratified or year-based splitting.**
3. **Location name leakage:** `Monitoring Location` (181 unique values) and `STN code` (168 unique values) are identifiers — they must be **excluded** as features.
4. **Water body type confound:** `Type Water Body` is a strong categorical signal (DRAIN/STP inherently polluted, MARINE inherently high conductivity). Including it is valid but its role should be examined carefully to avoid a proxy-leakage scenario if the target is correlated with water body type by construction.

---

## F. Recommended Next Step

> **Awaiting project owner approval before proceeding.**

Once approved, the recommended next step is:

**Step 2 — Data Pre-Processing & Target Engineering**, which should include:
1. Confirm the full names of truncated columns 7/8 and 21/22 against the CPCB source document
2. Fix the µ encoding in column 11/12 names
3. Handle BDL values (substitution strategy)
4. Correct or flag the 15 Min > Max anomalies (5 Conductivity + 10 Fecal Coliform)
5. Decide on a WQI formula and compute the target variable
6. Apply log-transform to right-skewed Coliform and Conductivity columns
7. Handle remaining missing values (imputation or row exclusion)
8. Define the train/test split strategy (station-stratified recommended)

---

*All findings in this report are based exclusively on the actual contents of `data/Indian_water_data.csv`. No data has been synthesised, modified, or overwritten.*
