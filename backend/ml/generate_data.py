"""Synthetic Demand & Market Price Generator (Data.md §4, ML.md §2).

Generates:
1. Complete panel: 5 hubs × 5 crops × 730 days = exactly 18,250 rows.
2. Deterministic post-dropout dataset (~1% missing days for pipeline evaluation).
3. Synthetic benchmark market prices for the last 90 days.
4. Provenance metadata and database persistence with safe preservation of real snapshot data.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.dates import today_ist
from app.db.models import DemandHistory, MarketPrice

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "generator.yaml"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def load_generator_config(config_path: Path | str | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Generator config not found at: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_panels(
    config: dict[str, Any] | None = None,
    end_date: date | None = None,
    seed: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate:

    1. complete_panel_df (exactly 18,250 rows before dropout)
    2. post_dropout_df (~1% dropout applied deterministically)
    3. synthetic_prices_df (last 90 days min/modal/max benchmark prices)
    """
    if config is None:
        config = load_generator_config()

    random_seed = seed if seed is not None else int(config.get("seed", 42))
    horizon_days = int(config.get("horizon_days", 730))
    elasticity = float(config.get("elasticity", 0.3))
    noise_sigma = float(config.get("noise_sigma", 0.12))
    shock_prob = float(config.get("shock_prob", 0.01))
    dropout_prob = float(config.get("dropout_prob", 0.01))
    trend_per_year = float(config.get("trend_per_year", 0.03))
    ar1_phi = float(config.get("ar1_phi", 0.70))
    ar1_sigma = float(config.get("ar1_sigma", 0.04))

    base_prices = config["base_prices"]
    base_demand = config["base_demand"]
    hub_scale = config["hub_scale"]
    seasonal_amp = config.get(
        "seasonal_amplitude",
        {"Tomato": 0.25, "Onion": 0.15, "Potato": 0.10, "Cauliflower": 0.35, "Green Chilli": 0.20},
    )
    seasonal_phase = config.get(
        "seasonal_phase_doy",
        {"Tomato": 60, "Onion": 120, "Potato": 30, "Cauliflower": 340, "Green Chilli": 200},
    )
    dow_factors = {int(k): float(v) for k, v in config.get("dow_factors", {}).items()}
    if not dow_factors:
        dow_factors = {0: 0.95, 1: 0.98, 2: 1.00, 3: 1.02, 4: 1.08, 5: 1.15, 6: 0.82}

    # Reference entities: 5 hubs × 5 crops
    crops = list(base_prices.keys())
    hubs = list(hub_scale.keys())

    # Map name -> 1-based ID matching seeded reference data
    crop_ids = {name: idx + 1 for idx, name in enumerate(crops)}
    hub_ids = {name: idx + 1 for idx, name in enumerate(hubs)}

    if end_date is None:
        target_end = today_ist() - timedelta(days=1)
    else:
        target_end = end_date

    start_date = target_end - timedelta(days=horizon_days - 1)
    date_list = [start_date + timedelta(days=i) for i in range(horizon_days)]

    # Deterministic RNGs
    rng_price = np.random.RandomState(random_seed)
    rng_noise = np.random.RandomState(random_seed + 1)
    rng_shock = np.random.RandomState(random_seed + 2)
    rng_drop = np.random.RandomState(random_seed + 3)

    # 1. Pre-generate daily crop-level price series (AR1 noise + seasonality + anchor)
    price_series: dict[str, np.ndarray] = {}
    for crop in crops:
        b_price = base_prices[crop]
        amp = seasonal_amp.get(crop, 0.20)
        phase = seasonal_phase.get(crop, 100)

        # Autoregressive AR(1) process
        eps = np.zeros(horizon_days)
        innovations = rng_price.normal(0, ar1_sigma, horizon_days)
        eps[0] = innovations[0]
        for t in range(1, horizon_days):
            eps[t] = ar1_phi * eps[t - 1] + np.sqrt(1 - ar1_phi**2) * innovations[t]

        prices = np.zeros(horizon_days)
        for t, d in enumerate(date_list):
            doy = d.timetuple().tm_yday
            # Price seasonality has roughly inverse/shifted phase vs supply
            seas = 1.0 + (amp * 0.7) * np.sin(2 * np.pi * (doy - phase - 90) / 365.25)
            raw_p = b_price * seas * np.exp(eps[t])
            prices[t] = max(round(raw_p, 2), 1.0)

        # DEMO-PRICE-ANCHOR: last 30 days mean-reverted to within ±10% of base_price
        for t in range(horizon_days - 30, horizon_days):
            target_lo = b_price * 0.90
            target_hi = b_price * 1.10
            prices[t] = round(float(np.clip(prices[t], target_lo, target_hi)), 2)

        price_series[crop] = prices

    # 2. Generate Complete Panel (5 hubs × 5 crops × 730 days = 18,250 rows)
    rows: list[dict[str, Any]] = []
    for hub in hubs:
        h_id = hub_ids[hub]
        h_scale = hub_scale[hub]

        for crop in crops:
            c_id = crop_ids[crop]
            b_kg = base_demand[crop]
            amp = seasonal_amp.get(crop, 0.20)
            phase = seasonal_phase.get(crop, 100)
            b_price = base_prices[crop]
            prices = price_series[crop]

            for t, d in enumerate(date_list):
                level = b_kg * h_scale
                doy = d.timetuple().tm_yday
                seasonal = 1.0 + amp * np.sin(2 * np.pi * (doy - phase) / 365.25)
                dow = dow_factors.get(d.weekday(), 1.0)
                trend = 1.0 + trend_per_year * (t / 365.0)

                p = prices[t]
                price_effect = (p / b_price) ** (-elasticity)

                shock = 1.5 if rng_shock.uniform() < shock_prob else 1.0
                noise = rng_noise.lognormal(0.0, noise_sigma)

                demand_kg = level * seasonal * dow * trend * price_effect * shock * noise
                demand_kg = max(round(float(demand_kg), 1), 10.0)

                rows.append(
                    {
                        "hub_id": h_id,
                        "hub_name": hub,
                        "crop_id": c_id,
                        "crop_name": crop,
                        "date": d,
                        "demand_kg": demand_kg,
                        "avg_price_per_kg": p,
                        "is_synthetic": True,
                        "generator_version": "1.0",
                    }
                )

    complete_panel_df = pd.DataFrame(rows)
    # Sort strictly chronologically
    complete_panel_df.sort_values(by=["hub_id", "crop_id", "date"], inplace=True)
    complete_panel_df.reset_index(drop=True, inplace=True)

    # 3. Apply Deterministic ~1% Dropout
    # Draw dropout mask deterministically
    n_rows = len(complete_panel_df)
    drop_mask = rng_drop.uniform(0.0, 1.0, n_rows) < dropout_prob

    # Ensure we never drop all rows for any (hub, crop) series
    post_dropout_df = complete_panel_df[~drop_mask].copy().reset_index(drop=True)

    # 4. Generate Synthetic Daily Benchmark Market Prices (last 90 days)
    # Stored in market_prices with source="SYNTHETIC_DEMO", is_synthetic=True
    cutoff_date = target_end - timedelta(days=89)
    recent_panel = complete_panel_df[complete_panel_df["date"] >= cutoff_date].copy()

    price_rows: list[dict[str, Any]] = []
    for _, row in recent_panel.iterrows():
        modal = float(row["avg_price_per_kg"])
        min_p = round(modal * 0.90, 2)
        max_p = round(modal * 1.10, 2)
        # Ensure min <= modal <= max
        if min_p > modal:
            min_p = modal
        if max_p < modal:
            max_p = modal

        price_rows.append(
            {
                "hub_id": int(row["hub_id"]),
                "crop_id": int(row["crop_id"]),
                "market_name": f"{row['hub_name']} Reference Market (SYNTHETIC)",
                "price_date": row["date"],
                "min_price_per_kg": min_p,
                "modal_price_per_kg": modal,
                "max_price_per_kg": max_p,
                "source": "SYNTHETIC_DEMO",
                "is_synthetic": True,
            }
        )

    synthetic_prices_df = pd.DataFrame(price_rows)
    synthetic_prices_df.sort_values(by=["hub_id", "crop_id", "price_date"], inplace=True)
    synthetic_prices_df.reset_index(drop=True, inplace=True)

    return complete_panel_df, post_dropout_df, synthetic_prices_df


def save_datasets(
    post_dropout_df: pd.DataFrame,
    complete_panel_df: pd.DataFrame,
    synthetic_prices_df: pd.DataFrame,
    output_dir: Path | None = None,
    config: dict[str, Any] | None = None,
) -> tuple[Path, Path, Path]:
    """Save processed CSVs and provenance metadata."""
    out_dir = output_dir or DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save demand history CSV
    demand_csv_path = out_dir / "demand_history.csv"
    post_dropout_df.to_csv(demand_csv_path, index=False)

    # Save demand history metadata (Data.md §11)
    meta_path = out_dir / "demand_history.meta.json"
    meta = {
        "dataset_id": "DS-01",
        "data_source": "SYNTHETIC",
        "generator_version": "1.0",
        "seed": int(config.get("seed", 42)) if config else 42,
        "pre_dropout_rows": len(complete_panel_df),
        "post_dropout_rows": len(post_dropout_df),
        "dropped_rows": len(complete_panel_df) - len(post_dropout_df),
        "dropout_rate_pct": round(
            (len(complete_panel_df) - len(post_dropout_df)) / len(complete_panel_df) * 100, 2
        ),
        "num_hubs": int(complete_panel_df["hub_id"].nunique()),
        "num_crops": int(complete_panel_df["crop_id"].nunique()),
        "start_date": str(complete_panel_df["date"].min()),
        "end_date": str(complete_panel_df["date"].max()),
        "generated_at": datetime.now(UTC).isoformat(),
        "disclaimer": (
            "Demand history is synthetic, generated from a documented process. "
            "Forecast metrics validate the pipeline, not real-world accuracy."
        ),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Save synthetic prices metadata
    prices_meta_path = out_dir / "prices.meta.json"
    prices_meta = {
        "dataset_id": "DS-02",
        "data_source": "SYNTHETIC_DEMO",
        "num_rows": len(synthetic_prices_df),
        "start_date": str(synthetic_prices_df["price_date"].min()),
        "end_date": str(synthetic_prices_df["price_date"].max()),
        "generated_at": datetime.now(UTC).isoformat(),
        "disclaimer": "Market prices are synthetic benchmarks derived from generator price levels.",
    }
    with open(prices_meta_path, "w", encoding="utf-8") as f:
        json.dump(prices_meta, f, indent=2)

    return demand_csv_path, meta_path, prices_meta_path


def seed_demand_and_prices(
    db: Session,
    post_dropout_df: pd.DataFrame,
    synthetic_prices_df: pd.DataFrame,
) -> dict[str, int]:
    """Persist generated demand history and synthetic benchmark prices to SQLite.

    CRITICAL RULE (Mandatory Correction 2):
    Never delete or overwrite real AGMARKNET_SNAPSHOT records.
    Only rows where is_synthetic == True and source == 'SYNTHETIC_DEMO' are cleared.
    """
    # 1. Clear existing synthetic demand history
    db.query(DemandHistory).filter(DemandHistory.is_synthetic.is_(True)).delete(
        synchronize_session=False
    )

    # 2. Clear ONLY synthetic market prices (PROTECT real AGMARKNET_SNAPSHOT records)
    db.query(MarketPrice).filter(
        MarketPrice.is_synthetic.is_(True),
        MarketPrice.source == "SYNTHETIC_DEMO",
    ).delete(synchronize_session=False)
    db.commit()

    # 3. Bulk insert DemandHistory
    demand_objects = [
        DemandHistory(
            hub_id=int(row["hub_id"]),
            crop_id=int(row["crop_id"]),
            date=row["date"],
            demand_kg=float(row["demand_kg"]),
            avg_price_per_kg=float(row["avg_price_per_kg"]),
            is_synthetic=True,
            generator_version="1.0",
        )
        for _, row in post_dropout_df.iterrows()
    ]
    db.bulk_save_objects(demand_objects)

    # 4. Bulk insert synthetic MarketPrice
    price_objects = [
        MarketPrice(
            hub_id=int(row["hub_id"]),
            crop_id=int(row["crop_id"]),
            market_name=str(row["market_name"]),
            price_date=row["price_date"],
            min_price_per_kg=float(row["min_price_per_kg"]),
            modal_price_per_kg=float(row["modal_price_per_kg"]),
            max_price_per_kg=float(row["max_price_per_kg"]),
            source="SYNTHETIC_DEMO",
            is_synthetic=True,
        )
        for _, row in synthetic_prices_df.iterrows()
    ]
    db.bulk_save_objects(price_objects)
    db.commit()

    return {
        "demand_history_seeded": len(demand_objects),
        "synthetic_prices_seeded": len(price_objects),
    }


def main():
    parser = argparse.ArgumentParser(description="FasalSetu Synthetic Data Generator")
    parser.add_argument("--config", type=str, default=None, help="Path to generator.yaml")
    parser.add_argument("--seed", type=int, default=None, help="Random seed override")
    parser.add_argument("--end-date", type=str, default=None, help="End date YYYY-MM-DD")
    parser.add_argument(
        "--to-db", action="store_true", help="Persist datasets to database as well as CSV"
    )
    args = parser.parse_args()

    config = load_generator_config(args.config)
    end_d = date.fromisoformat(args.end_date) if args.end_date else None

    print("Generating complete panel and post-dropout dataset...")
    complete_df, post_drop_df, prices_df = generate_panels(
        config=config, end_date=end_d, seed=args.seed
    )

    print(f"Pre-dropout rows:  {len(complete_df)} (5 hubs × 5 crops × 730 days)")
    print(f"Post-dropout rows: {len(post_drop_df)} (~1% dropout)")
    print(f"Synthetic prices:  {len(prices_df)} (last 90 days)")

    demand_csv, meta_path, _ = save_datasets(post_drop_df, complete_df, prices_df, config=config)
    print(f"Saved datasets to {demand_csv.parent}")

    if args.to_db:
        print("Persisting to database...")
        db = SessionLocal()
        try:
            counts = seed_demand_and_prices(db, post_drop_df, prices_df)
            print(f"Database seeded: {counts}")
        finally:
            db.close()


if __name__ == "__main__":
    main()
