"""
Stage 5: Machine Learning — WQI Score Prediction
=================================================
Models     : Ridge Regression (baseline) + Random Forest Regressor (primary)
Target     : WQI_score (WQI_applicable == 1 rows only, no nulls in WQI_score)
Features   : Temp_mean, DO_assumed_mean, pH_mean, BOD_mean, State_Name,
             Water_Body_Type, Year  (Option A — Final Implementation Scope)
Validation : 5-fold GroupKFold, groups = STN_code
Charts     : V12 Feature Importance, V13 Actual vs Predicted, V14 Residual Plot

DISCLOSURES (must not be removed):
  - DO_assumed_mean is derived from the column labelled "Dissolved" in the raw
    dataset. This interpretation (Dissolved Oxygen, mg/L) is UNVERIFIED — it is
    based on value-range consistency with CPCB NWMP parameters; the original
    column name in the source file has not been confirmed against the CPCB data
    dictionary.
  - WQI_score is a MODIFIED/CUSTOM index (Brown 1970 formula structure +
    project-specific parametrisation). It is NOT identical to any single
    published index.
  - The annual representative value for each WQI parameter is computed as
    (Min + Max) / 2 — a range-midpoint approximation, NOT a true annual mean.
  - DO_assumed_mean, pH_mean, and BOD_mean are also WQI component variables.
    Including them as ML features creates PARTIAL TARGET LEAKAGE — the model can
    partially reconstruct the WQI formula from these inputs. This model does NOT
    independently predict water quality; it approximates a partial-formula
    reconstruction. Conductivity_mean, NitrateN_mean, FC_mean, and TC_mean are
    deliberately withheld to avoid full reconstruction.
  - The Stage 3 processed dataset contains imputed values created before ML
    validation (global group-median imputation over the full dataset). This script
    mitigates that by re-imputing numeric features INSIDE each training fold using
    only that fold's training data. However, the upstream imputed columns in
    wqi_scores.csv were produced before any fold split, so residual leakage from
    the Stage 3 imputation cannot be fully eliminated for the ~5% imputed rows.
    This is explicitly disclosed here and in the output.
"""

import json
import warnings
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent
DATA_PROC = ROOT / "data" / "processed"
REPORT_IMAGES = ROOT / "report_images"
MODEL_DIR = ROOT / "model"

REPORT_IMAGES.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

WQI_CSV = DATA_PROC / "wqi_scores.csv"
PROC_CSV = DATA_PROC / "water_quality_processed.csv"

# ---------------------------------------------------------------------------
# 1. Load and merge data
# ---------------------------------------------------------------------------
print("=" * 70)
print("Stage 5: Machine Learning — WQI Score Prediction")
print("=" * 70)

wqi_df = pd.read_csv(WQI_CSV)
proc_df = pd.read_csv(PROC_CSV)

# Compute Temp_mean from processed CSV (not stored in wqi_scores.csv)
proc_df["Temp_mean"] = (proc_df["Temp_Min"] + proc_df["Temp_Max"]) / 2

df = wqi_df.merge(
    proc_df[["STN_code", "Year", "Temp_mean"]],
    on=["STN_code", "Year"],
    how="left",
)

# ---------------------------------------------------------------------------
# 2. Filter to WQI_applicable == 1 rows with valid WQI_score
# ---------------------------------------------------------------------------
ml_df = df[(df["WQI_applicable"] == 1) & df["WQI_score"].notna()].copy()
print(f"\nRows used for ML (WQI_applicable=1, WQI_score valid): {len(ml_df)}")
print(f"Unique stations (STN_code): {ml_df['STN_code'].nunique()}")
print(f"Years: {sorted(ml_df['Year'].unique())}")

# ---------------------------------------------------------------------------
# 3. Feature / target / group definitions
# ---------------------------------------------------------------------------
NUMERIC_FEATURES = ["Temp_mean", "DO_assumed_mean", "pH_mean", "BOD_mean", "Year"]
CATEGORICAL_FEATURES = ["State_Name", "Water_Body_Type"]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

TARGET = "WQI_score"
GROUP_COL = "STN_code"

X = ml_df[ALL_FEATURES].copy()
y = ml_df[TARGET].values
groups = ml_df[GROUP_COL].values

print(f"\nFeature set (Option A — Final Implementation Scope):")
for f in ALL_FEATURES:
    print(f"  {f}")
print(f"\nTarget: {TARGET}")
print(f"Group (for GroupKFold): {GROUP_COL}")

# ---------------------------------------------------------------------------
# 4. Imputation flags summary (disclosure)
# ---------------------------------------------------------------------------
imputed_flags = [
    "DO_assumed_Min_imputed_flag", "DO_assumed_Max_imputed_flag",
    "pH_Min_imputed_flag", "pH_Max_imputed_flag",
    "BOD_Min_imputed_flag", "BOD_Max_imputed_flag",
    "Temp_Min_imputed_flag", "Temp_Max_imputed_flag",
]
available_flags = [c for c in imputed_flags if c in ml_df.columns]
if available_flags:
    imputed_any = (ml_df[available_flags].sum(axis=1) > 0).sum()
    print(f"\n[DISCLOSURE] Stage 3 upstream imputation:")
    print(f"  {imputed_any} of {len(ml_df)} rows have at least one ML feature")
    print("  value derived from Stage 3 group-median imputation (pre-split).")
    print("  In-fold re-imputation below mitigates but cannot fully eliminate this.")

# ---------------------------------------------------------------------------
# 5. Build sklearn pipelines (imputation + encoding inside pipeline)
# ---------------------------------------------------------------------------
# Numeric: median imputation (fitted on train fold only) + StandardScaler
# Categorical: most-frequent imputation + OneHotEncoder (handle_unknown='ignore')

numeric_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, NUMERIC_FEATURES),
        ("cat", categorical_transformer, CATEGORICAL_FEATURES),
    ],
    remainder="drop",
)

ridge_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", Ridge(alpha=1.0)),
])

rf_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )),
])

# ---------------------------------------------------------------------------
# 6. 5-Fold GroupKFold cross-validation
# ---------------------------------------------------------------------------
gkf = GroupKFold(n_splits=5)

def run_cv(pipeline, X, y, groups, model_name):
    """Run 5-fold GroupKFold CV and return per-fold RMSE and R²."""
    fold_rmse = []
    fold_r2 = []
    fold_results = []

    print(f"\n{'-'*60}")
    print(f"Model: {model_name}")
    print(f"{'-'*60}")
    print(f"{'Fold':>5}  {'RMSE':>10}  {'R2':>10}  {'Train n':>9}  {'Val n':>7}")
    print(f"{'-'*5}  {'-'*10}  {'-'*10}  {'-'*9}  {'-'*7}")

    for fold_idx, (train_idx, val_idx) in enumerate(
        gkf.split(X, y, groups=groups), start=1
    ):
        X_train_fold = X.iloc[train_idx]
        y_train_fold = y[train_idx]
        X_val_fold = X.iloc[val_idx]
        y_val_fold = y[val_idx]

        pipeline.fit(X_train_fold, y_train_fold)
        y_pred = pipeline.predict(X_val_fold)

        rmse = np.sqrt(mean_squared_error(y_val_fold, y_pred))
        r2 = r2_score(y_val_fold, y_pred)

        fold_rmse.append(rmse)
        fold_r2.append(r2)
        fold_results.append({
            "fold": fold_idx,
            "train_n": len(train_idx),
            "val_n": len(val_idx),
            "rmse": rmse,
            "r2": r2,
        })
        print(f"{fold_idx:>5}  {rmse:>10.4f}  {r2:>10.4f}  "
              f"{len(train_idx):>9}  {len(val_idx):>7}")

    mean_rmse = np.mean(fold_rmse)
    std_rmse = np.std(fold_rmse, ddof=1)
    mean_r2 = np.mean(fold_r2)
    std_r2 = np.std(fold_r2, ddof=1)

    print(f"\n  Mean RMSE : {mean_rmse:.4f} +/- {std_rmse:.4f}")
    print(f"  Mean R2   : {mean_r2:.4f} +/- {std_r2:.4f}")

    return {
        "model_name": model_name,
        "fold_results": fold_results,
        "mean_rmse": mean_rmse,
        "std_rmse": std_rmse,
        "mean_r2": mean_r2,
        "std_r2": std_r2,
    }


ridge_cv = run_cv(ridge_pipeline, X, y, groups, "Ridge Regression (alpha=1.0)")
rf_cv = run_cv(rf_pipeline, X, y, groups, "Random Forest Regressor (n_estimators=200)")

# ---------------------------------------------------------------------------
# 7. Summary comparison table
# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
print("Model Comparison (5-fold GroupKFold CV)")
print(f"{'='*60}")
print(f"{'Model':<35}  {'Mean RMSE':>12}  {'Mean R2':>10}")
print(f"{'-'*35}  {'-'*12}  {'-'*10}")
for cv in [ridge_cv, rf_cv]:
    print(f"{cv['model_name']:<35}  "
          f"{cv['mean_rmse']:.4f} +/- {cv['std_rmse']:.4f}  "
          f"{cv['mean_r2']:.4f} +/- {cv['std_r2']:.4f}")

# ---------------------------------------------------------------------------
# 8. Retrain final models on ALL data
# ---------------------------------------------------------------------------
print("\nRetraining final models on all 160 rows...")
ridge_pipeline.fit(X, y)
rf_pipeline.fit(X, y)
print("Done.")

# ---------------------------------------------------------------------------
# 9. Save models and metadata
# ---------------------------------------------------------------------------
joblib.dump(rf_pipeline, MODEL_DIR / "best_model.pkl")
joblib.dump(ridge_pipeline, MODEL_DIR / "ridge_model.pkl")
print(f"\nSaved: model/best_model.pkl  (Random Forest)")
print(f"Saved: model/ridge_model.pkl (Ridge Regression)")

metadata = {
    "stage": "Stage 5 — Machine Learning",
    "target": "WQI_score",
    "feature_set": "Option A (Final Implementation Scope)",
    "features": ALL_FEATURES,
    "numeric_features": NUMERIC_FEATURES,
    "categorical_features": CATEGORICAL_FEATURES,
    "validation": "5-fold GroupKFold (groups = STN_code)",
    "n_rows": int(len(ml_df)),
    "n_stations": int(ml_df["STN_code"].nunique()),
    "models": {
        "ridge_regression": {
            "params": {"alpha": 1.0},
            "mean_rmse": round(ridge_cv["mean_rmse"], 4),
            "std_rmse": round(ridge_cv["std_rmse"], 4),
            "mean_r2": round(ridge_cv["mean_r2"], 4),
            "std_r2": round(ridge_cv["std_r2"], 4),
            "fold_results": ridge_cv["fold_results"],
        },
        "random_forest": {
            "params": {
                "n_estimators": 200,
                "min_samples_leaf": 3,
                "random_state": 42,
            },
            "mean_rmse": round(rf_cv["mean_rmse"], 4),
            "std_rmse": round(rf_cv["std_rmse"], 4),
            "mean_r2": round(rf_cv["mean_r2"], 4),
            "std_r2": round(rf_cv["std_r2"], 4),
            "fold_results": rf_cv["fold_results"],
        },
    },
    "disclosures": [
        "DO_assumed_mean is UNVERIFIED — column 'Dissolved' in raw data assumed "
        "to be Dissolved Oxygen (mg/L) based on value-range evidence only; not "
        "confirmed against CPCB data dictionary.",
        "WQI_score is a MODIFIED/CUSTOM index (Brown 1970 formula structure + "
        "project-specific parametrisation); not identical to any single published index.",
        "Annual representative values use (Min+Max)/2 — range-midpoint approximation, "
        "not a true annual mean.",
        "PARTIAL TARGET LEAKAGE: DO_assumed_mean, pH_mean, and BOD_mean are also WQI "
        "component variables. The model partially reconstructs the WQI formula from "
        "these inputs and does NOT independently predict water quality.",
        "Stage 3 upstream group-median imputation was applied before fold splitting. "
        "In-fold re-imputation is applied here to mitigate but cannot fully eliminate "
        "residual leakage for the ~5% imputed rows.",
    ],
    "best_model": "random_forest",
    "best_model_file": "model/best_model.pkl",
}

with open(MODEL_DIR / "model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
print(f"Saved: model/model_metadata.json")

# ---------------------------------------------------------------------------
# 10. V12 — Random Forest Feature Importance
# ---------------------------------------------------------------------------
print("\nGenerating V12: Random Forest Feature Importance...")

# Extract feature names after ColumnTransformer
cat_encoder = rf_pipeline.named_steps["preprocessor"].named_transformers_["cat"]
cat_feature_names = (
    cat_encoder.named_steps["onehot"].get_feature_names_out(CATEGORICAL_FEATURES).tolist()
)
all_feature_names = NUMERIC_FEATURES + cat_feature_names

importances = rf_pipeline.named_steps["model"].feature_importances_
importance_df = pd.DataFrame(
    {"feature": all_feature_names, "importance": importances}
).sort_values("importance", ascending=True)

fig, ax = plt.subplots(figsize=(9, max(5, len(importance_df) * 0.35)))
colors = ["#3b82d4" if imp >= importance_df["importance"].median() else "#a8c7f0"
          for imp in importance_df["importance"]]
ax.barh(importance_df["feature"], importance_df["importance"], color=colors)
ax.set_xlabel("Feature Importance (mean decrease in impurity)")
ax.set_title(
    "V12 -- Random Forest Feature Importance\n"
    "Target: WQI_score  |  Feature Set Option A  |  n=200 trees\n"
    "[!] DO/pH/BOD are also WQI components -- see partial-leakage disclosure",
    fontsize=10,
)
ax.tick_params(axis="y", labelsize=8)
plt.tight_layout()
v12_path = REPORT_IMAGES / "V12_feature_importance.png"
fig.savefig(v12_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {v12_path}")

# Print top features
print("\nTop features by importance (Random Forest):")
for _, row in importance_df.sort_values("importance", ascending=False).head(10).iterrows():
    print(f"  {row['feature']:<45}  {row['importance']:.4f}")

# ---------------------------------------------------------------------------
# 11. V13 — Actual vs Predicted WQI (out-of-fold predictions)
# ---------------------------------------------------------------------------
print("\nGenerating V13: Actual vs Predicted WQI (out-of-fold)...")

# Collect out-of-fold predictions from RF
oof_actual = np.empty(len(y))
oof_pred_rf = np.empty(len(y))
oof_pred_ridge = np.empty(len(y))

for train_idx, val_idx in gkf.split(X, y, groups=groups):
    rf_pipeline.fit(X.iloc[train_idx], y[train_idx])
    ridge_pipeline.fit(X.iloc[train_idx], y[train_idx])
    oof_actual[val_idx] = y[val_idx]
    oof_pred_rf[val_idx] = rf_pipeline.predict(X.iloc[val_idx])
    oof_pred_ridge[val_idx] = ridge_pipeline.predict(X.iloc[val_idx])

# Retrain final models on full data again after OOF collection
rf_pipeline.fit(X, y)
ridge_pipeline.fit(X, y)

oof_rmse_rf = np.sqrt(mean_squared_error(oof_actual, oof_pred_rf))
oof_r2_rf = r2_score(oof_actual, oof_pred_rf)
oof_rmse_ridge = np.sqrt(mean_squared_error(oof_actual, oof_pred_ridge))
oof_r2_ridge = r2_score(oof_actual, oof_pred_ridge)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
wqi_min = min(oof_actual.min(), oof_pred_rf.min(), oof_pred_ridge.min()) - 5
wqi_max = max(oof_actual.max(), oof_pred_rf.max(), oof_pred_ridge.max()) + 5

for ax, preds, name, rmse, r2, color in [
    (axes[0], oof_pred_ridge, "Ridge Regression", oof_rmse_ridge, oof_r2_ridge, "#3b82d4"),
    (axes[1], oof_pred_rf, "Random Forest", oof_rmse_rf, oof_r2_rf, "#7c5cd8"),
]:
    ax.scatter(oof_actual, preds, alpha=0.55, s=30, color=color, edgecolors="white", linewidths=0.4)
    ax.plot([wqi_min, wqi_max], [wqi_min, wqi_max], "k--", linewidth=1, label="Perfect fit")
    ax.set_xlim(wqi_min, wqi_max)
    ax.set_ylim(wqi_min, wqi_max)
    ax.set_xlabel("Actual WQI_score")
    ax.set_ylabel("Predicted WQI_score")
    ax.set_title(
        f"V13 — {name}\n"
        f"OOF RMSE = {rmse:.2f}  |  OOF R² = {r2:.3f}\n"
        f"5-fold GroupKFold (groups = STN_code)",
        fontsize=9,
    )
    ax.legend(fontsize=8)
    ax.set_aspect("equal", "box")

fig.suptitle(
    "Actual vs Predicted WQI_score (Out-of-Fold)\n"
    "[!] DO/pH/BOD features are WQI components -- partial leakage applies; "
    "see model_metadata.json disclosures",
    fontsize=9,
    y=1.01,
)
plt.tight_layout()
v13_path = REPORT_IMAGES / "V13_actual_vs_predicted.png"
fig.savefig(v13_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {v13_path}")

# ---------------------------------------------------------------------------
# 12. V14 — Residual Plot
# ---------------------------------------------------------------------------
print("Generating V14: Residual Plot...")

residuals_rf = oof_actual - oof_pred_rf
residuals_ridge = oof_actual - oof_pred_ridge

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

for ax, preds, residuals, name, color in [
    (axes[0], oof_pred_ridge, residuals_ridge, "Ridge Regression", "#3b82d4"),
    (axes[1], oof_pred_rf, residuals_rf, "Random Forest", "#7c5cd8"),
]:
    ax.scatter(preds, residuals, alpha=0.55, s=30, color=color, edgecolors="white", linewidths=0.4)
    ax.axhline(0, color="black", linewidth=1, linestyle="--")
    ax.set_xlabel("Predicted WQI_score")
    ax.set_ylabel("Residual (Actual − Predicted)")
    ax.set_title(
        f"V14 — {name} Residuals\n"
        f"Mean residual = {residuals.mean():.3f}  |  SD = {residuals.std():.3f}",
        fontsize=9,
    )

fig.suptitle(
    "Residual Plot (Out-of-Fold Predictions)\n"
    "[!] Partial target leakage present -- WQI components used as features",
    fontsize=9,
    y=1.01,
)
plt.tight_layout()
v14_path = REPORT_IMAGES / "V14_residuals.png"
fig.savefig(v14_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {v14_path}")

# ---------------------------------------------------------------------------
# 13. Final summary
# ---------------------------------------------------------------------------
print(f"\n{'='*70}")
print("Stage 5 Complete — Files Created")
print(f"{'='*70}")
created = [
    "stage5_ml.py              (this script)",
    "model/best_model.pkl      (Random Forest, retrained on all 160 rows)",
    "model/ridge_model.pkl     (Ridge Regression, retrained on all 160 rows)",
    "model/model_metadata.json (CV metrics, feature list, disclosures)",
    "report_images/V12_feature_importance.png",
    "report_images/V13_actual_vs_predicted.png",
    "report_images/V14_residuals.png",
]
for f in created:
    print(f"  {f}")

print(f"\n{'-'*70}")
print("MANDATORY DISCLOSURES (reproduced from file header):")
print("  1. DO_assumed_mean is UNVERIFIED -- column 'Dissolved' in raw data")
print("     assumed to be Dissolved Oxygen (mg/L) based on value-range evidence.")
print("  2. WQI_score is a MODIFIED/CUSTOM index, not any single published index.")
print("  3. Annual values use (Min+Max)/2 -- range-midpoint approximation, not a")
print("     true annual mean.")
print("  4. PARTIAL TARGET LEAKAGE: DO/pH/BOD are WQI components. The model")
print("     does NOT independently predict water quality; it approximates a")
print("     partial WQI formula reconstruction.")
print("  5. Stage 3 upstream group-median imputation pre-dates fold splits.")
print("     In-fold re-imputation applied here cannot fully eliminate residual")
print("     leakage for the ~5% imputed rows.")
print(f"{'-'*70}")
