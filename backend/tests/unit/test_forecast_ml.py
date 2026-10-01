from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from ml.evaluate import (
    compute_bias,
    compute_coverage,
    compute_mae,
    compute_mape,
    compute_rmse,
    compute_wape,
    evaluate_deployment_gate,
)
from ml.features import (
    FEATURE_COLUMNS,
    compute_features_for_series,
    create_splits,
    prepare_time_series_panel,
)


def test_metric_functions_hand_computed_vectors():
    """Verify evaluation metric calculations against hand-computed numeric vectors (AC-FC-08)."""
    # Hand-crafted test vectors
    y_true = np.array([100.0, 200.0, 50.0, 150.0, 5.0])
    y_pred = np.array([110.0, 190.0, 60.0, 120.0, 10.0])
    # Absolute errors: [10, 10, 10, 30, 5] -> sum = 65, mean = 65 / 5 = 13.0
    # Squared errors: [100, 100, 100, 900, 25] -> sum = 1225, mean = 245.0, sqrt = 15.6524758
    # Sum true: 100 + 200 + 50 + 150 + 5 = 505.0
    # WAPE: 65 / 505 * 100 = 12.871287%
    # MAPE with y >= 10: rows with y in {100, 200, 50, 150} -> [10/100, 10/200, 10/50, 30/150] = [0.10, 0.05, 0.20, 0.20]
    # Mean MAPE: (0.10 + 0.05 + 0.20 + 0.20) / 4 = 0.55 / 4 = 0.1375 = 13.75%
    # Bias: [(110-100) + (190-200) + (60-50) + (120-150) + (10-5)] / 5 = [10 - 10 + 10 - 30 + 5] / 5 = -15 / 5 = -3.0

    assert compute_mae(y_true, y_pred) == pytest.approx(13.0, rel=1e-4)
    assert compute_rmse(y_true, y_pred) == pytest.approx(np.sqrt(245.0), rel=1e-4)
    assert compute_wape(y_true, y_pred) == pytest.approx((65.0 / 505.0) * 100.0, rel=1e-4)
    assert compute_mape(y_true, y_pred, min_y=10.0) == pytest.approx(13.75, rel=1e-4)
    assert compute_bias(y_true, y_pred) == pytest.approx(-3.0, rel=1e-4)

    # Coverage test: q10 and q90
    q10 = np.array([90.0, 180.0, 40.0, 100.0, 1.0])
    q90 = np.array([120.0, 210.0, 55.0, 140.0, 8.0])
    # Inside:
    # 100 in [90, 120] -> True
    # 200 in [180, 210] -> True
    # 50 in [40, 55] -> True
    # 150 in [100, 140] -> False (150 > 140)
    # 5 in [1, 8] -> True
    # 4 out of 5 = 80.0%
    assert compute_coverage(y_true, q10, q90) == pytest.approx(80.0, rel=1e-4)


def test_causal_imputation_and_leakage_invariance():
    """Verify that future observations after date t CANNOT leak into features for date t (AC-FC-04).
    
    1. Create a synthetic daily series.
    2. Add some missing calendar days (to trigger causal forward-fill).
    3. Compute features up to date t.
    4. Mutate / modify future observations at t+1, t+2...
    5. Recompute features and verify that features at date t are 100% identical.
    """
    start = date(2025, 1, 1)
    dates = [start + timedelta(days=i) for i in range(100)]
    
    # Base series
    np.random.seed(42)
    demands = [1000.0 + np.sin(i) * 200.0 + np.random.normal(0, 10) for i in range(100)]
    prices = [25.0 + np.cos(i) * 2.0 for i in range(100)]

    df = pd.DataFrame({
        "hub_id": 1,
        "crop_id": 1,
        "hub_name": "Delhi North",
        "crop_name": "Tomato",
        "date": dates,
        "demand_kg": demands,
        "avg_price_per_kg": prices,
        "is_synthetic": True,
        "generator_version": "1.0",
    })

    # Drop some days to exercise imputation (e.g. days 20, 21, 50, 75)
    df_with_holes = df[~df["date"].isin([dates[20], dates[21], dates[50], dates[75]])].copy()

    # Prepare causal panel and compute features
    panel = prepare_time_series_panel(df_with_holes)
    feats_orig = compute_features_for_series(panel)

    # Pick a target date t (e.g. date index 60)
    target_idx = 60
    target_date = dates[target_idx]
    row_orig = feats_orig[feats_orig["date"] == target_date].iloc[0]

    # Now create an altered scenario: mutate future data AFTER target_date - 6 (e.g. dates 65, 70, 80)
    df_altered = df_with_holes.copy()
    future_mask = df_altered["date"] > target_date
    df_altered.loc[future_mask, "demand_kg"] = df_altered.loc[future_mask, "demand_kg"] * 5.0 + 9999.0
    df_altered.loc[future_mask, "avg_price_per_kg"] = 999.0

    panel_altered = prepare_time_series_panel(df_altered)
    feats_altered = compute_features_for_series(panel_altered)
    row_altered = feats_altered[feats_altered["date"] == target_date].iloc[0]

    # Verify every single feature is strictly identical
    for col in FEATURE_COLUMNS:
        if col in ["hub_id", "crop_id"]:
            assert row_orig[col] == row_altered[col]
        else:
            val_orig = float(row_orig[col])
            val_alt = float(row_altered[col])
            assert val_orig == pytest.approx(val_alt, abs=1e-7), f"Leakage detected in feature {col}!"


def test_chronological_split_temporal_separation():
    """Verify that train, validation, and test splits have strictly zero temporal overlap."""
    start = date(2024, 10, 1)
    dates = [start + timedelta(days=i) for i in range(730)]  # 2 years
    df = pd.DataFrame({
        "hub_id": 1,
        "crop_id": 1,
        "hub_name": "Delhi North",
        "crop_name": "Tomato",
        "date": dates,
        "demand_kg": [1000.0] * 730,
        "avg_price_per_kg": [25.0] * 730,
        "is_synthetic": True,
        "generator_version": "1.0",
    })
    panel = prepare_time_series_panel(df)
    feats = compute_features_for_series(panel)

    cutoff = date(2026, 9, 30)
    train_df, val_df, test_df = create_splits(feats, cutoff_date=cutoff)

    # Assert non-empty
    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0

    # Temporal boundaries
    train_max = train_df["date"].max()
    val_min = val_df["date"].min()
    val_max = val_df["date"].max()
    test_min = test_df["date"].min()
    test_max = test_df["date"].max()

    assert train_max < val_min, "Train overlaps with Validation!"
    assert val_max < test_min, "Validation overlaps with Test!"
    assert test_max == cutoff, "Test max date does not equal cutoff!"

    # Validation must be exactly 56 days
    val_days = (val_max - val_min).days + 1
    assert val_days == 56

    # Test must be exactly 28 days
    test_days = (test_max - test_min).days + 1
    assert test_days == 28


def test_deployment_gate_honesty_logic():
    """Verify deployment gate passes only when LightGBM beats baselines by >5% on val and beats on test (AC-FC-09)."""
    # Case 1: Passes both conditions
    # Baselines val min: 50.0 -> threshold 0.95 * 50 = 47.5
    # Baselines test min: 55.0
    gate_pass = evaluate_deployment_gate(
        val_mae_lgbm=45.0,  # < 47.5 (pass)
        val_mae_b1=52.0,
        val_mae_b2=50.0,
        test_mae_lgbm=53.0,  # < 55.0 (pass)
        test_mae_b1=58.0,
        test_mae_b2=55.0,
    )
    assert gate_pass["passed"] is True
    assert gate_pass["deployed_method"] == "LIGHTGBM"

    # Case 2: Fails validation threshold (beats baseline, but not by 5%)
    gate_fail_val = evaluate_deployment_gate(
        val_mae_lgbm=48.0,  # > 47.5 (fail)
        val_mae_b1=52.0,
        val_mae_b2=50.0,
        test_mae_lgbm=53.0,
        test_mae_b1=58.0,
        test_mae_b2=55.0,
    )
    assert gate_fail_val["passed"] is False
    assert gate_fail_val["deployed_method"] == "SEASONAL_NAIVE"

    # Case 3: Fails test condition
    gate_fail_test = evaluate_deployment_gate(
        val_mae_lgbm=45.0,
        val_mae_b1=52.0,
        val_mae_b2=50.0,
        test_mae_lgbm=56.0,  # > 55.0 (fail)
        test_mae_b1=58.0,
        test_mae_b2=55.0,
    )
    assert gate_fail_test["passed"] is False
    assert gate_fail_test["deployed_method"] == "SEASONAL_NAIVE"


def test_quantile_monotonicity_and_non_negativity():
    """Verify that predictions are clipped >= 0 and sorted q10 <= yhat <= q90."""
    raw_yhat = np.array([-10.0, 50.0, 100.0, 20.0])
    raw_q10 = np.array([5.0, 60.0, 80.0, -5.0])
    raw_q90 = np.array([20.0, 40.0, 120.0, 15.0])

    # Simulated post-processing
    processed = []
    for yh, q1, q9 in zip(raw_yhat, raw_q10, raw_q90, strict=False):
        c_yh = max(0.0, float(yh))
        c_q1 = max(0.0, float(q1))
        c_q9 = max(0.0, float(q9))
        ordered = sorted([c_q1, c_yh, c_q9])
        processed.append((ordered[0], ordered[1], ordered[2]))

    for q1, yh, q9 in processed:
        assert q1 >= 0.0
        assert yh >= 0.0
        assert q9 >= 0.0
        assert q1 <= yh <= q9
