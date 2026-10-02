from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_token(persona: str) -> str:
    res = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_order_price_breakdown_ac_prc_01_and_02():
    """Verify GET /api/v1/pricing/breakdown for seeded order O5:

    - landed = farmgate + transport + platform_fee (AC-PRC-01)
    - benchmark includes source, is_synthetic, basis="MODELLED_SCENARIO" (AC-PRC-02)
    - totals reconcile with quantity_kg
    """
    token = get_token("buyer_noida")  # Buyer B2 owns Order 5 (400 kg Cauliflower @ 28.50)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/pricing/breakdown?order_id=5", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["order_id"] == 5
    assert data["quantity_kg"] == 400.0

    # AC-PRC-01: per_kg waterfall arithmetic
    per_kg = data["per_kg"]
    assert per_kg["farmgate"] == 28.50
    assert per_kg["platform_fee"] == round(per_kg["farmgate"] * 0.02, 2)
    assert abs(per_kg["landed"] - (per_kg["farmgate"] + per_kg["transport"] + per_kg["platform_fee"])) <= 0.01

    # Totals reconciliation
    totals = data["totals"]
    qty = data["quantity_kg"]
    assert abs(totals["farmgate_total"] - round(per_kg["farmgate"] * qty, 2)) <= 0.01
    assert abs(totals["transport_total"] - round(per_kg["transport"] * qty, 2)) <= 0.01
    assert abs(totals["platform_fee_total"] - round(per_kg["platform_fee"] * qty, 2)) <= 0.01
    assert abs(totals["landed_total"] - round(per_kg["landed"] * qty, 2)) <= 0.01

    # Transport basis
    assert data["transport_basis"] in ["ESTIMATE", "ALLOCATED_ROUTE"]

    # AC-PRC-02: Provenance & Scenario disclosure
    assert data["basis"] == "MODELLED_SCENARIO"
    assert "disclaimer" in data

    assert data["benchmark"] is not None
    bm = data["benchmark"]
    assert "source" in bm
    assert "is_synthetic" in bm
    assert bm["source"] in ["AGMARKNET_SNAPSHOT", "SYNTHETIC_DEMO"]
    assert isinstance(bm["is_synthetic"], bool)

    # Traditional Scenario
    assert data["scenario"] is not None
    sc = data["scenario"]
    assert "farmer_mandi_net_per_kg" in sc
    assert "buyer_traditional_per_kg" in sc
    assert "delta_farmer_pct" in sc
    assert "delta_buyer_pct" in sc
    assert sc["assumptions"]["commission_agent_pct"] == 5.0

    # Fair band
    if data["fair_band"] is not None:
        assert data["fair_band"]["high"] > data["fair_band"]["low"]


def test_order_price_breakdown_auth():
    """Verify unauthorized user cannot access another party's order breakdown."""
    # Order 5 is between P1 (fpo_sonipat) and B2 (buyer_noida).
    # buyer_gurugram (B1) should receive 403.
    b1_token = get_token("buyer_gurugram")
    res = client.get("/api/v1/pricing/breakdown?order_id=5", headers={"Authorization": f"Bearer {b1_token}"})
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

    # Operator (ADMIN) is allowed
    op_token = get_token("operator")
    res_op = client.get("/api/v1/pricing/breakdown?order_id=5", headers={"Authorization": f"Bearer {op_token}"})
    assert res_op.status_code == 200


def test_pricing_benchmark_endpoint_ac_prc_02():
    """Verify GET /api/v1/pricing/benchmark by hub_id and by coordinates."""
    token = get_token("fpo_sonipat")
    headers = {"Authorization": f"Bearer {token}"}

    # By hub_id
    res = client.get("/api/v1/pricing/benchmark?crop_id=1&hub_id=1", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["hub"]["id"] == 1
    assert data["basis"] == "MODELLED_SCENARIO"
    assert "disclaimer" in data
    assert "trend" in data
    assert isinstance(data["trend"], list)

    if data["benchmark"]:
        assert data["benchmark"]["source"] in ["AGMARKNET_SNAPSHOT", "SYNTHETIC_DEMO"]
        assert isinstance(data["benchmark"]["is_synthetic"], bool)

    # By lat, lng (near Sonipat / Delhi)
    res_geo = client.get("/api/v1/pricing/benchmark?crop_id=1&lat=28.98&lng=77.03", headers=headers)
    assert res_geo.status_code == 200
    geo_data = res_geo.json()
    assert geo_data["hub"]["id"] in [1, 2, 3, 4, 5]


def test_pricing_benchmark_validation_errors():
    """Verify 404 on invalid crop/hub, and 422 if neither hub_id nor coordinates provided."""
    token = get_token("fpo_sonipat")
    headers = {"Authorization": f"Bearer {token}"}

    # Missing hub_id and coords -> 422
    res_missing = client.get("/api/v1/pricing/benchmark?crop_id=1", headers=headers)
    assert res_missing.status_code == 422

    # Invalid crop -> 404
    res_crop = client.get("/api/v1/pricing/benchmark?crop_id=999&hub_id=1", headers=headers)
    assert res_crop.status_code == 404

    # Invalid hub -> 404
    res_hub = client.get("/api/v1/pricing/benchmark?crop_id=1&hub_id=999", headers=headers)
    assert res_hub.status_code == 404


def test_pricing_missing_benchmark_ac_prc_04():
    """Verify AC-PRC-04: Missing benchmark -> benchmark:null, scenario:null, HTTP 200 (not an error)."""
    # Create order with no benchmark (or delete benchmark prices for a test crop/hub)
    from app.core.database import SessionLocal
    from app.db.models import Crop, Order, OrderEvent
    db = SessionLocal()
    try:
        # Create temp crop 99 with no prices
        c_temp = Crop(
            id=99,
            name="Exotic Herb",
            category="HERB",
            agmarknet_commodity_name="Exotic Herb",
            shelf_life_days=5,
            max_transit_hours=12,
            perishability="HIGH",
        )
        db.add(c_temp)
        db.commit()

        from datetime import date
        o_temp = Order(
            id=999,
            listing_id=1,
            buyer_id=2,  # buyer_noida
            producer_id=1,  # fpo_sonipat
            crop_id=99,
            quantity_kg=100.0,
            agreed_price_per_kg=50.00,
            transport_cost_estimate_per_kg=5.00,
            platform_fee_per_kg=1.00,
            delivery_date=date(2026, 10, 10),
            status="CONFIRMED",
            origin="MARKETPLACE",
            is_demo=True,
        )
        db.add(o_temp)
        db.commit()

        token = get_token("buyer_noida")
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/v1/pricing/breakdown?order_id=999", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["benchmark"] is None
        assert data["scenario"] is None
        assert data["fair_band"] is None
        assert data["per_kg"]["landed"] == 56.00

        # Benchmark endpoint with no prices returns HTTP 200 with benchmark: null
        res_bm = client.get("/api/v1/pricing/benchmark?crop_id=99&hub_id=1", headers=headers)
        assert res_bm.status_code == 200
        bm_data = res_bm.json()
        assert bm_data["benchmark"] is None
        assert bm_data["fair_band"] is None
    finally:
        db.query(OrderEvent).filter(OrderEvent.order_id == 999).delete()
        db.query(Order).filter(Order.id == 999).delete()
        db.query(Crop).filter(Crop.id == 99).delete()
        db.commit()
        db.close()

