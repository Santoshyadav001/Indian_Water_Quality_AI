# PROJECT PLAN
## Indian Water Quality Analytics and WQI Prediction using Machine Learning
**AICTE | IBM SkillsBuild Data Analytics with AI Internship 2026**

---

> **Status:** Planning Stage — awaiting approval before implementation begins.  
> **Rule:** Every section in this plan must be traceable to the actual verified dataset. Nothing is invented.

---

## 1. Project Title

**Indian Water Quality Analytics and WQI Prediction using Machine Learning**

---

## 2. Problem Statement

India's Central Pollution Control Board (CPCB) monitors hundreds of surface-water stations annually, measuring parameters such as dissolved oxygen, pH, BOD, conductivity, nitrate, and coliform bacteria. The raw monitoring data is multi-parametric and difficult to interpret holistically. There is no single, unified quality score in the dataset.

This project addresses two interlinked problems:

1. **Analytics problem:** Given annual Min–Max monitoring readings across 194 station-year records spanning 17 states and 11 water-body types, what is the spatial, temporal, and categorical pattern of water quality in India (2021–2023)?

2. **Machine-learning problem:** Given a subset of easily-measured water-quality parameters, can a model reliably estimate the Water Quality Index (WQI) that would be produced by the full suite of measurements? This would be useful when not all parameters are measured at every station.

---

## 3. Business and Environmental Motivation

- Access to safe water is a constitutional right in India and a UN Sustainable Development Goal (SDG 6).
- Surface water quality degradation due to industrial discharge, sewage, and agricultural runoff is documented extensively in Indian monitoring data.
- A WQI compresses multi-parameter complexity into a single actionable number, aiding policy-makers, regulators, and the public.
- An ML model that can estimate WQI from partial measurements could reduce the cost of comprehensive water testing for low-resource monitoring stations.
- Temporal trends (2021–2023) provide early signals of improvement or deterioration.

---

## 4. Dataset Description

| Attribute | Value |
|---|---|
| File | `data/Indian_water_data.csv` |
| Format | CSV, UTF-8 with BOM |
| Rows | 194 (station × year records) |
| Columns | 23 |
| Duplicate rows | 0 |
| Unique stations | 168 STN codes |
| Stations in multiple years | 26 (appear in 2 years) |
| States covered | 17 |
| Water-body types | 11 |
| Years | 2021, 2022, 2023 |
| Measurement structure | Each row = one station, one year; columns report the annual Min and Max of each parameter |
| Pre-existing ML target | None |

Each measurement column pair (Min/Max) represents the observed annual range at a station, not individual spot readings. All quality assessments and derived indices will be computed using the **mean of Min and Max** as the representative annual value for that parameter at that station, unless the WQI methodology specifies otherwise (see Section 9).

---

## 5. Data-Quality Issues Discovered

All issues were discovered during the dataset audit. No issues are assumed.

| # | Issue | Affected Columns | Rows Affected | Severity |
|---|---|---|---|---|
| DQ-01 | Column names truncated | `Dissolved - Min/Max` (cols 7–8); `Fecal - Min/Max` (cols 21–22) | All rows | High |
| DQ-02 | µ symbol encoding corruption in column names | `Conductivity (µmho/cm)` (cols 11–12) | Cosmetic | Low |
| DQ-03 | BDL ("Below Detection Limit") string values | 8 columns | 1–18 per column | Medium |
| DQ-04 | Dash (`-`) string values | Cols 19, 21, 22 | 1–7 per column | Medium |
| DQ-05 | Conductivity Min > Max (data entry error or swap) | Cols 11–12 | 5 rows | Medium |
| DQ-06 | Fecal Coliform Min > Max (data entry error or swap) | Cols 17–18 | 10 rows | Medium |
| DQ-07 | `Fecal - Min` 32% missing | Col 21 | 62 rows | High |
| DQ-08 | `Fecal - Max` 52.6% missing | Col 22 | 102 rows | High |
| DQ-09 | Extreme coliform value: 14,000,000 MPN/100ml | Cols 18, 20 | 1 row (Row 136, Delhi Agra Canal) | Medium |
| DQ-10 | BOD Max = 90 mg/L (extreme) | Col 14 | 1 row (Row 163, HP Drain) | Low–Medium |
| DQ-11 | Conductivity values >10,000 µmho/cm | Cols 11–12 | ~28 rows (Marine/Beach/Sea) | Contextually valid |
| DQ-12 | Highly imbalanced state coverage | `State Name` | N/A | Medium |

---

## 6. Analytical Objectives

1. Describe the spatial distribution of water quality across 17 Indian states.
2. Compare water quality across 11 water-body types (rivers, canals, drains, marine, etc.).
3. Analyse temporal trends for the 26 stations with multi-year data.
4. Identify the most polluted and cleanest stations.
5. Compute parameter-level correlation analysis (e.g., BOD vs. DO, FC vs. TC).
6. Visualise geographic and categorical patterns using charts and state-level summaries.
7. Compute a WQI score for every station-year record and classify quality levels.
8. Identify which states and water-body types most frequently fall below safe thresholds.

---

## 7. ML Objective

Train a supervised regression model to **estimate the WQI score** of a station-year record from a subset of its measured parameters.

**Practical framing:** In real-world monitoring, some parameters may not be available. Given the 4 most routinely measured parameters (DO, pH, BOD, and one coliform measure), can we estimate what the full 7-parameter WQI would be?

**Why this is not pure leakage:** The model takes a *subset* of parameters as input and predicts the WQI computed from the *full set*. This is a valid regression-from-partial-information scenario, analogous to imputing a composite score from partial sub-scores.

**Honest acknowledgement:** Because WQI is a deterministic weighted formula of its inputs, a model trained on all WQI component features will learn the formula near-perfectly. The defensible ML framing is deliberately partial-feature prediction. This is documented explicitly.

---

## 8. Exact Proposed Target Variable

**Target: WQI_score** — a continuous numerical value in the range [0, 100+], computed using the Weighted Arithmetic WQI method.

- WQI is computed per station-year record using 7 parameters: DO, pH, BOD, Conductivity, Nitrate-N, Fecal Coliform, Total Coliform.
- The **annual mean** value per parameter = (Min + Max) / 2 is used as the representative measurement.
- WQI is then categorised into 5 quality classes for classification tasks (see Section 9).

The WQI column will be added to a **processed dataset** only. The raw CSV is never modified.

---

## 9. Exact WQI Methodology Proposed

### Methodology: Modified Weighted Arithmetic WQI

> **⚠ LABEL: MODIFIED/CUSTOM INDEX — not a single published standard.**

**Base formula source:** Brown, R.M., McClelland, N.I., Deininger, R.A., and Tozer, R.G. (1970). *"A Water Quality Index — Do We Dare?"* Water and Sewage Works, 117, pp. 339–343.

**Indian surface-water adaptation cited as reference:**
Tyagi S., Sharma B., Singh P., Dobhal R. (2013). *"Water Quality Assessment in Terms of Water Quality Index."* American Journal of Water Resources, 1(3), 34–38. DOI: 10.12691/ajwr-1-3-3.

**⚠ UNVERIFIED (UV-09):** The exact formula form, parameter set, Si values, and classification thresholds used in Tyagi et al. (2013) have not been verified against the original paper. The paper is cited as a reference for the approach; the specific parametrisation below is assembled from the available dataset columns and published Indian standards. Any deviation from the cited paper must be explicitly documented in the report.

**What is taken from an established source:**
- The formula structure `WQI = Σ(Qi × Wi) / Σ(Wi)` and `Wi = K/Si` from Brown (1970)

**What is a project-specific adaptation (not from a single canonical source):**
- Selection of these 7 parameters for this dataset
- The Si (standard) values chosen for each parameter (see table below)
- The pH absolute-deviation sub-index formula
- The DO inversion sub-index formula
- The `(Min + Max) / 2` annual representative value (see UV-08)
- The classification thresholds

**This index must be described in the report as:** *"A modified Weighted Arithmetic WQI following the formula structure of Brown (1970) as applied in Indian surface-water studies, with parameter selection, standard values, and sub-index adaptations specific to this dataset and project. It is not identical to any single published index."*

---

### Formula

**Step 1: Compute annual mean value per parameter**

```
C_i = (Min_i + Max_i) / 2
```

**Step 2: Compute unit weight (Wi) for each parameter**

```
W_i = K / S_i
```
where:
- `S_i` = standard/permissible limit for parameter i (from BIS IS:10500-2012 or CPCB guideline)
- `K` = proportionality constant = 1 / Σ(1/S_i)

This ensures weights are inversely proportional to the allowable standard: stricter standards receive higher weight.

**Step 3: Compute sub-index quality rating (Q_i) for each parameter**

```
Q_i = ((C_i - V_ideal_i) / (S_i - V_ideal_i)) × 100
```
where:
- `C_i` = observed mean concentration of parameter i
- `S_i` = permissible standard for parameter i
- `V_ideal_i` = ideal (pure water) value for parameter i

For DO: Q_i is inverted — DO is beneficial, not detrimental:
```
Q_DO = ((C_DO - 0) / (S_DO - 0)) × 100
     = (C_DO / S_DO) × 100
```

**Step 4: Compute WQI**

```
WQI = Σ(Q_i × W_i) / Σ(W_i)
```

---

### Standard Values (S_i) and Ideal Values (V_ideal_i) to Be Used

All standards are sourced from **BIS IS:10500-2012** (drinking water) and **CPCB Designated Best Use (DBU) criteria for surface water (IS:2296-1982)** where no BIS drinking standard applies.

| Parameter | S_i (Standard) | V_ideal_i (Ideal/Pure Water) | Source |
|---|---|---|---|
| DO (mg/L) | 6.0 (CPCB Class B minimum) | 14.6 (max saturation ~0°C) | CPCB DBU / CPCB 2015 |
| pH | 7.0 (neutral, ideal) / deviation computed differently | 7.0 | BIS IS:10500-2012 |
| BOD (mg/L) | 3.0 (CPCB Class B/C river standard) | 0.0 | CPCB DBU |
| Conductivity (µmho/cm) | 300.0 (BIS acceptable limit) | 0.0 | BIS IS:10500-2012 |
| Nitrate-N (mg/L as N) | 10.2 (= 45 mg/L as NO3, BIS IS:10500-2012) | 0.0 | BIS IS:10500-2012 |
| Fecal Coliform (MPN/100ml) | 500.0 (CPCB Class B bathing) | 0.0 | CPCB DBU |
| Total Coliform (MPN/100ml) | 5000.0 (CPCB Class C raw water) | 0.0 | CPCB DBU |

> **⚠ Engineering Decision (documented):** For pH, the sub-index rating uses absolute deviation from the ideal value of 7.0:
> `Q_pH = |C_pH − 7.0| / |S_pH − 7.0| × 100`
> where S_pH = 8.5 (upper BIS permissible limit); thus `|S_pH − 7.0| = 1.5`.

> **⚠ Engineering Decision (documented):** DO sub-index is inverted from the standard Q_i formula (higher DO = better quality) using: `Q_DO = (C_DO / S_DO) × 100`, capped at 100. If `C_DO >= S_DO`, `Q_DO = 100`.

> **⚠ Engineering Decision (documented):** Conductivity S_i = 300 µmho/cm (BIS acceptable limit). For MARINE, SEA, and BEACH water bodies, conductivity reflects salinity and is not applicable to the drinking/surface-water WQI; these observations will be **excluded** from WQI computation or flagged as "not applicable for WQI" with a separate analysis.

---

### WQI Classification

Based on the scale in Tyagi et al. (2013) and consistent with the majority of Indian WQI literature:

| WQI Range | Water Quality Category |
|---|---|
| 0 – 25 | Excellent |
| 26 – 50 | Good |
| 51 – 75 | Poor |
| 76 – 100 | Very Poor |
| > 100 | Unsuitable for Drinking |

---

## 10. Authoritative Source for WQI Methodology

**Primary methodological source:**

> Brown, R.M., McClelland, N.I., Deininger, R.A., and Tozer, R.G. (1970).  
> *"A Water Quality Index — Do We Dare?"*  
> Water and Sewage Works, 117, 339–343.

**Indian application reference:**

> Tyagi S., Sharma B., Singh P., Dobhal R. (2013).  
> *"Water Quality Assessment in Terms of Water Quality Index."*  
> American Journal of Water Resources, 1(3), 34–38.  
> DOI: 10.12691/ajwr-1-3-3

**Standard reference for parameter limits:**

> Bureau of Indian Standards (2012). *IS:10500 — Drinking Water Specification (Second Revision).*  
> New Delhi: BIS.

> Central Pollution Control Board (CPCB) (2015). *Guidelines for Water Quality Management.*  
> Ministry of Environment, Forest and Climate Change, Government of India.

**Why not NSF-WQI?**  
The National Sanitation Foundation WQI (Brown et al., 1970, as later developed into the NSF form) requires Turbidity (NTU), Total Phosphate (mg/L), and Total Solids (mg/L) — none of which are present in this dataset. The NSF-WQI cannot be computed from the available data.

**Why not CCME-WQI?**  
The Canadian Council of Ministers of the Environment WQI uses a frequency/amplitude/scope approach that requires individual spot measurements and exceedance counts across multiple visits — not annual Min/Max summaries. It is not directly applicable to this dataset's structure.

---

## 11. Explanation of Why This WQI Methodology Is Appropriate

1. **Data compatibility:** The Weighted Arithmetic WQI method requires only the 7 parameters that are all present in our dataset (DO, pH, BOD, Conductivity, Nitrate-N, FC, TC).
2. **Indian standard alignment:** Standards used (BIS IS:10500-2012 and CPCB DBU) are the official Indian regulatory thresholds.
3. **Wide precedent:** This methodology is the most widely used WQI computation approach in peer-reviewed Indian water quality studies, making our results directly comparable.
4. **Deterministic and reproducible:** Given fixed standard values, the formula is fully reproducible. Every step is documented and traceable.
5. **Compatible with annual summary data:** Computing `(Min + Max) / 2` as the representative annual concentration is an established practice when only range data is available.

---

## 12. Exact Variables Used to Calculate WQI

The following 7 parameters will be used for WQI calculation. The annual mean is derived from the Min/Max pair:

| Parameter | Source Columns | Derived Value |
|---|---|---|
| DO (mg/L) | `Dissolved - Min`, `Dissolved - Max` | `(Dissolved_Min + Dissolved_Max) / 2` |
| pH | `pH - Min`, `pH - Max` | `(pH_Min + pH_Max) / 2` |
| BOD (mg/L) | `BOD (mg/L) - Min`, `BOD (mg/L) - Max` | `(BOD_Min + BOD_Max) / 2` |
| Conductivity (µmho/cm) | `Conductivity - Min`, `Conductivity - Max` | `(Cond_Min + Cond_Max) / 2` |
| Nitrate-N (mg/L) | `NitrateN (mg/L) - Min`, `NitrateN (mg/L) - Max` | `(Nitrate_Min + Nitrate_Max) / 2` |
| Fecal Coliform (MPN/100ml) | `Fecal Coliform (MPN/100ml) - Min`, `Fecal Coliform (MPN/100ml) - Max` | `(FC_Min + FC_Max) / 2` |
| Total Coliform (MPN/100ml) | `Total Coliform (MPN/100ml) - Min`, `Total Coliform (MPN/100ml) - Max` | `(TC_Min + TC_Max) / 2` |

**Excluded from WQI computation:**
- Temperature: Not included in the selected WQI formula (no delta-T from equilibrium available)
- `Fecal - Min/Max` (cols 21–22): Name truncated, meaning unverified, 32–53% missing — excluded
- MARINE, SEA, BEACH water bodies: Conductivity is dominated by salinity and is not meaningful for the drinking/surface-water WQI standard; these rows will receive a `WQI_applicable = False` flag

---

## 13. Exact Variables Allowed as ML Features

### The ML Prediction Problem (Partial-Feature Framing)

**Target:** `WQI_score` (computed from all 7 parameters above)

**Model input features:** A subset that does NOT include all 7 WQI component means.

The defensible feature set for ML prediction is:

| Feature | Type | Rationale |
|---|---|---|
| `Type_Water_Body` | Categorical (11 classes) | Strong contextual predictor; not a WQI component |
| `State_Name` | Categorical (17 classes) | Geographic signal; not a WQI component |
| `Year` | Ordinal (2021–2023) | Temporal signal; not a WQI component |
| `Temp_mean` = (Temp_Min + Temp_Max) / 2 | Numeric | Not in WQI formula — valid feature |
| `DO_mean` = (Dissolved_Min + Dissolved_Max) / 2 | Numeric | **Also a WQI component — see leakage analysis** |
| `pH_mean` = (pH_Min + pH_Max) / 2 | Numeric | **Also a WQI component — see leakage analysis** |
| `BOD_mean` = (BOD_Min + BOD_Max) / 2 | Numeric | **Also a WQI component — see leakage analysis** |

**Deliberately withheld from features (to create partial-information prediction):**
- `Conductivity_mean` — withheld
- `Nitrate_mean` — withheld
- `FC_mean` (Fecal Coliform) — withheld
- `TC_mean` (Total Coliform) — withheld

This framing asks: *"Given temperature, DO, pH, BOD, water body type, and state, can the model predict the WQI that would result from measuring all 7 parameters?"* This is a realistic partial-observation scenario.

**Alternative full-feature baseline model:** A second model using all 7 WQI component means as features will also be trained, clearly labelled as "WQI formula approximation / upper bound", not treated as a real predictive model.

---

## 14. Explicit Target-Leakage Analysis

| Leakage Type | Risk | Mitigation |
|---|---|---|
| **Direct formula leakage** | Using all 7 WQI component means as input features means the model can reconstruct the formula exactly — not genuine prediction | Primary ML model uses only partial features (Temp, DO, pH, BOD + categoricals). Full-feature model is labelled as an approximation baseline only. |
| **Station-level leakage** | 26 stations appear in 2 different years. Random splitting could place Year 1 of station X in train and Year 2 in test — the model may memorise station identity. | Station-stratified group split: all records for a given STN code go to the same partition (see Section 24–25). |
| **Location name leakage** | `Monitoring Location` (181 unique values) and `STN code` (168 unique values) are identifiers. They encode station identity and would cause near-perfect memorisation if included as features. | Both columns are excluded from all ML feature sets. |
| **Water body type confound** | `Type Water Body` correlates with WQI by construction (DRAIN/STP stations always score poorly). Including it as a feature is valid but risks the model learning type → WQI instead of chemistry → WQI. | Include it as a feature but test model performance with and without it; report both. |
| **Indirect leakage via target encoding** | If state or water-body-type is encoded using the mean WQI value (target encoding), future data leaks into encoding. | Use one-hot encoding or ordinal encoding; never mean/target encoding on this dataset. |

---

## 15. Treatment of BDL Values

**BDL = "Below Detection Limit"** — the parameter was measured but the result was below the instrument's detection threshold. It is NOT equivalent to zero or to missing.

**Plan:**
1. During preprocessing, identify all BDL occurrences (found in 8 columns, 18 values total across the 6 WQI-relevant columns).
2. Replace BDL with `detection_limit / 2` — the standard environmental science substitution when the measured value is known only to be below the detection threshold (US EPA QA/G-5, 2002; WHO Guidelines for Drinking-water Quality).
3. **Problem:** The actual detection limits for each parameter at each CPCB monitoring station are NOT present in the dataset and have not been sourced from CPCB documentation.
4. **⛔ UNVERIFIED substitution values (UV-06):** In the absence of confirmed detection limits, the following conservative published typical instrument MDLs are used as a proxy. These are **NOT confirmed from the dataset source** and must be disclosed as approximations:
   - DO (assumed): **⛔ UNVERIFIED** — proposed 0.1 mg/L / 2 = 0.05 mg/L (typical electrochemical DO meter MDL)
   - BOD: **⛔ UNVERIFIED** — proposed 0.5 mg/L / 2 = 0.25 mg/L (typical BOD₅ test MDL)
   - Conductivity: **⛔ UNVERIFIED** — proposed 1.0 µmho/cm / 2 = 0.5 µmho/cm (typical conductivity meter MDL)
   - Nitrate-N: **⛔ UNVERIFIED** — proposed 0.1 mg/L / 2 = 0.05 mg/L (typical ion chromatography MDL)
   - Fecal Coliform: **⛔ UNVERIFIED** — proposed 2 MPN/100ml / 2 = 1 MPN/100ml (MPN tube-series lower bound)
   - Total Coliform: **⛔ UNVERIFIED** — proposed 2 MPN/100ml / 2 = 1 MPN/100ml (same)
5. Impact is minimal: only 18 BDL values exist across all 6 WQI columns in a 194-row dataset. Even if the substitution value is off by a factor of 2, the effect on the aggregate WQI score is negligible.
6. Each BDL replacement is logged with a `{col}_BDL_flag = 1` companion column and recorded in the preprocessing audit trail.
7. **Required report language:** *"BDL values (n = 18) are substituted with half of a published typical instrument detection limit for each parameter. The actual detection limits for CPCB monitoring stations are unavailable; the substituted values are unverified approximations and are flagged accordingly."*

---

## 16. Treatment of Dash (`-`) Values

**Dash (`-`) values** appear in 3 columns (Total Coliform Min: 1 occurrence; Fecal-Min: 7 occurrences; Fecal-Max: 7 occurrences). Their meaning is ambiguous — they may mean "not measured," "not applicable," or "zero."

**Plan:**
1. Treat all dash values as `NaN` (missing/not measured).
2. Flag them with a companion `{col}_dash_flag = 1` column.
3. Do NOT substitute a numeric value for dash entries — the meaning is too ambiguous.
4. If a WQI-required parameter has a dash, that station-year record will be excluded from WQI computation and flagged as `WQI_score = NaN` with reason `incomplete_parameters`.

---

## 17. Treatment of Min > Max Anomalies

**15 total anomalous rows:** 5 Conductivity rows + 10 Fecal Coliform rows.

**Plan:**
1. All 15 anomalous rows are **preserved in the raw processed dataset** — not deleted.
2. A flag column is added: `{param}_minmax_anomaly = True` for each affected row.
3. Treatment for derived mean: `(Min + Max) / 2` is computed regardless — the mean of swapped values is identical to the mean of correct values, so the mean is unaffected by the swap.
4. The individual Min/Max columns for these rows will NOT be automatically corrected (the source data cannot be verified).
5. Any analysis or visualisation using Min or Max individually (e.g., "worst-case reading") will exclude flagged rows or use the correct directionality check.

> **⚠ Documented decision:** These anomalies are documented but not auto-corrected. If the dataset source (CPCB) is consulted and the swap is confirmed, corrections can be applied in a documented patch step.

---

## 18. Treatment of Extreme Values

**Extreme values identified:**
- Fecal Coliform Max = 14,000,000 MPN/100ml (Row 136: Delhi Agra Canal)
- Total Coliform Max = 14,000,000 MPN/100ml (same row)
- BOD Max = 90 mg/L (Row 163: Himachal Pradesh drain)
- Conductivity >10,000 µmho/cm (~28 rows for marine/beach/sea locations)

**Plan:**
1. **Retain all extreme values** in the processed dataset — they represent real pollution or environmental conditions.
2. Marine/beach/sea conductivity extremes: Contextually valid (saline water) — retain but flag with `WQI_applicable = False` for those water-body types.
3. For ML modelling: Apply **log1p transformation** (`log(1 + x)`) to right-skewed columns: Fecal Coliform, Total Coliform, Conductivity, BOD. This stabilises variance without removing values.
4. A flag column `{col}_extreme = True` will mark values exceeding the 99th percentile of the column distribution.
5. Sensitivity analysis: Model performance will be checked with and without the 14,000,000 MPN outlier row to test its influence.

---

## 19. Treatment of Missing Values

| Column | Missing % | Strategy |
|---|---|---|
| Temperature Min/Max | 1.0% | Impute using median of same `Type Water Body` group |
| Dissolved (DO) Min/Max | 0.5% | Impute using median of same `Type Water Body` group |
| Conductivity Min/Max | 6.7% | Impute using median of same `Type Water Body` and `State Name` group |
| BOD Min/Max | 6.7–7.7% | Impute using median of same `Type Water Body` group |
| NitrateN Min/Max | 6.7% | Impute using median of same `State Name` group |
| Fecal Coliform Min/Max | 6.7% | Impute using median of same `Type Water Body` group |
| Total Coliform Min/Max | 7.2–7.7% | Impute using median of same `Type Water Body` group |
| **Fecal - Min** | **32.0%** | **Exclude from all analysis and modelling** (truncated name + high missingness) |
| **Fecal - Max** | **52.6%** | **Exclude from all analysis and modelling** (truncated name + high missingness) |

**General rules:**
- All imputation is performed **after** the train/test split — imputation statistics (medians) are computed on the training set only, then applied to validation/test sets.
- An `{col}_imputed_flag = 1` column is added for each imputed value to allow downstream awareness.
- Rows where more than 3 of the 7 WQI parameters remain missing after imputation will be excluded from WQI computation and labelled `WQI_insufficient_data = True`.

---

## 20. Treatment of Truncated Column Names

**Affected columns:**
- Columns 7–8: `Dissolved - Min` and `Dissolved - Max`
- Columns 21–22: `Fecal - Min` and `Fecal - Max`
- Columns 11–12: Encoding artefact (`µ` → `��`) in `Conductivity (µmho/cm)` — cosmetic only

**Plan:**

| Column | Status | Action |
|---|---|---|
| `Dissolved - Min/Max` | **⛔ UNVERIFIED — assumed to be Dissolved Oxygen (mg/L).** The CPCB source data dictionary has not been consulted. Value-range evidence (0.3–13.6) is consistent with DO mg/L and inconsistent with all other common dissolved parameters, but this is circumstantial evidence only, not confirmation. | Rename to `DO_assumed_mgL_min` / `DO_assumed_mgL_max` in the processed dataset. Every output (notebook cells, charts, report) must carry the label *"assumed Dissolved Oxygen"* until the CPCB source document confirms or refutes this interpretation. The original column name is always preserved in a metadata field. |
| `Fecal - Min/Max` | **⛔ UNVERIFIED — identity unknown.** Could be Fecal Streptococcus, Enterococcus, or a second FC measurement. 32–52% missing. Cannot be used. | **Excluded from all analysis and modelling.** Noted in the report as an unresolved data-source issue. |
| `Conductivity (µmho/cm)` | Encoding artefact only — no ambiguity in meaning. | Fix column name to `Conductivity_µmho_cm_min` / `max` in processed dataset. |

> **⛔ UNVERIFIED ASSUMPTION (UV-01):** `Dissolved - Min/Max` is treated as Dissolved Oxygen (DO) in mg/L. This interpretation is based solely on value-range consistency with the CPCB NWMP standard parameter set. It has NOT been confirmed against the CPCB data dictionary or any official source document. If this assumption is incorrect, all WQI sub-index calculations for DO are invalid.

---

## 21. Feature Engineering Plan

All engineered features are derived from raw columns. The raw CSV is never modified.

| Feature | Formula | Type | Notes |
|---|---|---|---|
| `Temp_mean` | (Temp_Min + Temp_Max) / 2 | Numeric | Annual mean temperature |
| `DO_mean` | (DO_Min + DO_Max) / 2 | Numeric | Annual mean dissolved oxygen |
| `pH_mean` | (pH_Min + pH_Max) / 2 | Numeric | Annual mean pH |
| `Cond_mean` | (Cond_Min + Cond_Max) / 2 | Numeric | Annual mean conductivity |
| `BOD_mean` | (BOD_Min + BOD_Max) / 2 | Numeric | Annual mean BOD |
| `Nitrate_mean` | (Nitrate_Min + Nitrate_Max) / 2 | Numeric | Annual mean Nitrate-N |
| `FC_mean` | (FC_Min + FC_Max) / 2 | Numeric | Annual mean Fecal Coliform |
| `TC_mean` | (TC_Min + TC_Max) / 2 | Numeric | Annual mean Total Coliform |
| `Temp_range` | Temp_Max − Temp_Min | Numeric | Seasonal temperature variability |
| `DO_range` | DO_Max − DO_Min | Numeric | DO variability (pollution stress) |
| `BOD_range` | BOD_Max − BOD_Min | Numeric | BOD variability |
| `log1p_FC` | log(1 + FC_mean) | Numeric | Log-transformed FC for ML |
| `log1p_TC` | log(1 + TC_mean) | Numeric | Log-transformed TC for ML |
| `log1p_Cond` | log(1 + Cond_mean) | Numeric | Log-transformed conductivity for ML |
| `log1p_BOD` | log(1 + BOD_mean) | Numeric | Log-transformed BOD for ML |
| `WQI_score` | Weighted Arithmetic formula | Numeric | **Target variable** — Section 9 |
| `WQI_category` | Bins from WQI_score | Ordinal (5 classes) | Classification target |
| `WQI_applicable` | False for MARINE/SEA/BEACH | Boolean | Conductivity not meaningful for WQI |
| `BDL_flag_{col}` | 1 if original value was BDL | Binary | Missing-mechanism indicator |
| `imputed_flag_{col}` | 1 if value was imputed | Binary | Imputation indicator |
| `minmax_anomaly_{col}` | 1 if Min > Max detected | Binary | Data quality flag |

---

## 22. EDA Plan

Exploratory Data Analysis will be conducted in a dedicated notebook section and will include:

1. **Univariate analysis:** Distribution plots for every numeric column; counts for categoricals.
2. **Bivariate analysis:**
   - Scatter plots: DO vs BOD, FC vs TC, BOD vs WQI.
   - Correlation heatmap across all 7 WQI parameters.
   - Box plots of WQI by water-body type and by state.
3. **Temporal analysis:** For the 26 multi-year stations, line plots of WQI across years.
4. **Outlier visualisation:** Box plots and IQR-based highlight plots for skewed columns.
5. **Missing value pattern:** Heatmap of missingness across rows and columns.
6. **BDL / anomaly distribution:** Bar chart showing count of BDL, dash, and Min>Max flags per column.
7. **State-level summary:** Bar chart of mean WQI per state (only for WQI-applicable rows).
8. **Water-body-type summary:** Bar chart of mean WQI per water-body type.

---

## 23. Visualisation Plan

All visualisations will be created using **Matplotlib** and **Seaborn**. No JavaScript or interactive library is required for the core deliverable; optional Plotly charts may be added for the dashboard.

| # | Plot Title | Type | Library | Notes |
|---|---|---|---|---|
| V01 | Distribution of WQI Scores | Histogram + KDE | Seaborn | Primary target distribution |
| V02 | WQI Category Counts | Bar chart | Matplotlib | Excellent/Good/Poor/Very Poor/Unsuitable |
| V03 | WQI by State | Horizontal bar chart | Matplotlib/Seaborn | Mean WQI with 95% CI |
| V04 | WQI by Water Body Type | Box plot | Seaborn | Grouped by 11 types |
| V05 | Parameter Correlation Heatmap | Heatmap | Seaborn | 7 WQI parameters + derived means |
| V06 | DO vs BOD Scatter | Scatter | Matplotlib | Colour-coded by WQI category |
| V07 | FC vs TC Scatter | Scatter | Matplotlib | Log scale both axes |
| V08 | Missing Value Heatmap | Heatmap | Seaborn/Missingno | Rows × columns |
| V09 | Temporal Trend (multi-year stations) | Line chart | Matplotlib | 26 stations, 2 years each |
| V10 | Top 10 Most Polluted Stations | Horizontal bar | Matplotlib | Ranked by WQI score |
| V11 | Top 10 Cleanest Stations | Horizontal bar | Matplotlib | Ranked by WQI score |
| V12 | Feature Importance | Bar chart | Sklearn/Matplotlib | From Random Forest model |
| V13 | Actual vs Predicted WQI | Scatter | Matplotlib | For primary ML model |
| V14 | Residual Plot | Scatter | Matplotlib | For primary ML model |
| V15 | India State-Level WQI Choropleth | Map (optional) | Plotly/Geopandas | State polygons from public shapefile |

Charts V01–V14 are mandatory. V15 (choropleth) is optional/stretch goal dependent on available shapefile.

All plots will be saved as PNG files to `report_images/`.

---

## 24. Train / Validation / Test Strategy

**Challenge:** Only 194 rows. 26 stations appear in 2 years (potential leakage).

**Strategy: Station-Stratified Group Split**

1. Group all rows by `STN code`.
2. Randomly assign STN codes (not individual rows) to train/validation/test partitions at a **70/15/15** ratio, stratified on `WQI_category` to preserve class distribution.
3. All rows belonging to a given STN code stay in the same partition — preventing any station from appearing in both train and test.
4. Result (approximate for 168 unique stations):
   - Train: ~118 stations → ~145 rows
   - Validation: ~25 stations → ~25 rows
   - Test: ~25 stations → ~24 rows

5. For hyperparameter tuning: Use **5-fold cross-validation on the training set only**, using `GroupKFold` with groups = STN code.

6. **Important:** With only ~145 training rows, complex models (deep neural nets, large ensembles) are inappropriate. The train/test split is used primarily for honest final evaluation; the 5-fold CV result is the primary model comparison metric.

---

## 25. Station-Level Leakage Prevention Strategy

| Risk | Mechanism | Prevention |
|---|---|---|
| Station identity in train + test | 26 stations appear in 2 years | `GroupShuffleSplit(groups=stn_code)` — ensures all records for a station go to one partition |
| Imputation leakage | Imputing with global median before split | All imputation statistics computed on training set only, applied to all sets |
| Scaling leakage | StandardScaler fitted on full data | Scaler fitted on training set only |
| Target encoding leakage | If state/water-body-type encoded with mean WQI | Use one-hot encoding only |
| STN code / Location as feature | Identifier columns memorised by model | Explicitly excluded from all feature sets |

---

## 26. Candidate ML Algorithms

Given 194 observations (after preprocessing, ~155–180 rows with valid WQI), the following algorithms are appropriate:

| Algorithm | Type | Reason for Inclusion |
|---|---|---|
| **Ridge Regression** | Linear regression with L2 | Baseline; interpretable; stable with small n |
| **Random Forest Regressor** | Tree ensemble | Handles non-linearity; robust to outliers after log-transform; provides feature importance |
| **Gradient Boosting Regressor** (scikit-learn `GradientBoostingRegressor`) | Boosted ensemble | Often outperforms RF on tabular data; suitable for small datasets |
| **Support Vector Regressor (SVR)** | Kernel-based | Effective in small-sample settings; RBF kernel |
| **K-Nearest Neighbours Regressor** | Instance-based | Simple baseline; good for small n |

**Explicitly excluded:**
- Deep neural networks (too many parameters for 194 rows)
- XGBoost / LightGBM (powerful but prone to overfitting at this scale without extensive tuning)
- Any model requiring >5× more parameters than training samples

**For classification target (`WQI_category`):**
- Random Forest Classifier
- Logistic Regression (multinomial)
- Support Vector Classifier (SVC)

---

## 27. Evaluation Metrics

### Regression (WQI_score prediction)

| Metric | Symbol | Why |
|---|---|---|
| Root Mean Squared Error | RMSE | Penalises large errors; same unit as WQI |
| Mean Absolute Error | MAE | Robust to extreme WQI outliers |
| R² Score | R² | Proportion of variance explained |
| Mean Absolute Percentage Error | MAPE | Scale-independent for comparison |

### Classification (WQI_category prediction)

| Metric | Why |
|---|---|
| Accuracy | Baseline; meaningful if classes are balanced |
| Macro-F1 Score | Accounts for imbalanced class distribution |
| Confusion Matrix | Visualises per-class errors |
| Cohen's Kappa | Agreement beyond chance |

Primary metric for model selection: **RMSE** (regression) and **Macro-F1** (classification).

---

## 28. Model Comparison Methodology

1. All models are trained on the same training fold with identical preprocessing pipeline.
2. Hyperparameter tuning via `GridSearchCV` / `RandomizedSearchCV` with `GroupKFold(n_splits=5)` on training data only.
3. Models are compared using 5-fold CV RMSE on the training set (primary ranking).
4. The best model is re-evaluated on the held-out test set (reported once, at the end — no iteration on test set).
5. Results are presented in a comparison table showing train CV score, validation score, and test score for each model.
6. Overfitting check: Flag any model where `(CV RMSE - Test RMSE) / CV RMSE > 0.15` as potentially overfitting.

---

## 29. Explainability Plan

| Method | Applied To | Purpose |
|---|---|---|
| Feature importance (built-in) | Random Forest, Gradient Boosting | Which parameters drive WQI prediction |
| Permutation importance | All models | Model-agnostic cross-check |
| Partial Dependence Plots (PDP) | Best model | How WQI changes as each feature varies |
| SHAP values (optional) | Best model | If SHAP library is available; individual prediction explanations |
| Residual analysis | All models | Which station types / states are poorly predicted |

All explainability output will be included as charts in the notebook and referenced in the report.

---

## 30. Project Folder and File Architecture

```
C:\Indian_Water_Quality_AI\
│
├── data/
│   ├── Indian_water_data.csv          ← RAW DATA (READ-ONLY, NEVER MODIFIED)
│   └── processed/
│       ├── water_quality_processed.csv    ← Cleaned + engineered dataset
│       ├── wqi_scores.csv                 ← WQI scores + categories
│       └── preprocessing_audit_log.csv    ← Log of every transformation
│
├── notebooks/
│   └── YourName_IndianWaterQuality.ipynb  ← Primary submission notebook
│
├── backend/
│   ├── __init__.py
│   ├── preprocess.py                  ← Preprocessing functions
│   ├── wqi_calculator.py              ← WQI computation functions
│   ├── train.py                       ← Model training functions
│   ├── evaluate.py                    ← Evaluation functions
│   └── predict.py                     ← Prediction API functions
│
├── frontend/
│   ├── app.py                         ← Streamlit dashboard app
│   ├── components/
│   │   ├── overview.py
│   │   ├── analysis.py
│   │   └── predictor.py
│   └── assets/
│       └── style.css
│
├── model/
│   ├── best_model.pkl                 ← Saved best ML model (joblib)
│   ├── scaler.pkl                     ← Saved feature scaler
│   └── model_metadata.json            ← Model version, metrics, features used
│
├── report_images/                     ← All chart PNGs saved here
│
├── tests/
│   ├── test_preprocess.py
│   ├── test_wqi_calculator.py
│   └── test_predict.py
│
├── DATASET_AUDIT.md                   ← Stage 1 output (complete)
├── PROJECT_PLAN.md                    ← This document (Stage 2 output)
├── README.md                          ← Project README (updated at end)
├── requirements.txt                   ← Python dependencies
└── YourName_ProjectReport.docx        ← Final internship report
```

---

## 31. Notebook Structure

The primary Jupyter notebook (`YourName_IndianWaterQuality.ipynb`) will be organised into clearly labelled sections using Markdown headers:

```
Section 0:  Project Overview and Setup
Section 1:  Data Loading and Initial Inspection
Section 2:  Data Quality Audit Summary (references DATASET_AUDIT.md)
Section 3:  Data Preprocessing
  3.1  Column renaming and encoding fixes
  3.2  BDL value handling
  3.3  Dash value handling
  3.4  Min > Max anomaly flagging
  3.5  Missing value imputation (post-split)
  3.6  Derived mean features
Section 4:  WQI Computation
  4.1  Standard values and ideal values
  4.2  Sub-index (Q_i) computation
  4.3  Unit weights (W_i) computation
  4.4  WQI score computation
  4.5  WQI category classification
  4.6  WQI applicability flags
Section 5:  Exploratory Data Analysis
  5.1  Univariate distributions
  5.2  WQI distribution
  5.3  Parameter correlations
  5.4  State and water-body-type analysis
  5.5  Temporal analysis
  5.6  Pollution hotspots
Section 6:  Feature Engineering and Train/Test Split
  6.1  Log transforms
  6.2  Categorical encoding
  6.3  Station-stratified group split
  6.4  Imputation on training set
Section 7:  Machine Learning Models
  7.1  Baseline model (Ridge Regression)
  7.2  Random Forest Regressor
  7.3  Gradient Boosting Regressor
  7.4  SVR
  7.5  KNN Regressor
  7.6  Model comparison table
  7.7  Best model selection
Section 8:  Model Evaluation and Explainability
  8.1  Test set evaluation
  8.2  Feature importance
  8.3  Partial dependence plots
  8.4  Residual analysis
Section 9:  WQI Classification Model (Secondary)
Section 10: Conclusions and Insights
Section 11: Model Export
```

---

## 32. Backend Plan

The `backend/` module provides reusable Python functions that:

1. **`preprocess.py`**:
   - `load_raw_data(path)` → DataFrame
   - `rename_columns(df)` → DataFrame with clean column names
   - `handle_bdl(df, bdl_substitutions)` → DataFrame
   - `handle_dash(df)` → DataFrame
   - `flag_minmax_anomalies(df)` → DataFrame
   - `impute_missing(df, strategy='median_by_group', groups=['Type_Water_Body'])` → DataFrame

2. **`wqi_calculator.py`**:
   - `compute_annual_means(df)` → DataFrame
   - `compute_unit_weights(standards, K)` → dict
   - `compute_sub_index(df, standards, ideals)` → DataFrame
   - `compute_wqi(df, weights)` → Series
   - `classify_wqi(wqi_series)` → Series

3. **`train.py`**:
   - `get_feature_matrix(df, feature_cols)` → X
   - `get_target(df)` → y
   - `train_model(model, X_train, y_train)` → fitted model
   - `save_model(model, path)` → None

4. **`evaluate.py`**:
   - `evaluate_regression(y_true, y_pred)` → dict of metrics
   - `plot_actual_vs_predicted(y_true, y_pred, save_path)` → None

5. **`predict.py`**:
   - `predict_wqi(input_dict, model, scaler, feature_cols)` → float

All functions use clear docstrings, type hints, and no hard-coded absolute paths.

---

## 33. Frontend / Dashboard Plan

**Framework:** Streamlit (Python-native, no JavaScript required)

**Dashboard pages:**

| Page | Content |
|---|---|
| **Overview** | Dataset summary stats, map/chart of state coverage, WQI distribution |
| **Analysis** | Interactive parameter comparison charts; filter by state/year/water-body-type |
| **Pollution Hotspots** | Top 10 most/least polluted stations table and bar chart |
| **WQI Predictor** | Input form for DO, pH, BOD, Temperature, State, Water Body Type → outputs predicted WQI and category |

**Dashboard constraints:**
- Uses only the processed dataset and saved model — never reads or modifies raw CSV
- Input validation on the predictor form (e.g., pH must be 0–14)
- Clear disclaimers: "Predicted WQI is an estimate based on partial measurements"

---

## 34. Testing Plan

Unit tests will be written in `tests/` using `pytest`:

| Test File | Tests |
|---|---|
| `test_preprocess.py` | Test BDL substitution; test dash → NaN; test Min > Max flag; test imputation does not alter raw data |
| `test_wqi_calculator.py` | Test WQI formula with known inputs → verify expected output; test Q_i bounds; test WQI classification thresholds |
| `test_predict.py` | Test predictor with valid inputs; test predictor rejects out-of-range inputs |

The raw CSV (`data/Indian_water_data.csv`) is hashed before and after every test run to confirm it has not been modified.

---

## 35. Documentation and Report Plan

**YourName_ProjectReport.docx** will include:

| Section | Content |
|---|---|
| 1. Executive Summary | Project overview, key findings, impact |
| 2. Introduction | Problem statement, motivation |
| 3. Dataset Description | Source, structure, quality issues |
| 4. Methodology | WQI formula, ML approach, leakage prevention |
| 5. Preprocessing | All transformations with before/after examples |
| 6. EDA Results | Key charts and findings with captions |
| 7. WQI Analysis | Distribution, state rankings, hotspots |
| 8. ML Model Results | Comparison table, best model, evaluation metrics |
| 9. Model Explainability | Feature importance, PDP, SHAP (if available) |
| 10. Conclusions | Answers to analytical questions, limitations, future work |
| Appendix A | Full column mapping table |
| Appendix B | BDL substitution values used |
| Appendix C | WQI standard values and formula derivation |
| References | All cited sources |

---

## 36. GitHub Submission Structure

```
Indian_Water_Quality_AI/
├── data/Indian_water_data.csv            ← Raw data (commit as-is)
├── data/processed/                       ← Processed outputs
├── notebooks/YourName_IndianWaterQuality.ipynb
├── backend/                              ← Python source modules
├── frontend/app.py                       ← Streamlit dashboard
├── model/best_model.pkl
├── model/model_metadata.json
├── report_images/                        ← All saved charts
├── tests/                                ← Unit tests
├── requirements.txt
├── README.md
├── DATASET_AUDIT.md
├── PROJECT_PLAN.md
└── YourName_ProjectReport.docx
```

**`.gitignore`** should exclude: `__pycache__/`, `*.pyc`, `.env`, any virtual-environment folder.

---

## 37. Final Deliverables Checklist

**AICTE | IBM SkillsBuild Required Deliverables:**

- [ ] `notebooks/YourName_IndianWaterQuality.ipynb` — Primary notebook with all code and output cells run
- [ ] `requirements.txt` — All Python dependencies with pinned versions
- [ ] `YourName_ProjectReport.docx` — Full written report per Section 35
- [ ] `README.md` — Updated with project description, setup instructions, and how to run

**Project-Specific Deliverables:**

- [ ] `data/processed/water_quality_processed.csv` — Cleaned dataset
- [ ] `data/processed/wqi_scores.csv` — WQI scores and categories
- [ ] `data/processed/preprocessing_audit_log.csv` — Transformation log
- [ ] `backend/*.py` — Modular preprocessing, WQI, train, evaluate, predict functions
- [ ] `frontend/app.py` — Streamlit dashboard
- [ ] `model/best_model.pkl` — Saved best model
- [ ] `model/model_metadata.json` — Model info
- [ ] `report_images/*.png` — All visualisations (V01–V14 mandatory)
- [ ] `tests/` — Unit tests passing
- [ ] `DATASET_AUDIT.md` — Complete ✅
- [ ] `PROJECT_PLAN.md` — Complete ✅

**Data Integrity Checks:**
- [ ] `data/Indian_water_data.csv` MD5 hash matches original (verified before and after all processing)
- [ ] No synthetic rows added to any dataset
- [ ] Preprocessing audit log accounts for every transformation

---

## Decisions Summary

| Decision | Choice | Reason |
|---|---|---|
| WQI methodology | **⚠ MODIFIED index** — Brown (1970) formula structure + project-specific parametrisation | Not identical to any single published index; see Section 9 |
| `Dissolved` column interpretation | **⛔ UNVERIFIED assumption** — treated as DO (mg/L) | Value-range evidence only; CPCB source doc not consulted |
| `Fecal - Min/Max` (cols 21–22) | Excluded entirely | Truncated name unverifiable + 32–53% missing |
| BDL substitution | **⛔ UNVERIFIED MDL values** — proposed MDL/2 per parameter | Actual CPCB lab detection limits unavailable; approximation disclosed |
| Marine/Beach/Sea WQI | Excluded (flagged `WQI_applicable = False`); saline CREEK also excluded | Conductivity standard inapplicable to saline water |
| pH sub-index | Absolute deviation from ideal (7.0) | Project adaptation; no single canonical source |
| DO sub-index | Inverted (beneficial parameter) | Higher DO = better quality |
| ML feature set (primary) | Awaiting scope decision (Option A/B/C — see Appendix A.8) | Not yet finalised |
| Evaluation strategy | 5-fold GroupKFold CV replaces 3-way split | 25-row test set too small; see Appendix A.8 |
| Skewed column treatment | log1p transform for FC, TC, Conductivity, BOD | Stabilises variance; retains all values including outliers |
| Min > Max anomalies | Flagged, not corrected | Cannot confirm correction without source document |

---

## Final Implementation Scope (Smallest Defensible — Pending Your Approval)

This scope satisfies all internship deliverable requirements (notebook, requirements.txt, report, README) while keeping the implementation honest and proportionate to 194 rows.

### What is included

| Component | Detail |
|---|---|
| **Preprocessing** | Load raw CSV (read-only). Rename columns (with UNVERIFIED labels). Handle BDL (flag + approximate MDL/2 substitution, disclosed). Handle dash → NaN. Flag Min>Max anomalies. Impute remaining missing values using group-median (per Type_Water_Body). Exclude saline rows from WQI. |
| **Target engineering** | Compute `(Min+Max)/2` for each of the 7 WQI parameters on ~160 freshwater rows. Compute modified Weighted Arithmetic WQI score. Classify into 5 WQI categories. Label every output with "range-midpoint approximation" disclaimer. |
| **EDA** | 10 mandatory charts (V01–V11 from Section 23): WQI distribution, WQI by state, WQI by water-body type, parameter correlations, DO vs BOD scatter, FC vs TC scatter, missing-value heatmap, top-10 polluted/clean stations, temporal trend for 26 multi-year stations. |
| **ML model** | **2 models only:** Ridge Regression (baseline) + Random Forest Regressor (primary). Feature set: **Option A** (Temp_mean, DO_assumed_mean, pH_mean, BOD_mean + State + WB_Type + Year) with partial-leakage disclosure. Evaluation: **5-fold GroupKFold CV** (groups = STN code) on ~160 freshwater rows. Reported metrics: mean RMSE ± std, mean R² ± std across 5 folds. No separate held-out test set (too small to be reliable). Final model trained on all ~160 rows and saved. |
| **Evaluation** | CV metric table + feature importance bar chart (Random Forest) + actual-vs-predicted scatter. Full leakage disclosure in notebook and report. |
| **Deliverables** | `YourName_IndianWaterQuality.ipynb` · `requirements.txt` · `YourName_ProjectReport.docx` · `README.md` · `data/processed/` (processed CSV + WQI scores + audit log) · `model/best_model.pkl` |

### What is deferred (not in minimal scope)

- Streamlit dashboard (`frontend/`) — deferred
- SVR, KNN, Gradient Boosting models — deferred (not needed for 194 rows)
- Separate held-out test set — deferred (statistically unreliable at ~25–30 rows)
- Choropleth map (V15) — optional stretch goal only

### Row counts at each stage

| Stage | Rows |
|---|---|
| Raw dataset | 194 |
| After excluding saline/WQI-inapplicable rows | ~160 freshwater rows |
| After BDL substitution + group-median imputation | ~155–160 rows with complete WQI |
| Used for ML (5-fold GroupKFold CV) | ~155–160 rows |

---

*This plan contains no invented data, no fabricated citations, no assumed model accuracy, and no synthetic observations. All verified decisions are traceable to DATASET_AUDIT.md and published sources. All unverified assumptions are explicitly labelled ⛔ UNVERIFIED throughout.*

*Next step after approval: Stage 3 — Preprocessing and WQI Computation, pending resolution of the items in Appendix A.*

---

## Appendix A — Scientific Validity Audit (Added Post-Plan Review)

> **Purpose:** This appendix documents every unverified assumption, methodological risk, and required decision identified during the scientific audit of this plan. It must be reviewed and each item either confirmed or resolved before Stage 3 implementation begins.

---

### A.1 — Column Name Verification: `Dissolved - Min/Max`

**Status: UNVERIFIED**

**Evidence supporting DO (mg/L):**
- Observed value range: 0.3–13.6, fully within the physical range of dissolved oxygen (0 mg/L anoxic to ~14.6 mg/L at 0°C fully saturated)
- Values of 0.3 mg/L coincide exclusively with highly polluted stations (Delhi Agra Canal BOD=32–46, Assam lakes BOD=10–26, drains, STPs) — scientifically consistent with severe hypoxia
- Values >12 mg/L occur at cold mountain rivers (Madhya Pradesh, Temp_Min as low as 5°C) — consistent with cold-water DO supersaturation
- CPCB National Water Quality Monitoring Programme standard parameter set is: DO, BOD, FC, TC, pH, Conductivity, Temperature, Nitrate-N — our dataset exactly matches this set, with `Dissolved` filling the DO slot
- No other common "dissolved" water quality parameter has a range of 0.3–13.6 mg/L (TDS: 50–1000+ mg/L; Dissolved CO₂: different range; Dissolved Inorganic Carbon: different range)

**What cannot be confirmed without source documentation:**
- The CPCB data dictionary or dataset README confirming the full column name
- Whether the unit is mg/L or another unit

**Required before implementation:** Treat as DO (mg/L) with an explicit documented assumption. The report must state: *"Column `Dissolved - Min/Max` is interpreted as Dissolved Oxygen (mg/L) based on value-range consistency with CPCB NWMP monitoring parameters. The original column name in the source file is preserved. This interpretation has not been confirmed against the CPCB data dictionary."*

**Impact if assumption is wrong:** All WQI computations using DO are invalid. This is the highest-risk unverified assumption in the project.

---

### A.2 — WQI Methodology: Is This an Established or Custom Method?

**Status: ESTABLISHED with local adaptations — partially verified**

**What is established:**
- Brown et al. (1970) introduced the weighted arithmetic WQI concept: `WQI = Σ(Qi × Wi) / Σ(Wi)`
- The formula structure (`Wi = K/Si`, `Qi = (Ci - V_ideal) / (Si - V_ideal) × 100`) appears in multiple Indian peer-reviewed papers citing Brown (1970) and Tyagi et al. (2013)

**What is a local/project adaptation (not from a single canonical source):**
- The specific choice of 7 parameters for this dataset
- The specific `Si` (standard) values for each parameter
- The pH absolute-deviation sub-index formula
- The DO inversion formula
- The `(Min + Max) / 2` annual representative value
- The classification thresholds

**What must be verified from Tyagi et al. (2013) before citing it:**
- Does the paper use `Wi = K/Si` where `K = 1/Σ(1/Si)`?
- Does the paper use the same `Si` values for DO, BOD, pH, Conductivity, Nitrate, FC, TC?
- Does the paper use the same classification thresholds (0–25 Excellent, 26–50 Good, 51–75 Poor, 76–100 Very Poor, >100 Unsuitable)?

**Required:** Read Tyagi et al. (2013) (DOI: 10.12691/ajwr-1-3-3) and confirm the formula, parameters, standard values, and classification thresholds match what is described in this plan. If they differ, adjust the plan to match the cited paper exactly, OR cite a different paper, OR explicitly document the deviation.

---

### A.3 — WQI Parameters Available vs. Required

**All 7 required parameters for the Weighted Arithmetic WQI (Indian form) are present in this dataset**, subject to the `Dissolved = DO` assumption (UV-01):

| Parameter | Dataset Column | Available | Issues |
|---|---|---|---|
| DO (mg/L) | `Dissolved - Min/Max` | ✅ Yes (UNVERIFIED name) | 1 BDL, 1 missing |
| pH | `pH - Min/Max` | ✅ Yes | 0 missing — complete |
| BOD (mg/L) | `BOD - Min/Max` | ✅ Yes | 11 BDL, ~7% missing |
| Conductivity (µmho/cm) | `Conductivity - Min/Max` | ✅ Yes | 1 BDL, ~7% missing |
| Nitrate-N (mg/L) | `NitrateN - Min/Max` | ✅ Yes | 2 BDL, ~7% missing |
| Fecal Coliform (MPN/100ml) | `Fecal Coliform - Min/Max` | ✅ Yes | 4 BDL, ~7% missing, 10 Min>Max |
| Total Coliform (MPN/100ml) | `Total Coliform - Min/Max` | ✅ Yes | 1 dash, ~7% missing |

**Parameters required by NSF-WQI but NOT available:** Turbidity (NTU), Total Phosphate (mg/L), Total Solids (mg/L) → NSF-WQI cannot be computed. This exclusion is correct.

**CREEK row note (not in original plan):** STN 2267 (Goa, CREEK) has Conductivity_Max = 51,530 µmho/cm — clearly tidal/saline. The plan currently excludes MARINE, SEA, BEACH from WQI but does NOT explicitly exclude CREEK. This row should also receive `WQI_applicable = False`. **Action required: Add CREEK to the exclusion list when Conductivity indicates saline conditions (e.g., > 5,000 µmho/cm).**

---

### A.4 — Appropriateness of Annual Min/Max Data for WQI

**Status: ACCEPTABLE with mandatory disclosure**

The Weighted Arithmetic WQI was designed for individual measurements or representative concentrations, not explicitly for annual Min/Max ranges.

**Critical finding from audit:**
- `(Min + Max) / 2` is the midpoint of the annual range, NOT the arithmetic mean of all samples
- A single extreme sampling event determines the Min or Max value
- The resulting WQI is a **range-midpoint approximation**, not a true annual mean WQI
- This is used in Indian WQI literature for CPCB annual summary data, but must be explicitly labelled

**Required wording in every output:** *"WQI values in this project are computed using the arithmetic midpoint of the reported annual parameter range [(Min + Max) / 2] as the representative annual concentration. This is an approximation; the true annual mean WQI would require individual sample measurements. WQI scores should be interpreted as indicative of annual water quality conditions, not as exact computed indices."*

**Rows that will have valid WQI:**
- Total rows: 194
- Saline/excluded rows: 34 (MARINE: 10, BEACH: 19, SEA: 4, CREEK: 1 — pending conductivity check)
- Freshwater rows: 160
- Freshwater rows with all parameters after BDL substitution: ~131 of 160 (~82%)
- Freshwater rows with remaining gaps (dash or empty): ~29 — these require group-median imputation or exclusion

---

### A.5 — BDL Substitution: What Is Required

**Status: UNVERIFIED (substitution values are approximations)**

The plan proposes using published typical MDL / 2 per parameter. The actual lab detection limits for CPCB monitoring stations are not in the dataset.

**Column-by-column BDL impact and required information:**

| Column | BDL Count | Proposed Substitution | Required for Exact Value | Impact on WQI |
|---|---|---|---|---|
| DO (Dissolved) Min | 1 | 0.05 mg/L (= 0.1/2) | CPCB lab DO meter MDL | Very low — 1 row only |
| Conductivity Min | 1 | 0.5 µmho/cm (= 1.0/2) | CPCB lab conductivity MDL | Very low — 1 row only |
| BOD Min | 11 | 0.25 mg/L (= 0.5/2) | CPCB lab BOD test MDL | Low — 11 rows; BOD BDL means very clean water; substituting ~0.25 is conservative |
| Nitrate-N Min | 2 | 0.05 mg/L (= 0.1/2) | CPCB lab nitrate MDL | Very low — 2 rows only |
| Fecal Coliform Min | 3 | 1.0 MPN/100ml (MPN series lower bound = 2; use 1) | CPCB lab FC method MDL | Low — 3 rows |
| Fecal Coliform Max | 1 | 1.0 MPN/100ml | Same | Very low |

**Required disclosure:** *"BDL values (n = 18 across 6 columns, excluding excluded Fecal-Min/Max) are substituted with MDL/2 using published typical instrument detection limits from standard laboratory practice. Actual detection limits for CPCB monitoring laboratories are not available from the dataset. This substitution introduces a minor approximation affecting a maximum of 18 out of 194 rows."*

---

### A.6 — Marine/Beach/Sea Exclusion Justification

**Status: SCIENTIFICALLY JUSTIFIED — confirmed by data**

The exclusion of MARINE, SEA, and BEACH water body types from WQI computation is fully justified:

1. **BIS IS:10500-2012** is a drinking water standard; it has no applicability to marine water
2. **CPCB Designated Best Use (IS:2296-1982)** applies to fresh inland surface water; marine water quality is governed by different standards (Coastal Regulation Zone, MoEF)
3. **Conductivity proof:** Marine/Beach/Sea rows show conductivity of 13,800–61,900 µmho/cm. At S_i = 300 µmho/cm, Q_conductivity = (50,000/300) × 100 ≈ 16,667 — an absurd result that would render the WQI meaningless
4. **Additional row to exclude (identified in audit):** STN 2267 (Goa, CREEK, Conductivity_Max = 51,530 µmho/cm) is clearly a saline tidal creek. **The plan must be updated to flag this row as `WQI_applicable = False`.**

**Updated exclusion rule:** `WQI_applicable = False` when:
- `Type Water Body` ∈ {MARINE, SEA, BEACH}, OR
- `Type Water Body` = CREEK AND `Conductivity_mean` > 5,000 µmho/cm

This rule excludes exactly 34 rows (33 MARINE/SEA/BEACH + 1 saline CREEK).

---

### A.7 — Min > Max Anomalies: What Verification Is Required

**Status: FLAGGED, NOT CORRECTED — correct approach**

The plan's approach (flag, do not correct) is correct. Detailed findings:

**Conductivity Min > Max (5 rows, all 2023, Andhra Pradesh × 4 + Gujarat × 1):**
All 5 are CANAL water bodies. The anomaly values are in the range 4–275 µmho/cm — within realistic freshwater conductivity. Most likely cause: Min and Max columns were transposed during data entry. Correction would require the original CPCB 2023 monitoring report for each STN code.

**Fecal Coliform Min > Max (10 rows — 2 Assam 2023, 6 Himachal Pradesh 2021, 2 Punjab 2021):**
The 2021 Himachal Pradesh anomalies are particularly severe (Min 1,600–20,000 >> Max 49–490). These may represent a systemic data entry issue in 2021 HP/Punjab reporting. Correction requires original reports.

**Critical finding for WQI:** The plan correctly states that `(Min + Max) / 2` is unaffected by a Min/Max swap — the mean is identical regardless of which value is labelled Min or Max. **Therefore, Min>Max anomalies do NOT affect WQI calculation using the midpoint, only affect any analysis using Min or Max values individually.**

---

### A.8 — ML Leakage and Split Validity

**Status: PARTIAL LEAKAGE — disclosed; SPLIT — needs revision**

#### Leakage finding (confirmed):

The proposed primary feature set (DO_mean, pH_mean, BOD_mean + Temp + WB_Type + State) includes 3 of the 7 WQI formula components. The WQI formula assigns its largest unit weights to parameters with the smallest Si values:

| Parameter | Si | Relative weight (K/Si) |
|---|---|---|
| pH deviation | 1.5 | Largest |
| DO | 6.0 | Large |
| BOD | 3.0 | Large |
| Nitrate-N | 10.2 | Medium |
| Conductivity | 300 | Small |
| Fecal Coliform | 500 | Very small |
| Total Coliform | 5000 | Smallest |

**Implication:** DO, pH, and BOD together contribute the dominant share of WQI. A model with these 3 features as inputs will learn a near-linear relationship to WQI and will achieve high R² — not because of generalisation, but because the target is largely determined by its 3 largest-weight inputs. This should be clearly disclosed.

**Decision required by you:** Which ML framing do you prefer?
- **Option A (Current plan):** 3/7 WQI components + non-WQI features. High R² expected; partial leakage disclosed. Scientifically defensible with honest labelling.
- **Option B (Leakage-free):** Non-WQI features only (Temp, WB_Type, State, Year). Lower R² expected; genuinely predictive. More honest but less impressive.
- **Option C (Explicit formula learning):** All 7 WQI components as features. R² ≈ 1.0; explicitly labelled as "formula reproduction" for educational demonstration. Not a real ML model.

#### Split validity finding (revision recommended):

A 70/15/15 GroupShuffleSplit yields approximately:
- Train: ~117 stations, ~135 rows
- Validation: ~25 stations, ~25 rows
- Test: ~25 stations, ~25 rows

**A test set of 25 rows is too small for reliable model evaluation.** The 95% confidence interval on R² from 25 test points is very wide (±0.15 to ±0.25). Model selection using a 25-row validation set is similarly unreliable.

**Recommended revision:** Replace the 3-way split with:
- **Primary evaluation:** 5-fold `GroupKFold` cross-validation on all ~160 freshwater rows (groups = STN code)
- **Final model:** Trained on all 160 freshwater rows
- **Reported metrics:** Mean ± std of RMSE and R² across 5 folds
- **Optional holdout:** If a held-out test set is required, use a single 80/20 GroupShuffleSplit, clearly stating the test set contains only ~32 rows and results should be interpreted cautiously

---

### A.9 — Complete UNVERIFIED Assumptions Register

The following items must be resolved before Stage 3. Items marked **BLOCKING** must be resolved before any code is written.

| ID | Assumption | BLOCKING? | Resolution |
|---|---|---|---|
| UV-01 | `Dissolved` columns = Dissolved Oxygen (DO) in mg/L | **YES** | Treat as DO with documented assumption. Cannot confirm without source document. |
| UV-02 | `Fecal - Min/Max` excluded due to unknown identity | No | Exclusion is conservative; safe to proceed |
| UV-03 | Standard values (Si) from BIS IS:10500-2012 / CPCB DBU | **YES** | Must confirm exact Si values against cited sources before WQI computation |
| UV-04 | DO ideal value = 14.6 mg/L vs. 8.26 mg/L (25°C saturation) | **YES** | Your decision: use 14.6 (absolute max) or 8.26 (saturation at 25°C, more common in Indian studies). Both are defensible; must be stated. |
| UV-05 | pH sub-index: `|C_pH − 7.0| / 1.5 × 100` | **YES** | Must cite a specific paper using this exact formula. Alternatives exist. |
| UV-06 | BDL → MDL/2 using published typical MDLs | No | Disclose as approximation in report |
| UV-07 | WQI classification thresholds from Tyagi et al. 2013 | **YES** | Must verify exact threshold values from the paper before coding the classifier |
| UV-08 | Annual mean = (Min + Max) / 2 | **YES** | Accept as approximation; must add disclosure language to every output |
| UV-09 | Tyagi et al. 2013 uses the same formula form as described | **YES** | Must read the paper and confirm formula before citing it |
| UV-10 | FC standard = 500 MPN/100ml | **YES** | Your decision: use CPCB Class B (500) or BIS IS:10500 drinking water (absent/0)? Both are cited in literature. |
| UV-11 | TC standard = 5000 MPN/100ml | **YES** | Your decision: use CPCB Class C (5000) or BIS drinking water (10 MPN/100ml)? |
| UV-12 | Conductivity standard = 300 µmho/cm | No | BIS IS:10500 acceptable limit is 300; permissible is 600. Using 300 is conservative; acceptable either way |
| UV-13 | CREEK STN 2267 (Goa, Cond=51,530) excluded from WQI | **YES** | Add CREEK with high conductivity to exclusion rule |
| UV-14 | ML feature set and split strategy | **YES** | Choose Option A/B/C (Section A.8); confirm GroupKFold-only evaluation |

---

### A.10 — Minimum Scientifically Defensible Scope

Two implementation tiers are defined. **Your approval of a specific tier is required before Stage 3 begins.**

#### Tier 1 — Analytics Only (Minimum viable; no ML)
- Preprocessing + WQI computation for ~131 freshwater rows
- Full EDA with all planned visualisations (V01–V14)
- No ML model
- **Scientific integrity:** Maximum — no leakage, no small-sample ML concerns
- **Deliverables:** Notebook, processed data, report, README, requirements.txt
- **Appropriate when:** The internship allows analytics-only projects

#### Tier 2 — Analytics + Constrained ML (Recommended for internship)
- All of Tier 1
- ML evaluation using 5-fold `GroupKFold` CV on ~160 freshwater rows
- 2 models only: **Ridge Regression** (baseline) + **Random Forest** (primary)
- Feature set: Option A (3/7 WQI components + non-WQI features) OR Option B (non-WQI only) — **your choice**
- Honest disclosure of partial leakage (Option A) or low predictive power (Option B)
- No Streamlit dashboard (defer to post-internship)
- **Scientific integrity:** High, with documented limitations
- **Deliverables:** All internship required files + backend module + saved model

#### Tier 3 — Full Plan as Written (Higher complexity risk)
- 5 models, 3-way split, Streamlit dashboard
- **Risk:** 25-row test set is statistically unreliable; results may be uninterpretable
- **Risk:** Complexity may exceed the time budget for a rigorous internship project
- **Not recommended** without a larger dataset or deliberate acceptance of the limitations documented here

---

*Appendix A added: Scientific Validity Audit — all items must be reviewed by the project owner before Stage 3.*
