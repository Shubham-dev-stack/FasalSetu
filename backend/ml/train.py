import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor, early_stopping, log_evaluation

from ml.evaluate import evaluate_deployment_gate, evaluate_metrics
from ml.features import (
    CATEGORICAL_COLUMNS,
    FEATURE_COLUMNS,
    create_splits,
    extract_features,
    prepare_time_series_panel,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "demand_history.csv"
META_PATH = BASE_DIR / "data" / "processed" / "demand_history.meta.json"
ARTIFACTS_DIR = BASE_DIR / "ml" / "artifacts"


def compute_file_sha256(filepath: Path) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def get_git_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=BASE_DIR)
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def evaluate_split(
    df_split: pd.DataFrame,
    point_model: LGBMRegressor,
    q10_model: LGBMRegressor,
    q90_model: LGBMRegressor,
) -> dict:
    """Evaluate point model, quantile models, and baselines on non-imputed rows of a split."""
    # Strictly filter out imputed calendar rows
    eval_df = df_split[~df_split["is_imputed"]].copy()

    X = eval_df[FEATURE_COLUMNS]
    y_true = eval_df["target_demand_kg"].to_numpy(dtype=float)

    # Predictions
    y_pred_lgbm = point_model.predict(X)
    q10_pred = q10_model.predict(X)
    q90_pred = q90_model.predict(X)

    # Post-process quantiles
    preds_stacked = np.column_stack([q10_pred, y_pred_lgbm, q90_pred])
    preds_sorted = np.sort(np.clip(preds_stacked, a_min=0.0, a_max=None), axis=1)
    q10_clean = preds_sorted[:, 0]
    y_pred_clean = preds_sorted[:, 1]
    q90_clean = preds_sorted[:, 2]

    # Baseline predictions
    b1_pred = eval_df["b1_pred"].to_numpy(dtype=float)
    b2_pred = eval_df["b2_pred"].to_numpy(dtype=float)

    overall_lgbm = evaluate_metrics(y_true, y_pred_clean, q10_clean, q90_clean)
    overall_b1 = evaluate_metrics(y_true, b1_pred)
    overall_b2 = evaluate_metrics(y_true, b2_pred)

    # Per crop metrics for LightGBM
    by_crop = {}
    for crop_id, crop_group in eval_df.groupby("crop_id", observed=True):
        c_mask = eval_df["crop_id"] == crop_id
        crop_name = crop_group["crop_name"].iloc[0]
        y_c = y_true[c_mask]
        pred_c = y_pred_clean[c_mask]
        q10_c = q10_clean[c_mask]
        q90_c = q90_clean[c_mask]
        by_crop[str(crop_name)] = evaluate_metrics(y_c, pred_c, q10_c, q90_c)

    return {
        "lgbm": overall_lgbm,
        "b1_seasonal_naive": overall_b1,
        "b2_trailing_mean": overall_b2,
        "by_crop_lgbm": by_crop,
    }


def train_models():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading raw demand history from {DATA_PATH}...")
    df_raw = pd.read_csv(DATA_PATH)
    dataset_hash = compute_file_sha256(DATA_PATH)
    git_commit = get_git_commit()

    with open(META_PATH) as f:
        meta_data = json.load(f)

    print("Preparing continuous panel with strictly causal imputation...")
    panel_df = prepare_time_series_panel(df_raw)

    print("Extracting features with 7-day cutoff...")
    df_feats = extract_features(panel_df)

    print("Creating chronological train/val/test splits...")
    train_df, val_df, test_df = create_splits(df_feats, cutoff_date="2026-09-30")

    # Filter out imputed rows from loss and training
    train_clean = train_df[~train_df["is_imputed"]].copy()
    val_clean = val_df[~val_df["is_imputed"]].copy()

    X_train = train_clean[FEATURE_COLUMNS]
    y_train = train_clean["target_demand_kg"].to_numpy(dtype=float)

    X_val = val_clean[FEATURE_COLUMNS]
    y_val = val_clean["target_demand_kg"].to_numpy(dtype=float)

    print(f"Train samples: {len(X_train)}, Val samples: {len(X_val)}, Test samples: {len(test_df[~test_df['is_imputed']])}")

    # 1. Train LGBM Point model on Train split with early stopping on Val split
    print("Fitting initial LightGBM point model on Train split...")
    point_init = LGBMRegressor(
        objective="regression",
        n_estimators=800,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=-1,
    )
    point_init.fit(
        X_train,
        y_train,
        categorical_feature=CATEGORICAL_COLUMNS,
        eval_set=[(X_val, y_val)],
        callbacks=[early_stopping(stopping_rounds=50, verbose=False), log_evaluation(period=0)],
    )
    best_n = point_init.best_iteration_ or 300
    print(f"Point model best iteration: {best_n}")

    # 2. Train quantile models on Train split
    print(f"Fitting initial Quantile models on Train split (n_estimators={best_n})...")
    q10_init = LGBMRegressor(
        objective="quantile",
        alpha=0.1,
        n_estimators=best_n,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=-1,
    )
    q10_init.fit(X_train, y_train, categorical_feature=CATEGORICAL_COLUMNS)

    q90_init = LGBMRegressor(
        objective="quantile",
        alpha=0.9,
        n_estimators=best_n,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=-1,
    )
    q90_init.fit(X_train, y_train, categorical_feature=CATEGORICAL_COLUMNS)

    # 3. Evaluate on Validation split
    print("Evaluating models on Validation split...")
    val_results = evaluate_split(val_df, point_init, q10_init, q90_init)

    # 4. Evaluate on Test split (unseen held-out evaluation)
    print("Evaluating models on Test split...")
    test_results = evaluate_split(test_df, point_init, q10_init, q90_init)

    val_mae_lgbm = val_results["lgbm"]["mae"]
    val_mae_b1 = val_results["b1_seasonal_naive"]["mae"]
    val_mae_b2 = val_results["b2_trailing_mean"]["mae"]

    test_mae_lgbm = test_results["lgbm"]["mae"]
    test_mae_b1 = test_results["b1_seasonal_naive"]["mae"]
    test_mae_b2 = test_results["b2_trailing_mean"]["mae"]

    print("\n--- Model Performance Summary ---")
    print(f"Val MAE:  LGBM={val_mae_lgbm:.2f}, B1={val_mae_b1:.2f}, B2={val_mae_b2:.2f}")
    print(f"Test MAE: LGBM={test_mae_lgbm:.2f}, B1={test_mae_b1:.2f}, B2={test_mae_b2:.2f}")

    gate_result = evaluate_deployment_gate(
        val_mae_lgbm=val_mae_lgbm,
        val_mae_b1=val_mae_b1,
        val_mae_b2=val_mae_b2,
        test_mae_lgbm=test_mae_lgbm,
        test_mae_b1=test_mae_b1,
        test_mae_b2=test_mae_b2,
    )
    print(f"Deployment Gate Passed: {gate_result['passed']}")
    print(f"Gate Reason: {gate_result['reason']}")

    # 5. Fit deployed models strictly on Train + Validation ONLY (Never on Test set)
    print("\nRefitting deployed model on Train + Validation splits ONLY (Test set remains strictly held-out)...")
    train_val_df = pd.concat([train_clean, val_clean], ignore_index=True)
    X_deploy = train_val_df[FEATURE_COLUMNS]
    y_deploy = train_val_df["target_demand_kg"].to_numpy(dtype=float)

    deployed_point = LGBMRegressor(
        objective="regression",
        n_estimators=best_n,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=-1,
    )
    deployed_point.fit(X_deploy, y_deploy, categorical_feature=CATEGORICAL_COLUMNS)

    deployed_q10 = LGBMRegressor(
        objective="quantile",
        alpha=0.1,
        n_estimators=best_n,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=-1,
    )
    deployed_q10.fit(X_deploy, y_deploy, categorical_feature=CATEGORICAL_COLUMNS)

    deployed_q90 = LGBMRegressor(
        objective="quantile",
        alpha=0.9,
        n_estimators=best_n,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=-1,
    )
    deployed_q90.fit(X_deploy, y_deploy, categorical_feature=CATEGORICAL_COLUMNS)

    # Save artifacts
    print("Saving model artifacts...")
    joblib.dump(deployed_point, ARTIFACTS_DIR / "model_point.joblib")
    joblib.dump(deployed_q10, ARTIFACTS_DIR / "model_q10.joblib")
    joblib.dump(deployed_q90, ARTIFACTS_DIR / "model_q90.joblib")

    feature_spec = {
        "model_version": "1.0.0",
        "created_at": datetime.now(UTC).isoformat(),
        "feature_columns": FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
    }
    with open(ARTIFACTS_DIR / "feature_spec.json", "w") as f:
        json.dump(feature_spec, f, indent=2)

    model_card = {
        "model_id": "MOD-01",
        "model_version": "1.0.0",
        "trained_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit,
        "dataset_hash_sha256": dataset_hash,
        "generator_version": meta_data.get("generator_version", "1.0"),
        "demand_data_source": "SYNTHETIC",
        "price_feature_sources": ["SYNTHETIC_DEMO", "AGMARKNET_SNAPSHOT"],
        "reproducibility": "Reproducible within the pinned project environment, dependency versions, dataset, generator version, and fixed seed.",
        "deployed_method": gate_result["deployed_method"],
        "deployment_gate": gate_result,
        "split_spec": {
            "train_end": str(train_df["date"].max()),
            "val_start": str(val_df["date"].min()),
            "val_end": str(val_df["date"].max()),
            "test_start": str(test_df["date"].min()),
            "test_end": str(test_df["date"].max()),
            "deployment_training_scope": "TRAIN_PLUS_VALIDATION_ONLY",
        },
        "metrics": {
            "validation": val_results,
            "test": test_results,
        },
        "disclaimer": "Demand history is synthetic, generated from a documented process. Forecast metrics validate the pipeline, not real-world accuracy.",
    }
    with open(ARTIFACTS_DIR / "model_card.json", "w") as f:
        json.dump(model_card, f, indent=2)

    print("Training pipeline complete! Artifacts successfully generated in backend/ml/artifacts/")


if __name__ == "__main__":
    train_models()
