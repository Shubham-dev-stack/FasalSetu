from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.core.dates import today_ist
from app.db.models import Crop, Listing, ProducerProfile, User
from app.db.seed import seed_reference_and_users


def test_ist_date_is_valid():
    d = today_ist()
    assert d is not None
    assert d.year >= 2026


def test_database_check_constraints_reject_invalid_listing():
    # AC-DATA-04
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.role == "PRODUCER").first()
        prod = (
            db.query(ProducerProfile).filter(ProducerProfile.user_id == user.id).first()
        )
        crop = db.query(Crop).first()
        today = today_ist()

        # Negative quantity
        bad_listing_1 = Listing(
            producer_id=prod.id,
            crop_id=crop.id,
            grade="A",
            quantity_kg=-50.0,
            quantity_available_kg=-50.0,
            ask_price_per_kg=20.0,
            min_order_kg=10.0,
            harvest_date=today,
            available_from=today,
            available_until=today + timedelta(days=2),
        )
        db.add(bad_listing_1)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        # Inverted dates (until < from)
        bad_listing_2 = Listing(
            producer_id=prod.id,
            crop_id=crop.id,
            grade="A",
            quantity_kg=100.0,
            quantity_available_kg=100.0,
            ask_price_per_kg=20.0,
            min_order_kg=10.0,
            harvest_date=today,
            available_from=today + timedelta(days=5),
            available_until=today,
        )
        db.add(bad_listing_2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.close()


def test_seed_determinism_and_flags():
    # AC-DATA-01 and AC-DATA-03
    db = SessionLocal()
    try:
        counts = seed_reference_and_users(db)
        assert counts["crops"] == 5
        assert counts["hubs"] == 5
        assert counts["producers"] == 6
        assert counts["buyers"] == 5
        assert counts["vehicles"] == 5

        # Verify demo flags
        demo_users = db.query(User).filter(User.is_demo.is_(True)).all()
        assert len(demo_users) == 12
    finally:
        db.close()
