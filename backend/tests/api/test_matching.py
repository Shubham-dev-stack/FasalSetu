from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.dates import today_ist
from app.db.models import Listing, Order, Requirement
from app.db.seed import seed_demo_orders, seed_demo_requirements
from app.main import create_app


@pytest.fixture(autouse=True)
def reset_db_state():
    yield
    db = SessionLocal()
    try:
        seed_demo_requirements(db)
        seed_demo_orders(db)
    finally:
        db.close()


def get_token(client: TestClient, persona: str) -> str:
    res = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_r3_partial_allocation_ac_mat_03():
    """Seed R3 (Cauliflower, Grade A, 1,000 kg) yields PARTIAL fill with shortfall 700 kg (only L10 300 kg is Grade A)."""
    app = create_app()
    client = TestClient(app)

    token = get_token(client, "buyer_noida")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/matching/requirements/3/candidates", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["fill_status"] == "PARTIAL"
    assert data["requested_kg"] == 1000.0
    assert data["fulfilled_kg"] == 300.0
    assert data["shortfall_kg"] == 700.0
    assert len(data["allocations"]) == 1
    assert data["allocations"][0]["listing_id"] == 10
    assert data["allocations"][0]["quantity_kg"] == 300.0

    # Ensure candidates list contains L10 with factor scores and reasons
    assert len(data["candidates"]) >= 1
    c10 = next(c for c in data["candidates"] if c["listing"]["id"] == 10)
    assert c10["allocated_kg"] == 300.0
    assert 0.0 <= c10["scores"]["total"] <= 1.0
    assert len(c10["reasons"]) >= 1


def test_r8_budget_shortfall_ac_mat_04():
    """Seed R8 (Tomato, Grade A, 2,500 kg, budget ₹22.00) yields NONE with budget near-misses."""
    app = create_app()
    client = TestClient(app)

    # Operator can view candidates for any requirement
    token = get_token(client, "operator")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/matching/requirements/8/candidates", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["fill_status"] == "NONE"
    assert data["fulfilled_kg"] == 0.0
    assert data["shortfall_kg"] == 2500.0
    assert len(data["allocations"]) == 0

    # Near misses should explain why candidates were excluded
    assert len(data["near_misses"]) >= 1
    assert any(nm["excluded_reason"] in ["BUDGET", "GRADE"] for nm in data["near_misses"])


def test_r2_multi_source_allocation_ac_mat_05():
    """Seed R2 (Onion, Grade B, 6,500 kg) allocates across >1 listing."""
    app = create_app()
    client = TestClient(app)

    token = get_token(client, "operator")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/matching/requirements/2/candidates", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    # R2 requests 6,500 kg. Available Onion: L5 (4800 kg), L6 (2000 kg), L7 (1400 kg)
    assert len(data["allocations"]) > 1
    total_allocated = sum(a["quantity_kg"] for a in data["allocations"])
    assert total_allocated <= 6500.0
    assert data["fill_status"] in ["FULL", "PARTIAL"]


def test_accept_matching_allocation_and_atomic_orders_ac_mat_06():
    """Accepting matching allocation creates orders with origin=MATCHING and status=PLACED atomically."""
    app = create_app()
    client = TestClient(app)

    token = get_token(client, "buyer_noida")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get candidates for R3
    res_cand = client.get("/api/v1/matching/requirements/3/candidates", headers=headers)
    assert res_cand.status_code == 200
    cand_data = res_cand.json()

    allocations = cand_data["allocations"]
    assert len(allocations) > 0

    delivery_date = str(today_ist() + timedelta(days=2))
    accept_payload = {
        "requirement_id": 3,
        "allocations": allocations,
        "delivery_date": delivery_date,
    }

    # 2. Accept allocation
    res_accept = client.post("/api/v1/matching/accept", json=accept_payload, headers=headers)
    assert res_accept.status_code == 201, res_accept.text
    accept_data = res_accept.json()

    assert len(accept_data["orders"]) == 1
    order = accept_data["orders"][0]
    assert order["origin"] == "MATCHING"
    assert order["status"] == "PLACED"
    assert order["requirement_id"] == 3
    assert order["quantity_kg"] == 300.0
    assert order["listing_id"] == 10

    # 3. Verify requirement fulfillment updated
    req_summary = accept_data["requirement"]
    assert req_summary["id"] == 3
    assert req_summary["status"] == "PARTIALLY_FULFILLED"
    assert req_summary["quantity_fulfilled_kg"] == 300.0

    # 4. Verify listing inventory decremented
    db = SessionLocal()
    l10 = db.query(Listing).filter(Listing.id == 10).first()
    assert float(l10.quantity_available_kg) == 0.0
    assert l10.status == "SOLD_OUT"
    db.close()


def test_stale_allocation_rejection_ac_mat_07():
    """If listing inventory changes concurrently before accept, returns 409 STALE_ALLOCATION with zero orders created."""
    app = create_app()
    client = TestClient(app)

    token = get_token(client, "buyer_noida")
    headers = {"Authorization": f"Bearer {token}"}

    # Get candidates for R3
    res_cand = client.get("/api/v1/matching/requirements/3/candidates", headers=headers)
    assert res_cand.status_code == 200
    allocations = res_cand.json()["allocations"]

    # Concurrently reduce listing 10 availability below the allocation amount
    db = SessionLocal()
    l10 = db.query(Listing).filter(Listing.id == 10).first()
    l10.quantity_available_kg = 50.0  # was 300.0
    db.commit()
    db.close()

    delivery_date = str(today_ist() + timedelta(days=2))
    accept_payload = {
        "requirement_id": 3,
        "allocations": allocations,  # demands 300 kg
        "delivery_date": delivery_date,
    }

    res_accept = client.post("/api/v1/matching/accept", json=accept_payload, headers=headers)
    assert res_accept.status_code == 409, res_accept.text
    err = res_accept.json()["error"]
    assert err["code"] == "STALE_ALLOCATION"

    # Verify zero orders created
    db = SessionLocal()
    orders_count = db.query(Order).filter(Order.requirement_id == 3).count()
    assert orders_count == 0
    # Verify requirement fulfillment not modified
    r3 = db.query(Requirement).filter(Requirement.id == 3).first()
    assert float(r3.quantity_fulfilled_kg) == 0.0
    db.close()


def test_authorization_guards():
    """Verify object-level security: producers cannot view/accept matches; buyers cannot access others' requirements."""
    app = create_app()
    client = TestClient(app)

    producer_token = get_token(client, "fpo_sonipat")
    p_headers = {"Authorization": f"Bearer {producer_token}"}

    # Producer cannot view buyer match candidates
    res = client.get("/api/v1/matching/requirements/3/candidates", headers=p_headers)
    assert res.status_code == 403

    # Producer cannot accept matching allocation
    res = client.post(
        "/api/v1/matching/accept",
        json={"requirement_id": 3, "allocations": [{"listing_id": 10, "quantity_kg": 100}], "delivery_date": str(today_ist())},
        headers=p_headers,
    )
    assert res.status_code == 403

    # Buyer Gurugram cannot access Buyer Noida's requirement R3
    buyer_gurugram_token = get_token(client, "buyer_gurugram")
    bg_headers = {"Authorization": f"Bearer {buyer_gurugram_token}"}

    res = client.get("/api/v1/matching/requirements/3/candidates", headers=bg_headers)
    assert res.status_code == 403

    res = client.post(
        "/api/v1/matching/accept",
        json={"requirement_id": 3, "allocations": [{"listing_id": 10, "quantity_kg": 100}], "delivery_date": str(today_ist() + timedelta(days=2))},
        headers=bg_headers,
    )
    assert res.status_code == 403


def test_producer_opportunities_endpoint():
    """Producer can view compatible open requirements for their own active listing with hub context."""
    app = create_app()
    client = TestClient(app)

    # L10 is owned by P1 (fpo_sonipat), Cauliflower Grade A
    token = get_token(client, "fpo_sonipat")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/matching/listings/10/opportunities", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["listing"]["id"] == 10
    assert "opportunities" in data
    # R3 (Cauliflower Grade A, Buyer Noida) is compatible!
    assert any(opp["requirement"]["id"] == 3 for opp in data["opportunities"])

    # Check hub forecast context
    if data["hub_context"]:
        assert "forecast_7d_kg" in data["hub_context"]
        assert data["hub_context"]["status"] in ["SHORTAGE", "BALANCED", "SURPLUS"]

    # Unauthorized producer cannot view L10 opportunities
    other_producer_token = get_token(client, "fpo_meerut")
    other_headers = {"Authorization": f"Bearer {other_producer_token}"}
    res_unauth = client.get("/api/v1/matching/listings/10/opportunities", headers=other_headers)
    assert res_unauth.status_code == 403
