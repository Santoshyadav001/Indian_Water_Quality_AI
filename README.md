# Indian Water Quality Analytics and WQI Prediction using Machine Learning

**AICTE | IBM SkillsBuild Data Analytics with AI Internship 2026**

## Student

**Santosh Kumar Yadav**

---

## Project Overview

This project performs exploratory data analysis on Indian water quality monitoring data collected by the Central Pollution Control Board (CPCB) through the National Water Quality Monitoring Programme (NWMP). A Modified Weighted Arithmetic Water Quality Index (WQI) is computed for approximately 160 freshwater monitoring stations, and two machine learning models are trained to predict WQI scores from a partial set of measured parameters.

---

## Problem Statement

Surface water quality in India varies significantly by geography, water body type, and season. Annual monitoring data from 194 stations across 17 states (years 2021–2023) is available in aggregated Min/Max form rather than as individual measurements. This project asks: given temperature, dissolved oxygen, pH, BOD, water body type, state, and year, can a model estimate the broader WQI score that incorporates all seven monitoring parameters?

---

## Objectives

1. Audit and document the data quality issues in the raw CPCB monitoring dataset.
2. Preprocess the dataset: handle BDL values, missing values, and anomalous Min/Max pairs.
3. Compute a Modified Weighted Arithmetic WQI for all applicable freshwater stations.
4. Conduct exploratory data analysis (EDA) across 14 visualisations (V01–V14).
5. Train Ridge Regression and Random Forest Regressor models to predict WQI scores.
6. Evaluate models using 5-fold GroupKFold cross-validation grouped by station.
7. Produce a complete, honest internship submission package.

---

## Dataset

| Property | Value |
|---|---|
| Source | CPCB National Water Quality Monitoring Programme (NWMP) |
| File | `data/Indian_water_data.csv` |
| Rows | 194 station-year observations |
| Columns | 23 (station identifiers + 9 parameter Min/Max pairs) |
| Years | 2021, 2022, 2023 |
| States | 17 |
| Water body types | 11 (RIVER, LAKE, CANAL, DRAIN, POND, STP, BEACH, MARINE, SEA, CREEK, WATER TREATMENT PLANT) |
| Rows used for WQI/ML | 160 (freshwater only; 34 saline rows excluded) |

**The raw CSV (`data/Indian_water_data.csv`) is never modified.** All outputs are written to `data/processed/`.

---

## Dataset Quality and Limitations

- **BDL values:** 18 BDL (Below Detection Limit) entries across 6 measurement columns. Replaced with proxy MDL/2 values — these substitution values are **UNVERIFIED** (not confirmed from CPCB lab documentation).
- **Dash values:** Some cells contain `-` (meaning ambiguous). Treated as missing (NaN).
- **Min > Max anomalies:** 15 rows have Min > Max for at least one parameter. Values are **flagged but not corrected** (correction requires source verification).
- **Missing values:** Approximately 7% of measurement values are missing. Imputed using group-median per `Water_Body_Type`.
- **Saline exclusion:** 34 rows (MARINE, SEA, BEACH, and one saline CREEK) are excluded from WQI computation.
- **Column name ambiguity:** The column `Dissolved - Min/Max` is interpreted as Dissolved Oxygen (mg/L) based on value-range consistency with CPCB NWMP parameters. This interpretation is **UNVERIFIED** — it has not been confirmed against the CPCB data dictionary.

See `DATASET_AUDIT.md` for the full audit.

---

## Project Structure

```
Indian_Water_Quality_AI/
│
├── data/
│   ├── Indian_water_data.csv                   ← Raw data (READ-ONLY)
│   └── processed/
│       ├── water_quality_processed.csv         ← Cleaned dataset
│       ├── wqi_scores.csv                      ← WQI scores and categories
│       └── preprocessing_audit_log.csv         ← Transformation log
│
├── backend/
│   ├── preprocess.py                           ← Preprocessing functions
│   └── wqi_calculator.py                       ← WQI computation functions
│
├── model/
│   ├── best_model.pkl                          ← Random Forest (all 160 rows)
│   ├── ridge_model.pkl                         ← Ridge Regression (all 160 rows)
│   └── model_metadata.json                     ← CV metrics and disclosures
│
├── report_images/                              ← V01–V14 chart PNGs
│
├── SANTOSHKUMARYADAV_IndianWaterQualityAnalytics.ipynb
├── SANTOSHKUMARYADAV_IndianWaterQualityAnalytics_ProjectReport.docx
├── requirements.txt
├── README.md
├── DATASET_AUDIT.md
├── PROJECT_PLAN.md
├── stage4_eda_charts.py                        ← EDA chart generation (V01–V11)
├── stage5_ml.py                                ← ML pipeline (V12–V14)
└── run_preprocessing.py                        ← Preprocessing runner
```

---

## Technologies Used

| Library | Version | Purpose |
|---|---|---|
| Python | 3.13 | Core language |
| pandas | >=2.0.0 | Data loading and manipulation |
| numpy | >=1.24.0 | Numerical operations |
| matplotlib | >=3.7.0 | Visualisation |
| seaborn | >=0.12.0 | Statistical visualisation |
| scikit-learn | >=1.2.0 | ML models, pipelines, GroupKFold |
| scipy | >=1.10.0 | Statistical tests in EDA |
| joblib | >=1.2.0 | Model serialisation |
| nbformat | >=5.7.0 | Notebook generation |

---

## Installation

```bash
# Clone or download the project folder
cd Indian_Water_Quality_AI

# Install dependencies
pip install -r requirements.txt
```

---

## How to Run

**Step 1 — Preprocessing and WQI computation** (already completed; outputs exist in `data/processed/`):
```bash
python run_preprocessing.py
```

**Step 2 — EDA charts** (already completed; outputs exist in `report_images/`):
```bash
python stage4_eda_charts.py
```

**Step 3 — Machine Learning** (already completed; outputs exist in `model/` and `report_images/`):
```bash
python stage5_ml.py
```

**Step 4 — View the notebook:**
Open `SANTOSHKUMARYADAV_IndianWaterQualityAnalytics.ipynb` in Jupyter Notebook or JupyterLab.

---

## Data Preprocessing

Implemented in `backend/preprocess.py` and orchestrated by `run_preprocessing.py`.

| Step | Description |
|---|---|
| Column renaming | Positional mapping; `Dissolved` renamed `DO_assumed` with UNVERIFIED label |
| BDL handling | `BDL` replaced with UNVERIFIED proxy MDL/2; flag column added |
| Dash handling | `-` values replaced with NaN; flag column added |
| Min > Max flagging | Anomalous pairs flagged, NOT corrected |
| Numeric parsing | All measurement columns converted to float (None for missing) |
| Group-median imputation | Missing values filled using median per `Water_Body_Type` group |
| WQI applicability flag | Saline water bodies flagged `WQI_applicable=0` |

All transformations are logged to `data/processed/preprocessing_audit_log.csv`.

---

## WQI Methodology

A **Modified Weighted Arithmetic WQI** following the formula structure of Brown et al. (1970) was implemented with adaptations for the available Indian water-quality parameters. It is **not identical to any single published WQI**.

**Formula:**

```
WQI = Σ(Qi × Wi) / Σ(Wi)
Wi  = K / Si    where K = 1 / Σ(1/Si)
```

**Annual representative concentration:**

```
Ci = (Min + Max) / 2    [range-midpoint approximation — NOT a true annual mean]
```

**Seven parameters used:** DO (assumed), pH, BOD, Conductivity, Nitrate-N, Fecal Coliform, Total Coliform.

**WQI Classification (project-specific thresholds):**

| WQI Score | Category |
|---|---|
| 0 – 25 | Excellent |
| 25 – 50 | Good |
| 50 – 75 | Poor |
| 75 – 100 | Very Poor |
| > 100 | Unsuitable for Drinking |

**WQI summary (160 freshwater rows):**
- Mean WQI: 68.0 | Median: 61.2 | Range: 41.1 – 141.6
- Good: 22 rows | Poor: 105 rows | Very Poor: 11 rows | Unsuitable: 22 rows

---

## Exploratory Data Analysis

14 charts are saved to `report_images/`:

| Chart | Description |
|---|---|
| V01 | WQI Score Distribution (histogram + KDE) |
| V02 | WQI Category Counts (bar chart) |
| V03 | WQI Score by State (box plot) |
| V04 | WQI Score by Water Body Type (box plot) |
| V05 | Parameter Correlation Heatmap |
| V06 | Assumed DO vs BOD Scatter |
| V07 | Fecal Coliform vs Total Coliform Scatter |
| V08 | Missing Values Heatmap |
| V09 | Temporal WQI Trend (multi-year stations) |
| V10 | Top 10 Most Polluted Stations |
| V11 | Top 10 Cleanest Stations |
| V12 | Random Forest Feature Importance |
| V13 | Actual vs Predicted WQI (out-of-fold) |
| V14 | Residual Plot (out-of-fold) |

---

## Machine Learning

**Target:** `WQI_score` (160 freshwater rows)

**Features (Option A — Final Implementation Scope):**

| Feature | Type |
|---|---|
| `Temp_mean` | Numeric |
| `DO_assumed_mean` | Numeric |
| `pH_mean` | Numeric |
| `BOD_mean` | Numeric |
| `Year` | Numeric (ordinal) |
| `State_Name` | Categorical (one-hot encoded) |
| `Water_Body_Type` | Categorical (one-hot encoded) |

**Models:**
- Ridge Regression (alpha=1.0) — baseline linear model
- Random Forest Regressor (n_estimators=200, min_samples_leaf=3) — primary model

All preprocessing (median imputation, standard scaling, one-hot encoding) is performed **inside** the sklearn Pipeline, with imputation statistics computed only on each training fold.

---

## Cross-Validation Strategy

**5-fold GroupKFold** with `groups = STN_code`.

All rows for a given station code are assigned to the same fold. This prevents station-level data leakage between training and validation sets.

No separate held-out test set was created: with only 160 rows and 150 unique stations, a ~25-row test set would be too small to produce reliable evaluation estimates.

---

## Results

**5-fold GroupKFold Cross-Validation:**

| Model | Mean RMSE | Std RMSE | Mean R² | Std R² |
|---|---|---|---|---|
| Ridge Regression (alpha=1.0) | 21.55 | ±16.79 | -0.196 | ±1.594 |
| Random Forest (n=200, min_leaf=3) | 4.70 | ±1.59 | 0.951 | ±0.017 |

Under the selected 5-fold GroupKFold evaluation, Random Forest produced lower mean RMSE and higher mean R² than Ridge Regression.

**Per-fold results — Random Forest:**

| Fold | RMSE | R² |
|---|---|---|
| 1 | 3.44 | 0.952 |
| 2 | 3.25 | 0.971 |
| 3 | 4.11 | 0.953 |
| 4 | 5.82 | 0.955 |
| 5 | 6.89 | 0.925 |

**Per-fold results — Ridge Regression:**

| Fold | RMSE | R² |
|---|---|---|
| 1 | 10.46 | 0.558 |
| 2 | 11.67 | 0.630 |
| 3 | 13.56 | 0.487 |
| 4 | 21.48 | 0.387 |
| 5 | 50.58 | -3.043 |

---

## Visualisations

All visualisation files are saved as PNG images in `report_images/`:

- `report_images/V01_wqi_distribution.png`
- `report_images/V02_wqi_category_counts.png`
- `report_images/V03_wqi_by_state.png`
- `report_images/V04_wqi_by_water_body_type.png`
- `report_images/V05_parameter_correlation.png`
- `report_images/V06_do_vs_bod.png`
- `report_images/V07_fc_vs_tc.png`
- `report_images/V08_missing_values.png`
- `report_images/V09_temporal_trend.png`
- `report_images/V10_top_10_polluted_stations.png`
- `report_images/V11_top_10_cleanest_stations.png`
- `report_images/V12_feature_importance.png`
- `report_images/V13_actual_vs_predicted.png`
- `report_images/V14_residuals.png`

---

## Important Scientific Disclosures

1. **Unverified DO interpretation:** The column `Dissolved - Min/Max` in the raw dataset is interpreted as Dissolved Oxygen (mg/L). This interpretation is based on value-range consistency with CPCB NWMP parameters and has **not been confirmed** against the CPCB data dictionary. All derived columns are labelled `DO_assumed` throughout the project.

2. **Modified/Custom WQI:** The WQI computed in this project is a Modified Weighted Arithmetic WQI following the formula structure of Brown et al. (1970). It uses project-specific standard values (BIS IS:10500-2012), parameter sub-index adaptations, and classification thresholds. It is **not identical to any single published water quality index**.

3. **Range-midpoint approximation:** Annual representative parameter values are computed as `(Min + Max) / 2`. This is a **range-midpoint approximation**, not a true arithmetic mean of individual measurements taken during the year.

4. **Unverified BDL substitutions:** BDL (Below Detection Limit) values were replaced with half of published typical instrument MDLs. These substitution values are **UNVERIFIED proxies** — actual CPCB laboratory detection limits were not available.

5. **Partial target reconstruction (not independent prediction):** Three of the ML features — `DO_assumed_mean`, `pH_mean`, and `BOD_mean` — are also components of the WQI target. The ML model can partially reconstruct the WQI formula from these inputs. This is a **partially reconstructive prediction task**, not independent external prediction of water quality. `Conductivity_mean`, `NitrateN_mean`, `FC_mean`, and `TC_mean` are deliberately withheld to avoid full reconstruction.

6. **Upstream imputation limitation:** Stage 3 preprocessing applied group-median imputation across the full 194-row dataset before any fold split. Stage 5 re-applies in-fold imputation to mitigate this, but **cannot fully eliminate residual leakage** for the approximately 15 rows with imputed ML feature values.

7. **Small dataset:** Approximately 160 freshwater rows are used for WQI computation and machine learning after excluding 34 saline rows. Cross-validation results should be interpreted with this small sample size in mind.

8. **Saline water body exclusion:** 34 rows with water body types MARINE, SEA, BEACH, and one saline CREEK (Conductivity > 5,000 µmho/cm) are excluded from the drinking-water-oriented WQI analysis.

---

## Project Files

| File | Description |
|---|---|
| `data/Indian_water_data.csv` | Raw monitoring data (read-only) |
| `data/processed/water_quality_processed.csv` | Cleaned dataset |
| `data/processed/wqi_scores.csv` | WQI scores and categories |
| `data/processed/preprocessing_audit_log.csv` | Full transformation log |
| `backend/preprocess.py` | Preprocessing functions |
| `backend/wqi_calculator.py` | WQI computation functions |
| `model/best_model.pkl` | Saved Random Forest model |
| `model/ridge_model.pkl` | Saved Ridge Regression model |
| `model/model_metadata.json` | CV metrics, features, disclosures |
| `stage4_eda_charts.py` | EDA chart generation script |
| `stage5_ml.py` | ML pipeline script |
| `run_preprocessing.py` | Preprocessing runner |
| `DATASET_AUDIT.md` | Data quality audit report |
| `PROJECT_PLAN.md` | Full project plan and methodology |

---

## Conclusion

This project demonstrates a complete end-to-end data analytics workflow applied to Indian surface water quality data. Key findings:

- The majority (66%) of the 160 analysed freshwater monitoring stations fall into the "Poor" WQI category.
- States such as Uttar Pradesh, Haryana, and Goa showed relatively lower WQI scores (better quality), while Odisha, Tamil Nadu, and Maharashtra showed the highest mean WQI scores.
- Sewage Treatment Plants (STPs) showed markedly higher WQI scores than natural water bodies.
- Under 5-fold GroupKFold evaluation, Random Forest achieved mean RMSE of 4.70 and mean R² of 0.951, compared to Ridge Regression's mean RMSE of 21.55 and mean R² of -0.196.
- However, these results must be interpreted with the partial target reconstruction caveat: BOD, DO, and pH are WQI components, and BOD alone accounts for approximately 96% of the Random Forest's feature importance.

All results are reproducible from the provided source files. The raw dataset has not been modified.

---

## References

- Brown, R.M., McClelland, N.I., Deininger, R.A., & Tozer, R.G. (1970). A water quality index — do we dare? *Water and Sewage Works*, 117, 339–343.
- Bureau of Indian Standards (2012). *IS:10500 — Drinking Water Specification (Second Revision).*
- Central Pollution Control Board (CPCB). National Water Quality Monitoring Programme (NWMP).
- Tyagi, S., Sharma, B., Singh, P., & Dobhal, R. (2013). Water quality assessment in terms of water quality index. *American Journal of Water Resources*, 1(3), 34–38. DOI: 10.12691/ajwr-1-3-3.

---

*This project was completed as part of the AICTE | IBM SkillsBuild Data Analytics with AI Internship 2026.*
