from datetime import date, timedelta

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "hub_id",
    "crop_id",
    "dow",
    "month",
    "week_of_year",
    "is_weekend",
    "doy_sin",
    "doy_cos",
    "lag_7",
    "lag_14",
    "lag_28",
    "roll_mean_7",
    "roll_std_7",
    "roll_mean_28",
    "price_lag_7",
    "price_roll_mean_7",
    "price_change_7",
]

CATEGORICAL_COLUMNS = ["hub_id", "crop_id"]


def prepare_time_series_panel(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Prepare a continuous daily time series panel with strictly causal imputation.
    
    1. Reindexes onto complete calendar index per (hub_id, crop_id).
    2. Flags missing days as is_imputed=True and sets target_demand_kg=NaN.
    3. Fills feature computation series causal_demand_kg forward-only (ffill).
       No future observation is ever accessed for causal imputation.
    """
    df = df_raw.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date

    min_date = df["date"].min()
    max_date = df["date"].max()
    full_dates = [min_date + timedelta(days=i) for i in range((max_date - min_date).days + 1)]

    panels = []
    series_groups = df.groupby(["hub_id", "crop_id"])

    for (hub_id, crop_id), group in series_groups:
        hub_name = group["hub_name"].iloc[0]
        crop_name = group["crop_name"].iloc[0]

        # Reindex onto complete calendar
        cal_df = pd.DataFrame({"date": full_dates})
        merged = pd.merge(cal_df, group, on="date", how="left")

        merged["hub_id"] = hub_id
        merged["crop_id"] = crop_id
        merged["hub_name"] = hub_name
        merged["crop_name"] = crop_name

        # Preserve genuine observed targets
        merged["target_demand_kg"] = merged["demand_kg"]
        merged["is_imputed"] = merged["target_demand_kg"].isna()

        # Causal imputation: forward-fill ONLY
        # Past observations propagate forward; future observations have zero effect
        merged["causal_demand_kg"] = merged["target_demand_kg"].ffill()
        # Edge case: if leading days are missing, backfill from first observed
        if merged["causal_demand_kg"].isna().any():
            merged["causal_demand_kg"] = merged["causal_demand_kg"].bfill()

        # Causal price
        merged["causal_price_per_kg"] = merged["avg_price_per_kg"].ffill()
        if merged["causal_price_per_kg"].isna().any():
            merged["causal_price_per_kg"] = merged["causal_price_per_kg"].bfill()

        panels.append(merged)

    panel_df = pd.concat(panels, ignore_index=True)
    panel_df.sort_values(["hub_id", "crop_id", "date"], inplace=True)
    panel_df.reset_index(drop=True, inplace=True)
    return panel_df


def compute_features_for_series(sub_df: pd.DataFrame) -> pd.DataFrame:
    """Compute features for a single (hub, crop) time series.
    
    All features for target date d use information strictly at or before d - 7.
    """
    df = sub_df.copy()
    d_series = pd.to_datetime(df["date"])

    # Calendar features from target date d
    df["dow"] = d_series.dt.dayofweek
    df["month"] = d_series.dt.month
    df["week_of_year"] = d_series.dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["dow"].isin([5, 6]).astype(int)
    day_of_year = d_series.dt.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)

    x = df["causal_demand_kg"]
    p = df["causal_price_per_kg"]

    # Shifted lag features (using x[d - 7], x[d - 14], x[d - 28])
    df["lag_7"] = x.shift(7)
    df["lag_14"] = x.shift(14)
    df["lag_28"] = x.shift(28)

    # Shifted rolling features:
    # roll_mean_7: mean over x[d - 13 ... d - 7] (7 days)
    # roll_std_7: std over x[d - 13 ... d - 7]
    # roll_mean_28: mean over x[d - 34 ... d - 7] (28 days)
    x_shifted_7 = x.shift(7)
    df["roll_mean_7"] = x_shifted_7.rolling(window=7, min_periods=7).mean()
    df["roll_std_7"] = x_shifted_7.rolling(window=7, min_periods=7).std(ddof=0)
    df["roll_mean_28"] = x_shifted_7.rolling(window=28, min_periods=28).mean()

    # Shifted price features
    p_shifted_7 = p.shift(7)
    df["price_lag_7"] = p_shifted_7
    df["price_roll_mean_7"] = p_shifted_7.rolling(window=7, min_periods=7).mean()
    p_shifted_14 = p.shift(14)
    df["price_change_7"] = (p_shifted_7 / p_shifted_14) - 1.0

    # Fill any numerical standard deviation NaN or division inf
    df["roll_std_7"] = df["roll_std_7"].fillna(0.0)
    df["price_change_7"] = df["price_change_7"].replace([np.inf, -np.inf], 0.0).fillna(0.0)

    # Baseline predictions
    # B1: Seasonal Naive = x[d - 7]
    df["b1_pred"] = df["lag_7"]
    # B2: Shifted Trailing Mean = (1/7) * sum(x[d - i]) for i = 7..13
    df["b2_pred"] = df["roll_mean_7"]

    return df


def extract_features(panel_df: pd.DataFrame) -> pd.DataFrame:
    """Extract features across all 25 hub x crop time series."""
    processed = []
    for _, group in panel_df.groupby(["hub_id", "crop_id"]):
        feat_group = compute_features_for_series(group)
        processed.append(feat_group)

    df_feats = pd.concat(processed, ignore_index=True)

    # Cast categoricals explicitly
    for col in CATEGORICAL_COLUMNS:
        df_feats[col] = df_feats[col].astype("category")

    return df_feats


def create_splits(
    df_feats: pd.DataFrame,
    cutoff_date: date | str = "2026-09-30",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create chronological splits per Data.md §3 and ML.md §3.
    
    T = cutoff_date
    - Drops initial ~35 days lacking 28-day history window
    - Train: oldest -> T - 84 days
    - Validation: T - 83 -> T - 28 days (56 days)
    - Test: T - 27 -> T (28 days)
    """
    df = df_feats.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    if isinstance(cutoff_date, str):
        T = pd.to_datetime(cutoff_date).date()
    else:
        T = cutoff_date

    # Drop rows where lag_28 or roll_mean_28 is NaN (first 34 days)
    valid_history = df["lag_28"].notna() & df["roll_mean_28"].notna()
    df = df[valid_history].copy()

    val_start = T - timedelta(days=83)
    val_end = T - timedelta(days=28)
    test_start = T - timedelta(days=27)

    train_df = df[df["date"] < val_start].copy()
    val_df = df[(df["date"] >= val_start) & (df["date"] <= val_end)].copy()
    test_df = df[(df["date"] >= test_start) & (df["date"] <= T)].copy()

    return train_df, val_df, test_df
