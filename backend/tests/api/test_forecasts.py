from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.db.models import Listing
from app.main import create_app
from ml.predict import predict_demand


@pytest.fixture(scope="module")
def client():
    app = create_app()
    return TestClient(app)


def test_health_shows_model_loaded(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"]["loaded"] is True
    assert data["model"]["deployed_method"] == "LIGHTGBM"


def test_get_forecast_demand_success(client: TestClient):
    response = client.get("/api/v1/forecasts/demand?hub_id=1&crop_id=1&horizon_days=7")
    assert response.status_code == 200
    data = response.json()

    assert data["hub_id"] == 1
    assert data["hub_name"] == "Delhi North"
    assert data["crop_id"] == 1
    assert data["crop_name"] == "Tomato"
    assert data["horizon_days"] == 7
    assert data["method"] == "LIGHTGBM"
    assert data["model_version"] == "1.0.0"
    assert data["demand_data_source"] == "SYNTHETIC"
    assert "SYNTHETIC_DEMO" in data["price_feature_sources"]
    assert "AGMARKNET_SNAPSHOT" in data["price_feature_sources"]
    assert "Demand history is synthetic" in data["disclaimer"]

    # History verification (up to 28 days with ~1% dropout)
    assert 25 <= len(data["history"]) <= 28
    for h in data["history"]:
        assert "date" in h
        assert h["demand_kg"] > 0
        assert h["is_synthetic"] is True

    # Forecast verification (7 days)
    assert len(data["forecast"]) == 7
    for item in data["forecast"]:
        assert "date" in item
        assert "day_of_week" in item
        point = item["point_forecast_kg"]
        lo = item["interval_lo_kg"]
        hi = item["interval_hi_kg"]
        assert point > 0
        assert lo is not None and lo >= 0
        assert hi is not None and hi >= point
        assert lo <= point <= hi, f"Monotonicity violated: {lo} <= {point} <= {hi}"


def test_get_forecast_demand_caching(client: TestClient):
    # First call
    res1 = client.get("/api/v1/forecasts/demand?hub_id=2&crop_id=2&horizon_days=5")
    assert res1.status_code == 200
    # Second call (hits cache)
    res2 = client.get("/api/v1/forecasts/demand?hub_id=2&crop_id=2&horizon_days=5")
    assert res2.status_code == 200
    assert res1.json() == res2.json()


def test_get_forecast_demand_validation_errors(client: TestClient):
    # Invalid horizon
    res = client.get("/api/v1/forecasts/demand?hub_id=1&crop_id=1&horizon_days=0")
    assert res.status_code in [400, 422]

    res = client.get("/api/v1/forecasts/demand?hub_id=1&crop_id=1&horizon_days=8")
    assert res.status_code in [400, 422]

    # Non-existent Hub
    res = client.get("/api/v1/forecasts/demand?hub_id=9999&crop_id=1&horizon_days=7")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "HUB_NOT_FOUND"

    # Non-existent Crop
    res = client.get("/api/v1/forecasts/demand?hub_id=1&crop_id=9999&horizon_days=7")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "CROP_NOT_FOUND"


def test_get_forecast_hubs_comparison_and_rule_d026_supply_attribution(client: TestClient):
    response = client.get("/api/v1/forecasts/hubs?crop_id=1&horizon_days=7")
    assert response.status_code == 200
    data = response.json()

    assert data["crop_id"] == 1
    assert data["crop_name"] == "Tomato"
    assert data["horizon_days"] == 7
    assert data["demand_data_source"] == "SYNTHETIC"
    assert len(data["hubs"]) == 5

    # Verify Rule D-026: Total active supply across hubs matches active listings for Tomato
    db = SessionLocal()
    try:
        from app.core.dates import today_ist
        active_listings = (
            db.query(Listing)
            .filter(
                Listing.crop_id == 1,
                Listing.status == "ACTIVE",
                Listing.available_until >= today_ist(),
                Listing.quantity_available_kg > 0,
            )
            .all()
        )
        expected_total_supply = sum(
            float(listing.quantity_available_kg) for listing in active_listings
        )
        actual_total_supply = sum(float(h["active_supply_kg"]) for h in data["hubs"])

        assert round(actual_total_supply, 1) == round(expected_total_supply, 1), (
            f"Supply mismatch: Hubs total {actual_total_supply} != active listings {expected_total_supply}"
        )
    finally:
        db.close()

    # Verify opportunity ranking
    ratios = [h["supply_demand_ratio"] for h in data["hubs"]]
    assert ratios == sorted(ratios), "Hubs should be sorted by supply-demand ratio ascending"

    for h in data["hubs"]:
        assert h["opportunity_label"] in ["HIGH_DEFICIT", "BALANCED", "OVERSUPPLIED"]
        assert h["total_forecast_kg"] > 0
        assert h["avg_daily_forecast_kg"] > 0


def test_get_model_info(client: TestClient):
    response = client.get("/api/v1/forecasts/model-info")
    assert response.status_code == 200
    data = response.json()

    assert data["model_id"] == "MOD-01"
    assert data["model_version"] == "1.0.0"
    assert data["deployed_method"] == "LIGHTGBM"
    assert data["demand_data_source"] == "SYNTHETIC"
    assert data["deployment_gate"]["passed"] is True
    assert "metrics" in data
    assert "validation" in data["metrics"]
    assert "test" in data["metrics"]
    assert data["metrics"]["test"]["lgbm"]["mae"] < data["metrics"]["test"]["b1_seasonal_naive"]["mae"]
    assert "Demand history is synthetic" in data["disclaimer"]


def test_seasonal_naive_fallback_when_history_short():
    db = SessionLocal()
    try:
        # Pick an arbitrary date from the very beginning of the dataset where only ~20 days exist
        # Min date is 2024-10-01. Cutoff 2024-10-22 gives 22 days of history (< 35 required for LGBM)
        early_cutoff = date(2024, 10, 22)
        res = predict_demand(db, hub_id=1, crop_id=1, horizon_days=5, cutoff_date=early_cutoff)
        assert res["method"] == "SEASONAL_NAIVE_FALLBACK"
        assert len(res["forecast"]) == 5
        for item in res["forecast"]:
            assert item["point_forecast_kg"] > 0
            assert item["interval_lo_kg"] is None
            assert item["interval_hi_kg"] is None
    finally:
        db.close()
