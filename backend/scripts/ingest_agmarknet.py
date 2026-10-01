"""Agmarknet Mandi Price Snapshot Ingestion (Data.md §5, Research.md §7).

Reads offline snapshot CSV, maps mandi -> demand hub, converts ₹/quintal -> ₹/kg,
aggregates across varieties, and populates `market_prices` with source='AGMARKNET_SNAPSHOT'.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.db.models import Crop, MarketPrice

logger = logging.getLogger(__name__)

DEFAULT_INPUT_CSV = Path(__file__).resolve().parent.parent / "data" / "raw" / "agmarknet_snapshot.csv"
DEFAULT_HUB_MAP = Path(__file__).resolve().parent.parent / "config" / "market_hub_map.csv"
DEFAULT_META_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "prices.meta.json"


def load_hub_mapping(map_path: Path | str | None = None) -> dict[str, int]:
    """Load mandi_name -> hub_id mapping."""
    path = Path(map_path) if map_path else DEFAULT_HUB_MAP
    if not path.exists():
        raise FileNotFoundError(f"Market-hub mapping not found at: {path}")

    df = pd.read_csv(path)
    mapping: dict[str, int] = {}
    for _, row in df.iterrows():
        mandi = str(row["mandi_name"]).strip().lower()
        mapping[mandi] = int(row["hub_id"])
    return mapping


def parse_arrival_date(val: Any) -> date | None:
    """Parse arrival date supporting DD/MM/YYYY or YYYY-MM-DD."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_and_clean_agmarknet(
    csv_path: Path | str,
    hub_mapping: dict[str, int],
    crop_mapping: dict[str, int],
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Read Agmarknet snapshot, filter, convert units (÷100), and aggregate.

    Returns:
        (aggregated_df, metrics_dict)
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Agmarknet snapshot not found at: {path}")

    raw_df = pd.read_csv(path)
    # Standardize column headers
    raw_df.columns = [col.strip().lower() for col in raw_df.columns]

    required_cols = {"market", "commodity", "arrival_date", "min_price", "max_price", "modal_price"}
    missing = required_cols - set(raw_df.columns)
    if missing:
        raise ValueError(f"Snapshot missing required columns: {missing}")

    initial_count = len(raw_df)

    # 1. Map mandi -> hub_id
    raw_df["market_clean"] = raw_df["market"].astype(str).str.strip().str.lower()
    raw_df["hub_id"] = raw_df["market_clean"].map(hub_mapping)
    valid_hub_df = raw_df[raw_df["hub_id"].notna()].copy()
    valid_hub_df["hub_id"] = valid_hub_df["hub_id"].astype(int)

    # 2. Map commodity -> crop_id
    valid_hub_df["commodity_clean"] = valid_hub_df["commodity"].astype(str).str.strip().str.lower()
    valid_hub_df["crop_id"] = valid_hub_df["commodity_clean"].map(crop_mapping)
    matched_df = valid_hub_df[valid_hub_df["crop_id"].notna()].copy()
    matched_df["crop_id"] = matched_df["crop_id"].astype(int)

    # 3. Parse date
    matched_df["price_date"] = matched_df["arrival_date"].apply(parse_arrival_date)
    valid_date_df = matched_df[matched_df["price_date"].notna()].copy()

    # 4. Convert prices ₹/quintal -> ₹/kg (÷100) per Assumption A-05
    for col in ("min_price", "modal_price", "max_price"):
        valid_date_df[col] = pd.to_numeric(valid_date_df[col], errors="coerce")

    clean_prices_df = valid_date_df[
        valid_date_df["modal_price"].notna()
        & (valid_date_df["modal_price"] > 0)
        & (valid_date_df["min_price"] > 0)
        & (valid_date_df["max_price"] >= valid_date_df["min_price"])
    ].copy()

    clean_prices_df["min_kg"] = (clean_prices_df["min_price"] / 100.0).round(2)
    clean_prices_df["modal_kg"] = (clean_prices_df["modal_price"] / 100.0).round(2)
    clean_prices_df["max_kg"] = (clean_prices_df["max_price"] / 100.0).round(2)

    # 5. Aggregate across varieties for (hub_id, crop_id, price_date)
    agg_df = (
        clean_prices_df.groupby(["hub_id", "crop_id", "price_date"], as_index=False)
        .agg(
            {
                "market": "first",
                "min_kg": "mean",
                "modal_kg": "mean",
                "max_kg": "mean",
            }
        )
    )

    agg_df["min_price_per_kg"] = agg_df["min_kg"].round(2)
    agg_df["modal_price_per_kg"] = agg_df["modal_kg"].round(2)
    agg_df["max_price_per_kg"] = agg_df["max_kg"].round(2)

    # Ensure min <= modal <= max
    agg_df["min_price_per_kg"] = agg_df[["min_price_per_kg", "modal_price_per_kg"]].min(axis=1)
    agg_df["max_price_per_kg"] = agg_df[["max_price_per_kg", "modal_price_per_kg"]].max(axis=1)

    agg_df["source"] = "AGMARKNET_SNAPSHOT"
    agg_df["is_synthetic"] = False
    agg_df["market_name"] = agg_df["market"]

    stats = {
        "raw_rows": initial_count,
        "valid_hub_rows": len(valid_hub_df),
        "matched_crop_rows": len(matched_df),
        "valid_price_rows": len(clean_prices_df),
        "aggregated_daily_rows": len(agg_df),
    }

    return agg_df, stats


def ingest_snapshot_to_db(
    db: Session,
    agg_df: pd.DataFrame,
) -> int:
    """Ingest aggregated real snapshot records into market_prices.

    CRITICAL RULE (Mandatory Correction 2):
    Never delete synthetic records during snapshot ingestion.
    Only existing AGMARKNET_SNAPSHOT records for the incoming dates are replaced.
    """
    if agg_df.empty:
        return 0

    incoming_dates = set(agg_df["price_date"].unique())

    # Delete only existing real AGMARKNET_SNAPSHOT rows for these dates to avoid duplicates
    db.query(MarketPrice).filter(
        MarketPrice.source == "AGMARKNET_SNAPSHOT",
        MarketPrice.is_synthetic.is_(False),
        MarketPrice.price_date.in_(incoming_dates),
    ).delete(synchronize_session=False)
    db.commit()

    records = [
        MarketPrice(
            hub_id=int(row["hub_id"]),
            crop_id=int(row["crop_id"]),
            market_name=str(row["market_name"]),
            price_date=row["price_date"],
            min_price_per_kg=float(row["min_price_per_kg"]),
            modal_price_per_kg=float(row["modal_price_per_kg"]),
            max_price_per_kg=float(row["max_price_per_kg"]),
            source="AGMARKNET_SNAPSHOT",
            is_synthetic=False,
        )
        for _, row in agg_df.iterrows()
    ]

    db.bulk_save_objects(records)
    db.commit()
    return len(records)


def write_prices_metadata(
    agg_df: pd.DataFrame,
    stats: dict[str, int],
    meta_path: Path | None = None,
) -> None:
    """Write or update prices.meta.json with snapshot provenance."""
    out_path = meta_path or DEFAULT_META_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "dataset_id": "DS-02/DS-03",
        "data_source": "AGMARKNET_SNAPSHOT",
        "is_synthetic": False,
        "ingested_at": datetime.now(UTC).isoformat(),
        "source_reference": "Agmarknet / data.gov.in Current Daily Mandi Prices",
        "unit_conversion": "Converted from Rs/quintal to Rs/kg (divided by 100.0 per Assumption A-05)",
        "total_records_ingested": len(agg_df),
        "date_range": {
            "start": str(agg_df["price_date"].min()) if not agg_df.empty else None,
            "end": str(agg_df["price_date"].max()) if not agg_df.empty else None,
        },
        "stats": stats,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Ingest Agmarknet Mandi Snapshot")
    parser.add_argument("--input", type=str, default=None, help="Path to raw Agmarknet CSV")
    parser.add_argument("--hub-map", type=str, default=None, help="Path to market_hub_map.csv")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else DEFAULT_INPUT_CSV
    if not input_path.exists():
        print(f"No Agmarknet snapshot found at: {input_path}")
        return

    db = SessionLocal()
    try:
        # Load active crops from DB to build commodity name -> crop_id map
        crops = db.query(Crop).all()
        crop_mapping = {c.agmarknet_commodity_name.strip().lower(): c.id for c in crops}
        hub_mapping = load_hub_mapping(args.hub_map)

        print(f"Reading and cleaning snapshot from {input_path}...")
        agg_df, stats = parse_and_clean_agmarknet(input_path, hub_mapping, crop_mapping)
        print(f"Stats: {stats}")

        print("Ingesting records into database (source='AGMARKNET_SNAPSHOT')...")
        inserted = ingest_snapshot_to_db(db, agg_df)
        print(f"Successfully inserted {inserted} real Agmarknet price records.")

        write_prices_metadata(agg_df, stats)
        print(f"Updated metadata at {DEFAULT_META_PATH}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
