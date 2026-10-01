from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.db.models import MarketPrice
from app.db.seed import seed_reference_and_users, seed_synthetic_demand_and_prices
from scripts.ingest_agmarknet import (
    parse_and_clean_agmarknet,
)

SAMPLE_CSV = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "sample_agmarknet_snapshot.csv"


def test_agmarknet_parsing_and_unit_conversion():
    """Verify Agmarknet snapshot parser, unit conversion (÷100), and commodity filtering."""
    hub_mapping = {"azadpur": 1, "gurgaon": 2, "noida": 3, "sahibabad": 4, "faridabad": 5}
    crop_mapping = {
        "tomato": 1,
        "onion": 2,
        "potato": 3,
        "cauliflower": 4,
        "green chilli": 5,
    }

    agg_df, stats = parse_and_clean_agmarknet(SAMPLE_CSV, hub_mapping, crop_mapping)

    # 1. Total raw rows = 11; unmapped commodity (Wheat) and invalid price (-500) dropped
    assert stats["raw_rows"] == 11
    assert stats["matched_crop_rows"] == 10  # Wheat dropped
    assert stats["valid_price_rows"] == 9   # -500 price row dropped
    assert stats["aggregated_daily_rows"] == 8  # 2 varieties of Tomato on 2026-09-25 merged into 1

    # 2. Check multi-variety aggregation for Tomato in Azadpur on 2026-09-25:
    # Hybrid: min=2200, max=2800, modal=2500 -> 22.0, 28.0, 25.0
    # Deshi: min=2000, max=2600, modal=2300 -> 20.0, 26.0, 23.0
    # Mean: min=21.0, max=27.0, modal=24.0
    tomato_row = agg_df[
        (agg_df["hub_id"] == 1)
        & (agg_df["crop_id"] == 1)
        & (agg_df["price_date"] == date(2026, 9, 25))
    ].iloc[0]

    assert tomato_row["modal_price_per_kg"] == 24.00
    assert tomato_row["min_price_per_kg"] == 21.00
    assert tomato_row["max_price_per_kg"] == 27.00
    assert tomato_row["source"] == "AGMARKNET_SNAPSHOT"
    assert bool(tomato_row["is_synthetic"]) is False


def test_synthetic_reseeding_preserves_real_agmarknet_records():
    """CRITICAL TEST (Mandatory Correction 2 & 6):

    1. Seed synthetic prices
    2. Insert an AGMARKNET_SNAPSHOT row (is_synthetic=False)
    3. Re-run synthetic regeneration
    4. Assert real AGMARKNET_SNAPSHOT row remains unchanged!
    """
    db: Session = SessionLocal()
    try:
        # Step 1: Seed base reference entities and initial synthetic data
        seed_reference_and_users(db)
        seed_synthetic_demand_and_prices(db, seed=42)

        # Count synthetic prices
        synthetic_count_before = db.query(MarketPrice).filter(
            MarketPrice.source == "SYNTHETIC_DEMO"
        ).count()
        assert synthetic_count_before > 0

        # Step 2: Insert a REAL Agmarknet snapshot row
        test_real_date = date(2026, 9, 20)
        # Clear any preexisting test row for this specific date
        db.query(MarketPrice).filter(
            MarketPrice.source == "AGMARKNET_SNAPSHOT",
            MarketPrice.hub_id == 1,
            MarketPrice.crop_id == 1,
            MarketPrice.price_date == test_real_date,
        ).delete()
        db.commit()

        real_record = MarketPrice(
            hub_id=1,
            crop_id=1,
            market_name="Azadpur Mandi (Real Government Snapshot)",
            price_date=test_real_date,
            min_price_per_kg=22.50,
            modal_price_per_kg=25.00,
            max_price_per_kg=28.00,
            source="AGMARKNET_SNAPSHOT",
            is_synthetic=False,
        )
        db.add(real_record)
        db.commit()
        real_id = real_record.id

        # Verify real record exists in DB
        persisted_real = db.query(MarketPrice).filter(MarketPrice.id == real_id).first()
        assert persisted_real is not None
        assert persisted_real.is_synthetic is False
        assert persisted_real.source == "AGMARKNET_SNAPSHOT"
        assert float(persisted_real.modal_price_per_kg) == 25.00

        # Step 3: Run synthetic regeneration / reseeding
        seed_synthetic_demand_and_prices(db, seed=123)

        # Step 4: Verify the real AGMARKNET_SNAPSHOT record still exists unchanged!
        verified_real = db.query(MarketPrice).filter(MarketPrice.id == real_id).first()
        assert verified_real is not None, "Real AGMARKNET_SNAPSHOT record was deleted by synthetic reseeding!"
        assert verified_real.source == "AGMARKNET_SNAPSHOT"
        assert verified_real.is_synthetic is False
        assert float(verified_real.modal_price_per_kg) == 25.00
        assert float(verified_real.min_price_per_kg) == 22.50
        assert float(verified_real.max_price_per_kg) == 28.00
        assert verified_real.price_date == test_real_date

    finally:
        db.close()
