import json
import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.db.models import Crop, DemandHistory, DemandHub
from ml.features import CATEGORICAL_COLUMNS, FEATURE_COLUMNS

logger = logging.getLogger("fasalsetu.ml.predict")

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "ml" / "artifacts"

# In-memory artifact cache
_LOADED_ARTIFACTS: dict[str, Any] | None = None


def get_model_artifacts() -> dict[str, Any] | None:
    """Load model artifacts into memory once."""
    global _LOADED_ARTIFACTS
    if _LOADED_ARTIFACTS is not None:
        return _LOADED_ARTIFACTS

    point_path = ARTIFACTS_DIR / "model_point.joblib"
    q10_path = ARTIFACTS_DIR / "model_q10.joblib"
    q90_path = ARTIFACTS_DIR / "model_q90.joblib"
    card_path = ARTIFACTS_DIR / "model_card.json"
    spec_path = ARTIFACTS_DIR / "feature_spec.json"

    if not (point_path.exists() and q10_path.exists() and q90_path.exists() and card_path.exists()):
        logger.warning("Forecast model artifacts missing at %s", ARTIFACTS_DIR)
        return None

    try:
        point_model = joblib.load(point_path)
        q10_model = joblib.load(q10_path)
        q90_model = joblib.load(q90_path)
        with open(card_path) as f:
            model_card = json.load(f)
        with open(spec_path) as f:
            feature_spec = json.load(f)

        _LOADED_ARTIFACTS = {
            "point_model": point_model,
            "q10_model": q10_model,
            "q90_model": q90_model,
            "model_card": model_card,
            "feature_spec": feature_spec,
        }
        return _LOADED_ARTIFACTS
    except Exception as e:
        logger.exception("Failed to load forecast artifacts: %s", e)
        return None


def build_inference_feature_row(
    history_lookup: dict[date, tuple[float, float]],
    target_date: date,
    hub_id: int,
    crop_id: int,
) -> dict[str, Any]:
    """Construct the feature vector for target_date using information up to target_date - 7 days."""
    d_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=UTC)
    dow = d_dt.weekday()
    month = d_dt.month
    week_of_year = int(d_dt.isocalendar()[1])
    is_weekend = int(dow in (5, 6))
    doy = d_dt.timetuple().tm_yday
    doy_sin = float(np.sin(2 * np.pi * doy / 365.25))
    doy_cos = float(np.cos(2 * np.pi * doy / 365.25))

    d7 = target_date - timedelta(days=7)
    d14 = target_date - timedelta(days=14)
    d28 = target_date - timedelta(days=28)

    lag_7 = history_lookup[d7][0]
    lag_14 = history_lookup[d14][0]
    lag_28 = history_lookup[d28][0]

    demand_7_vals = [history_lookup[target_date - timedelta(days=i)][0] for i in range(7, 14)]
    roll_mean_7 = float(np.mean(demand_7_vals))
    roll_std_7 = float(np.std(demand_7_vals, ddof=0))

    demand_28_vals = [history_lookup[target_date - timedelta(days=i)][0] for i in range(7, 35)]
    roll_mean_28 = float(np.mean(demand_28_vals))

    price_lag_7 = history_lookup[d7][1]
    price_7_vals = [history_lookup[target_date - timedelta(days=i)][1] for i in range(7, 14)]
    price_roll_mean_7 = float(np.mean(price_7_vals))

    price_lag_14 = history_lookup[d14][1]
    if price_lag_14 > 0:
        price_change_7 = float((price_lag_7 / price_lag_14) - 1.0)
    else:
        price_change_7 = 0.0

    return {
        "hub_id": hub_id,
        "crop_id": crop_id,
        "dow": dow,
        "month": month,
        "week_of_year": week_of_year,
        "is_weekend": is_weekend,
        "doy_sin": doy_sin,
        "doy_cos": doy_cos,
        "lag_7": lag_7,
        "lag_14": lag_14,
        "lag_28": lag_28,
        "roll_mean_7": roll_mean_7,
        "roll_std_7": roll_std_7,
        "roll_mean_28": roll_mean_28,
        "price_lag_7": price_lag_7,
        "price_roll_mean_7": price_roll_mean_7,
        "price_change_7": price_change_7,
    }


def predict_demand(
    db: Session,
    hub_id: int,
    crop_id: int,
    horizon_days: int = 7,
    cutoff_date: date | None = None,
) -> dict[str, Any]:
    """Generate demand forecast for (hub_id, crop_id) up to horizon_days."""
    if horizon_days < 1 or horizon_days > 7:
        raise AppException(
            status_code=400,
            code="INVALID_HORIZON",
            message="horizon_days must be between 1 and 7.",
        )

    # 1. Validate Hub and Crop exist
    hub = db.query(DemandHub).filter(DemandHub.id == hub_id).first()
    if not hub:
        raise AppException(
            status_code=404,
            code="HUB_NOT_FOUND",
            message=f"Demand hub with ID {hub_id} not found.",
        )

    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise AppException(
            status_code=404,
            code="CROP_NOT_FOUND",
            message=f"Crop with ID {crop_id} not found.",
        )

    # 2. Determine Cutoff Date T
    if cutoff_date is None:
        max_record_date = (
            db.query(func.max(DemandHistory.date))
            .filter(DemandHistory.hub_id == hub_id, DemandHistory.crop_id == crop_id)
            .scalar()
        )
        if not max_record_date:
            raise AppException(
                status_code=422,
                code="INSUFFICIENT_HISTORY",
                message=f"No demand history found for hub {hub.name} and crop {crop.name}.",
            )
        T = max_record_date
    else:
        T = cutoff_date

    # 3. Fetch history window (need at least 35 days prior to T for LightGBM, 14 days for naive)
    # Fetch 90 days of history prior to and including T
    history_start = T - timedelta(days=90)
    records = (
        db.query(DemandHistory)
        .filter(
            DemandHistory.hub_id == hub_id,
            DemandHistory.crop_id == crop_id,
            DemandHistory.date >= history_start,
            DemandHistory.date <= T,
        )
        .order_by(DemandHistory.date.asc())
        .all()
    )

    if len(records) < 14:
        raise AppException(
            status_code=422,
            code="INSUFFICIENT_HISTORY",
            message=(
                f"Insufficient historical observations for hub {hub.name} and crop {crop.name}. "
                f"Required at least 14 days, found {len(records)}."
            ),
        )

    # Reindex onto continuous daily calendar up to T with strictly causal forward fill
    full_dates = [records[0].date + timedelta(days=i) for i in range((T - records[0].date).days + 1)]
    rec_by_date = {r.date: r for r in records}

    causal_history: dict[date, tuple[float, float]] = {}
    last_demand = float(records[0].demand_kg)
    last_price = float(records[0].avg_price_per_kg)

    for d in full_dates:
        if d in rec_by_date:
            last_demand = float(rec_by_date[d].demand_kg)
            last_price = float(rec_by_date[d].avg_price_per_kg)
        causal_history[d] = (last_demand, last_price)

    # Check days of history available before T
    available_history_days = (T - records[0].date).days + 1
    artifacts = get_model_artifacts()

    can_use_lgbm = (
        artifacts is not None
        and artifacts["model_card"].get("deployed_method") == "LIGHTGBM"
        and available_history_days >= 35
    )

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    forecast_items = []
    method = "LIGHTGBM" if can_use_lgbm else "SEASONAL_NAIVE_FALLBACK"

    if can_use_lgbm:
        try:
            # Build feature matrix for target dates T+1 .. T+horizon_days
            rows = []
            target_dates = [T + timedelta(days=k) for k in range(1, horizon_days + 1)]
            for d_target in target_dates:
                row = build_inference_feature_row(causal_history, d_target, hub_id, crop_id)
                rows.append(row)

            df_inf = pd.DataFrame(rows)
            for col in CATEGORICAL_COLUMNS:
                df_inf[col] = df_inf[col].astype("category")

            X_inf = df_inf[FEATURE_COLUMNS]

            point_preds = artifacts["point_model"].predict(X_inf)
            q10_preds = artifacts["q10_model"].predict(X_inf)
            q90_preds = artifacts["q90_model"].predict(X_inf)

            # Enforce non-negativity and monotonic sort [q10 <= point <= q90]
            preds_stacked = np.column_stack([q10_preds, point_preds, q90_preds])
            preds_sorted = np.sort(np.clip(preds_stacked, 0.0, None), axis=1)

            for idx, d_target in enumerate(target_dates):
                q10_val = round(float(preds_sorted[idx, 0]), 1)
                point_val = round(float(preds_sorted[idx, 1]), 1)
                q90_val = round(float(preds_sorted[idx, 2]), 1)
                forecast_items.append(
                    {
                        "date": d_target.isoformat(),
                        "day_of_week": day_names[d_target.weekday()],
                        "point_forecast_kg": point_val,
                        "interval_lo_kg": q10_val,
                        "interval_hi_kg": q90_val,
                    }
                )
        except Exception as e:
            logger.exception("LightGBM inference error, falling back to seasonal naive: %s", e)
            method = "SEASONAL_NAIVE_FALLBACK"
            forecast_items.clear()

    if method == "SEASONAL_NAIVE_FALLBACK":
        target_dates = [T + timedelta(days=k) for k in range(1, horizon_days + 1)]
        for d_target in target_dates:
            naive_target = d_target - timedelta(days=7)
            naive_point = round(causal_history.get(naive_target, (last_demand, 0.0))[0], 1)
            forecast_items.append(
                {
                    "date": d_target.isoformat(),
                    "day_of_week": day_names[d_target.weekday()],
                    "point_forecast_kg": naive_point,
                    "interval_lo_kg": None,
                    "interval_hi_kg": None,
                }
            )

    # Return last 28 days of observed history
    recent_history_records = [r for r in records if r.date >= (T - timedelta(days=27))]
    history_items = [
        {
            "date": r.date.isoformat(),
            "demand_kg": round(float(r.demand_kg), 1),
            "is_synthetic": bool(r.is_synthetic),
        }
        for r in recent_history_records
    ]

    card = artifacts["model_card"] if artifacts else {}

    return {
        "hub_id": hub.id,
        "hub_name": hub.name,
        "crop_id": crop.id,
        "crop_name": crop.name,
        "cutoff_date": T.isoformat(),
        "horizon_days": horizon_days,
        "method": method,
        "model_version": card.get("model_version", "1.0.0"),
        "demand_data_source": "SYNTHETIC",
        "price_feature_sources": ["SYNTHETIC_DEMO", "AGMARKNET_SNAPSHOT"],
        "reproducibility": card.get(
            "reproducibility",
            "Reproducible within the pinned project environment, dependency versions, dataset, generator version, and fixed seed.",
        ),
        "disclaimer": (
            "Demand history is synthetic, generated from a documented process. "
            "Forecast metrics validate the pipeline, not real-world accuracy."
        ),
        "history": history_items,
        "forecast": forecast_items,
    }
