import numpy as np


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error in kg/day."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error in kg/day."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def compute_wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Weighted Absolute Percentage Error (Primary % Metric).
    
    WAPE = (sum |y - y_hat|) / (sum y) * 100
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    sum_true = float(np.sum(y_true))
    if sum_true == 0.0:
        return 0.0
    return float((np.sum(np.abs(y_true - y_pred)) / sum_true) * 100.0)


def compute_mape(y_true: np.ndarray, y_pred: np.ndarray, min_y: float = 10.0) -> float:
    """Mean Absolute Percentage Error guarded against divide-by-near-zero (y >= min_y)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true >= min_y
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def compute_bias(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Forecast Bias (y_hat - y). Positive indicates over-forecasting."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(y_pred - y_true))


def compute_coverage(y_true: np.ndarray, q10: np.ndarray, q90: np.ndarray) -> float:
    """Empirical interval coverage percentage (share of y in [q10, q90])."""
    y_true = np.asarray(y_true, dtype=float)
    q10 = np.asarray(q10, dtype=float)
    q90 = np.asarray(q90, dtype=float)
    if len(y_true) == 0:
        return 0.0
    inside = (y_true >= q10) & (y_true <= q90)
    return float(np.mean(inside) * 100.0)


def evaluate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    q10: np.ndarray | None = None,
    q90: np.ndarray | None = None,
) -> dict[str, float | None]:
    """Calculate all standard demand forecast metrics for point and interval predictions."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    metrics: dict[str, float | None] = {
        "mae": round(compute_mae(y_true, y_pred), 2),
        "rmse": round(compute_rmse(y_true, y_pred), 2),
        "wape_pct": round(compute_wape(y_true, y_pred), 2),
        "mape_pct": round(compute_mape(y_true, y_pred), 2),
        "bias": round(compute_bias(y_true, y_pred), 2),
        "coverage_80_pct": None,
    }

    if q10 is not None and q90 is not None:
        metrics["coverage_80_pct"] = round(compute_coverage(y_true, q10, q90), 2)

    return metrics


def evaluate_deployment_gate(
    val_mae_lgbm: float,
    val_mae_b1: float,
    val_mae_b2: float,
    test_mae_lgbm: float,
    test_mae_b1: float,
    test_mae_b2: float,
) -> dict:
    """Evaluate mandatory honesty gate per ML.md §5 & AC-FC-09.
    
    Condition 1: val_MAE(LGBM) < 0.95 * min(val_MAE(B1), val_MAE(B2))
    Condition 2: test_MAE(LGBM) < min(test_MAE(B1), test_MAE(B2))
    """
    min_val_baseline = min(val_mae_b1, val_mae_b2)
    val_threshold = 0.95 * min_val_baseline
    min_test_baseline = min(test_mae_b1, test_mae_b2)

    val_passed = val_mae_lgbm < val_threshold
    test_passed = test_mae_lgbm < min_test_baseline
    gate_passed = val_passed and test_passed

    if gate_passed:
        reason = (
            f"LGBM validation MAE ({val_mae_lgbm:.2f}) beats best baseline ({min_val_baseline:.2f}) "
            f"by >5% (threshold {val_threshold:.2f}) and test MAE ({test_mae_lgbm:.2f}) beats "
            f"best baseline test MAE ({min_test_baseline:.2f})."
        )
    else:
        reasons = []
        if not val_passed:
            reasons.append(
                f"Validation MAE ({val_mae_lgbm:.2f}) failed to beat 95% of baseline ({val_threshold:.2f})"
            )
        if not test_passed:
            reasons.append(
                f"Test MAE ({test_mae_lgbm:.2f}) failed to beat baseline test MAE ({min_test_baseline:.2f})"
            )
        reason = "; ".join(reasons)

    return {
        "passed": bool(gate_passed),
        "deployed_method": "LIGHTGBM" if gate_passed else "SEASONAL_NAIVE",
        "reason": reason,
        "val_mae_lgbm": round(val_mae_lgbm, 2),
        "min_val_baseline": round(min_val_baseline, 2),
        "test_mae_lgbm": round(test_mae_lgbm, 2),
        "min_test_baseline": round(min_test_baseline, 2),
    }
