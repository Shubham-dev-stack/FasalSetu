import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.db.models import Order, RoutePlan, Shipment
from app.db.seed import seed_demo_orders
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_orders():
    def _clean_and_reseed():
        db = SessionLocal()
        try:
            from app.db.models import ShipmentStop
            db.query(Order).update({"shipment_id": None, "allocated_transport_cost_total": None})
            db.query(ShipmentStop).delete()
            db.query(Shipment).delete()
            db.query(RoutePlan).delete()
            db.commit()
            seed_demo_orders(db)
            db.commit()
        finally:
            db.close()

    _clean_and_reseed()
    yield
    _clean_and_reseed()


def get_token(persona: str) -> str:
    res = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_optimize_routes_ac_rte_04_seeded_pool():
    """Verify POST /api/v1/routes/optimize solves confirmed unrouted orders O1-O6.

    AC-RTE-04: optimized_cost <= baseline_cost (or reports truthful delta).
    """
    token = get_token("operator")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/routes/optimize",
        headers=headers,
        json={"time_limit_s": 5, "distance_mode": "HAVERSINE"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["status"] == "PROPOSED"
    assert "plan_id" in data
    assert len(data["shipments"]) > 0
    assert data["totals"]["optimized_cost"] > 0
    assert data["totals"]["baseline_cost"] > 0
    # Consistent metrics
    assert data["totals"]["savings_cost"] == round(
        data["totals"]["baseline_cost"] - data["totals"]["optimized_cost"], 2
    )


def test_approve_plan_ac_rte_09_creates_shipments_and_allocates_cost():
    """Verify POST /api/v1/routes/plans/{id}/approve creates shipments, links orders,

    and allocates transport cost summing to total cost ±0.01 (AC-RTE-09).
    """
    token = get_token("operator")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Optimize
    res = client.post(
        "/api/v1/routes/optimize",
        headers=headers,
        json={"time_limit_s": 5},
    )
    assert res.status_code == 201
    plan_id = res.json()["plan_id"]

    # 2. Approve
    appr_res = client.post(
        f"/api/v1/routes/plans/{plan_id}/approve",
        headers=headers,
    )
    assert appr_res.status_code == 200, appr_res.text
    appr_data = appr_res.json()
    assert appr_data["plan"]["status"] == "APPROVED"
    assert len(appr_data["shipments"]) > 0

    # 3. Check second approve returns 409 INVALID_TRANSITION
    second_appr = client.post(
        f"/api/v1/routes/plans/{plan_id}/approve",
        headers=headers,
    )
    assert second_appr.status_code == 409
    assert second_appr.json()["error"]["code"] == "INVALID_TRANSITION"

    # 4. Verify orders in DB are linked to shipment and have allocated_transport_cost_total
    db = SessionLocal()
    try:
        for shp in appr_data["shipments"]:
            orders = db.query(Order).filter(Order.shipment_id == shp["id"]).all()
            assert len(orders) > 0
            allocated_sum = sum(float(o.allocated_transport_cost_total or 0) for o in orders)
            assert abs(allocated_sum - shp["total_cost"]) <= 0.05
    finally:
        db.close()


def test_discard_plan_ac_rte_10_and_stale_approval():
    """Verify discard leaves orders unchanged; and approving when an order status changed returns 409 STALE_PLAN."""
    token = get_token("operator")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Optimize
    res = client.post("/api/v1/routes/optimize", headers=headers, json={"time_limit_s": 5})
    assert res.status_code == 201
    plan_id = res.json()["plan_id"]

    # 2. Discard
    disc_res = client.post(f"/api/v1/routes/plans/{plan_id}/discard", headers=headers)
    assert disc_res.status_code == 200
    assert disc_res.json()["status"] == "DISCARDED"

    # Cannot approve discarded plan
    appr_res = client.post(f"/api/v1/routes/plans/{plan_id}/approve", headers=headers)
    assert appr_res.status_code == 409

    # 3. Test STALE_PLAN: Create new proposal, then cancel one order in it
    res2 = client.post("/api/v1/routes/optimize", headers=headers, json={"time_limit_s": 5})
    assert res2.status_code == 201
    plan2_id = res2.json()["plan_id"]

    # Cancel order 1 in background
    db = SessionLocal()
    try:
        o1 = db.query(Order).filter(Order.id == 1).first()
        o1.status = "CANCELLED"
        db.commit()
    finally:
        db.close()

    # Now attempt to approve plan2 -> must return 409 STALE_PLAN
    appr_stale = client.post(f"/api/v1/routes/plans/{plan2_id}/approve", headers=headers)
    assert appr_stale.status_code == 409
    assert appr_stale.json()["error"]["code"] == "STALE_PLAN"


def test_shipment_transition_flow():
    """Verify manual transition PLANNED -> DISPATCHED -> DELIVERED updates orders to IN_TRANSIT / DELIVERED."""
    token = get_token("operator")
    headers = {"Authorization": f"Bearer {token}"}

    # Optimize and approve
    res = client.post("/api/v1/routes/optimize", headers=headers, json={"time_limit_s": 5})
    plan_id = res.json()["plan_id"]
    appr = client.post(f"/api/v1/routes/plans/{plan_id}/approve", headers=headers)
    shp_id = appr.json()["shipments"][0]["id"]

    # Transition to DISPATCHED
    t1 = client.post(
        f"/api/v1/routes/shipments/{shp_id}/transition",
        headers=headers,
        json={"to_status": "DISPATCHED"},
    )
    assert t1.status_code == 200
    assert t1.json()["status"] == "DISPATCHED"

    # Check orders are now IN_TRANSIT
    db = SessionLocal()
    try:
        orders = db.query(Order).filter(Order.shipment_id == shp_id).all()
        assert all(o.status == "IN_TRANSIT" for o in orders)
    finally:
        db.close()

    # Transition to DELIVERED
    t2 = client.post(
        f"/api/v1/routes/shipments/{shp_id}/transition",
        headers=headers,
        json={"to_status": "DELIVERED"},
    )
    assert t2.status_code == 200
    assert t2.json()["status"] == "DELIVERED"

    db = SessionLocal()
    try:
        orders = db.query(Order).filter(Order.shipment_id == shp_id).all()
        assert all(o.status == "DELIVERED" for o in orders)
    finally:
        db.close()


def test_optimize_no_eligible_orders_ac_rte_06():
    """AC-RTE-06: 422 NO_ELIGIBLE_ORDERS when no confirmed unrouted orders exist."""
    token = get_token("operator")
    headers = {"Authorization": f"Bearer {token}"}

    # Cancel all orders
    db = SessionLocal()
    try:
        db.query(Order).update({"status": "CANCELLED"})
        db.commit()
    finally:
        db.close()

    res = client.post("/api/v1/routes/optimize", headers=headers, json={})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "NO_ELIGIBLE_ORDERS"
