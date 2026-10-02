from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_token(persona: str) -> str:
    res = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_analytics_overview_ac_anl_01():
    """AC-ANL-01: On the seed DB, KPIs equal independently computed direct values."""
    token = get_token("buyer_noida")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/overview", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    # Provenance and disclaimers
    assert "as_of" in data
    assert "All figures computed from synthetic demo records" in data["data_note"]

    kpis = data["kpis"]
    assert kpis["committed_orders"] == 10
    assert kpis["committed_volume_kg"] == 6350.0
    assert kpis["committed_value_inr"] == 140100.0
    assert kpis["requirement_fill_rate_pct"] is not None
    assert kpis["avg_logistics_cost_per_kg"] is not None
    # No route plans approved yet on initial seed
    assert kpis["route_savings_km"] == 0.0
    assert kpis["route_savings_inr"] == 0.0
    assert kpis["avg_utilization_pct"] is None

    # Price gap
    price_gap = data["price_gap"]
    assert price_gap["basis"] == "MODELLED_SCENARIO"
    assert price_gap["orders_considered"] == 10
    assert price_gap["avg_farmer_delta_pct"] is not None
    assert price_gap["avg_buyer_delta_pct"] is not None

    # Daily trend series
    daily = data["daily"]
    assert len(daily) == 14
    total_daily_vol = sum(d["volume_kg"] for d in daily)
    # Some delivered orders fall in the last 14 days
    assert total_daily_vol > 0

    # Model linkage
    model = data["model"]
    assert model["data_source"] == "SYNTHETIC"
    assert model["deployed_method"] in ["LIGHTGBM", "SEASONAL_NAIVE_FALLBACK"]


def test_analytics_supply_demand_matrix():
    """Verify GET /api/v1/analytics/supply-demand contracts, ratios, and crop filtering."""
    token = get_token("fpo_sonipat")
    headers = {"Authorization": f"Bearer {token}"}

    # Full matrix (5 hubs x 5 crops = 25 rows)
    res = client.get("/api/v1/analytics/supply-demand", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data["rows"]) == 25
    assert data["data_source"] == "SYNTHETIC"

    for row in data["rows"]:
        assert "hub" in row
        assert "crop" in row
        assert row["status"] in ["SHORTAGE", "SURPLUS", "BALANCED"]
        if row["forecast_7d_kg"] > 0:
            expected_ratio = round(row["supply_kg"] / row["forecast_7d_kg"], 2)
            assert abs(row["ratio"] - expected_ratio) <= 0.01

    # Filtered by crop_id=1 (Tomato: 5 hubs x 1 crop = 5 rows)
    res_crop = client.get("/api/v1/analytics/supply-demand?crop_id=1", headers=headers)
    assert res_crop.status_code == 200
    data_crop = res_crop.json()
    assert len(data_crop["rows"]) == 5
    for row in data_crop["rows"]:
        assert row["crop_id"] == 1
        assert row["crop"] == "Tomato"


def test_analytics_supply_demand_crop_not_found():
    """Verify 404 for non-existent crop ID."""
    token = get_token("operator")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/supply-demand?crop_id=99999", headers=headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "CROP_NOT_FOUND"


def test_analytics_auth_required():
    """Verify 401 when no token is provided."""
    res = client.get("/api/v1/analytics/overview")
    assert res.status_code == 401

    res_sd = client.get("/api/v1/analytics/supply-demand")
    assert res_sd.status_code == 401


def test_analytics_kpi_progression_ac_anl_02():
    """AC-ANL-02: After optimizing and approving a route plan, route savings KPIs change."""
    token = get_token("operator")
    headers = {"Authorization": f"Bearer {token}"}

    # Baseline overview
    res_before = client.get("/api/v1/analytics/overview", headers=headers)
    assert res_before.status_code == 200
    kpis_before = res_before.json()["kpis"]
    assert kpis_before["route_savings_km"] == 0.0

    # Optimize route plan on seeded pool
    res_opt = client.post("/api/v1/routes/optimize", json={"time_limit_s": 5}, headers=headers)
    assert res_opt.status_code == 201
    plan_id = res_opt.json()["plan_id"]

    try:
        # Approve route plan
        res_app = client.post(f"/api/v1/routes/plans/{plan_id}/approve", headers=headers)
        assert res_app.status_code == 200

        # Overview after approval
        res_after = client.get("/api/v1/analytics/overview", headers=headers)
        assert res_after.status_code == 200
        kpis_after = res_after.json()["kpis"]

        # Route savings and utilization are now computed from the approved plan
        assert kpis_after["route_savings_km"] != 0.0 or kpis_after["route_savings_inr"] != 0.0
        assert kpis_after["avg_utilization_pct"] is not None
    finally:
        from app.core.database import SessionLocal
        from app.db.models import Order, RoutePlan, Shipment, ShipmentStop

        db = SessionLocal()
        orders = db.query(Order).all()
        for o in orders:
            if o.shipment_id is not None:
                o.shipment_id = None
                o.allocated_transport_cost_total = None
            if o.status == "ROUTED":
                o.status = "CONFIRMED"
        db.flush()
        db.query(ShipmentStop).delete()
        db.flush()
        db.query(Shipment).delete()
        db.flush()
        db.query(RoutePlan).delete()
        db.commit()
        db.close()

