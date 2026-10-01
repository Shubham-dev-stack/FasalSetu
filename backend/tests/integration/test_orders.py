from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.dates import today_ist
from app.db.models import Listing, Requirement
from app.main import create_app


def get_token(client: TestClient, persona: str) -> str:
    res = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_create_order_atomic_reservation():
    app = create_app()
    client = TestClient(app)

    buyer_token = get_token(client, "buyer_gurugram")
    headers = {"Authorization": f"Bearer {buyer_token}"}

    db = SessionLocal()
    # Check L3 (600 kg available, min order 100 kg, Tomato, Producer P3)
    l3 = db.query(Listing).filter(Listing.id == 3).first()
    initial_avail = float(l3.quantity_available_kg)
    db.close()

    delivery_date = str(today_ist() + timedelta(days=2))
    payload = {
        "listing_id": 3,
        "quantity_kg": 200.0,
        "delivery_date": delivery_date,
    }

    res = client.post("/api/v1/orders", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    order_data = res.json()
    assert order_data["status"] == "PLACED"
    assert order_data["quantity_kg"] == 200.0
    assert order_data["origin"] == "MARKETPLACE"
    assert len(order_data["events"]) >= 1
    assert order_data["events"][0]["to_status"] == "PLACED"

    # Verify atomic inventory decrement
    db = SessionLocal()
    l3_after = db.query(Listing).filter(Listing.id == 3).first()
    assert float(l3_after.quantity_available_kg) == initial_avail - 200.0
    db.close()


def test_create_order_below_min_order_and_insufficient_quantity():
    app = create_app()
    client = TestClient(app)

    buyer_token = get_token(client, "buyer_gurugram")
    headers = {"Authorization": f"Bearer {buyer_token}"}
    delivery_date = str(today_ist() + timedelta(days=2))

    # L3 min order is 100 kg; order 50 kg -> 422 (AC-ORD-03)
    res = client.post(
        "/api/v1/orders",
        json={"listing_id": 3, "quantity_kg": 50.0, "delivery_date": delivery_date},
        headers=headers,
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"

    # Order more than available -> 409 (AC-ORD-02)
    res2 = client.post(
        "/api/v1/orders",
        json={"listing_id": 3, "quantity_kg": 10000.0, "delivery_date": delivery_date},
        headers=headers,
    )
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "INSUFFICIENT_QUANTITY"


def create_test_listing(client: TestClient, quantity_kg: float = 500.0) -> int:
    token = get_token(client, "fpo_sonipat")
    today = today_ist()
    payload = {
        "crop_id": 1,
        "variety": "Pusa Ruby Test",
        "grade": "B",
        "quantity_kg": quantity_kg,
        "ask_price_per_kg": 23.0,
        "min_order_kg": 100.0,
        "harvest_date": str(today - timedelta(days=1)),
        "available_from": str(today),
        "available_until": str(today + timedelta(days=5)),
    }
    res = client.post(
        "/api/v1/listings", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 201, res.text
    return res.json()["listing"]["id"]


def test_order_concurrency_no_oversell():
    app = create_app()
    client = TestClient(app)

    buyer_token = get_token(client, "buyer_gurugram")
    headers = {"Authorization": f"Bearer {buyer_token}"}
    delivery_date = str(today_ist() + timedelta(days=2))

    listing_id = create_test_listing(client, quantity_kg=400.0)

    # Order entire available quantity (400 kg)
    res1 = client.post(
        "/api/v1/orders",
        json={"listing_id": listing_id, "quantity_kg": 400.0, "delivery_date": delivery_date},
        headers=headers,
    )
    assert res1.status_code == 201

    # Second order must fail with 409 (AC-ORD-04)
    res2 = client.post(
        "/api/v1/orders",
        json={"listing_id": listing_id, "quantity_kg": 100.0, "delivery_date": delivery_date},
        headers=headers,
    )
    assert res2.status_code == 409

    # Check listing status is SOLD_OUT and available is 0
    db = SessionLocal()
    l_after = db.query(Listing).filter(Listing.id == listing_id).first()
    assert float(l_after.quantity_available_kg) == 0.0
    assert l_after.status == "SOLD_OUT"
    db.close()


def test_order_status_transitions_and_rejection():
    app = create_app()
    client = TestClient(app)

    buyer_token = get_token(client, "buyer_noida")
    producer_token = get_token(client, "fpo_sonipat")
    operator_token = get_token(client, "operator")

    delivery_date = str(today_ist() + timedelta(days=2))

    # Create order on L10 (Sonipat Cauliflower, P1)
    res = client.post(
        "/api/v1/orders",
        json={"listing_id": 10, "quantity_kg": 100.0, "delivery_date": delivery_date},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    assert res.status_code == 201
    order_id = res.json()["id"]

    # Producer confirms order (PLACED -> CONFIRMED)
    res_conf = client.post(
        f"/api/v1/orders/{order_id}/transition",
        json={"to_status": "CONFIRMED", "note": "Confirmed by FPO Sonipat"},
        headers={"Authorization": f"Bearer {producer_token}"},
    )
    assert res_conf.status_code == 200
    assert res_conf.json()["status"] == "CONFIRMED"

    # Confirmed order can be cancelled while unrouted
    res_cancel = client.post(
        f"/api/v1/orders/{order_id}/transition",
        json={"to_status": "CANCELLED", "note": "Cancelled unrouted order"},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELLED"

    # Cannot transition terminal order -> 409
    res_invalid = client.post(
        f"/api/v1/orders/{order_id}/transition",
        json={"to_status": "CONFIRMED"},
        headers={"Authorization": f"Bearer {producer_token}"},
    )
    assert res_invalid.status_code == 409
    assert res_invalid.json()["error"]["code"] == "INVALID_TRANSITION"

    # Test operator override on another order (AC-ORD-05)
    res_op = client.post(
        "/api/v1/orders",
        json={"listing_id": 10, "quantity_kg": 100.0, "delivery_date": delivery_date},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    assert res_op.status_code == 201
    op_order_id = res_op.json()["id"]

    res_op_conf = client.post(
        f"/api/v1/orders/{op_order_id}/transition",
        json={"to_status": "CONFIRMED", "note": "Operator override confirmation"},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert res_op_conf.status_code == 200
    assert res_op_conf.json()["status"] == "CONFIRMED"
    events = res_op_conf.json()["events"]
    assert any(e["actor_role"] == "ADMIN" and e["to_status"] == "CONFIRMED" for e in events)


def test_strict_requirement_compatibility_validation():
    app = create_app()
    client = TestClient(app)

    buyer_token = get_token(client, "buyer_gurugram")  # B1
    headers = {"Authorization": f"Bearer {buyer_token}"}
    delivery_date = str(today_ist() + timedelta(days=1))

    # R1 belongs to B1: Tomato, Grade B, 1500 kg, Max landed 29.00
    # Attempt linking order for Listing 5 (Onion) with R1 (Tomato) -> 422 crop mismatch
    res_crop_mismatch = client.post(
        "/api/v1/orders",
        json={
            "listing_id": 5,
            "quantity_kg": 500.0,
            "delivery_date": delivery_date,
            "requirement_id": 1,
        },
        headers=headers,
    )
    assert res_crop_mismatch.status_code == 422
    assert "crop" in res_crop_mismatch.json()["error"]["message"].lower()

    # Attempt linking order on requirement owned by buyer_noida (R3 belongs to B2) -> 403
    res_forbidden_req = client.post(
        "/api/v1/orders",
        json={
            "listing_id": 10,
            "quantity_kg": 100.0,
            "delivery_date": delivery_date,
            "requirement_id": 3,
        },
        headers=headers,
    )
    assert res_forbidden_req.status_code == 403

    # Attempt ordering quantity exceeding requirement remaining quantity -> 422
    res_qty_exceed = client.post(
        "/api/v1/orders",
        json={
            "listing_id": 2,  # Tomato Grade A, 700 kg available
            "quantity_kg": 2000.0,
            "delivery_date": delivery_date,
            "requirement_id": 1,
        },
        headers=headers,
    )
    assert res_qty_exceed.status_code in [409, 422]


def test_order_requirement_fulfillment_synchronization():
    app = create_app()
    client = TestClient(app)

    buyer_token = get_token(client, "buyer_gurugram")  # B1
    headers = {"Authorization": f"Bearer {buyer_token}"}
    delivery_date = str(today_ist() + timedelta(days=2))

    # Create a fresh requirement for buyer_gurugram with realistic budget
    req_res = client.post(
        "/api/v1/requirements",
        json={
            "crop_id": 1,
            "grade_min": "B",
            "quantity_kg": 1000.0,
            "max_landed_price_per_kg": 50.00,
            "needed_by": delivery_date,
            "notes": "Test fulfillment sync requirement",
        },
        headers=headers,
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # Place valid linked order on fresh requirement from L2 (Tomato Grade A)
    res = client.post(
        "/api/v1/orders",
        json={
            "listing_id": 2,
            "quantity_kg": 200.0,
            "delivery_date": delivery_date,
            "requirement_id": req_id,
        },
        headers=headers,
    )
    assert res.status_code == 201, res.text
    order_id = res.json()["id"]

    # Verify requirement fulfilled quantity increased
    db = SessionLocal()
    r = db.query(Requirement).filter(Requirement.id == req_id).first()
    assert float(r.quantity_fulfilled_kg) == 200.0
    assert r.status == "PARTIALLY_FULFILLED"
    db.close()

    # Cancel the order -> fulfillment restored to 0, status back to OPEN
    res_cancel = client.post(
        f"/api/v1/orders/{order_id}/transition",
        json={"to_status": "CANCELLED", "note": "Cancel linked order"},
        headers=headers,
    )
    assert res_cancel.status_code == 200

    db = SessionLocal()
    r_after = db.query(Requirement).filter(Requirement.id == req_id).first()
    assert float(r_after.quantity_fulfilled_kg) == 0.0
    assert r_after.status == "OPEN"
    db.close()


def test_order_object_level_authorization():
    app = create_app()
    client = TestClient(app)

    buyer1_token = get_token(client, "buyer_gurugram")
    buyer2_token = get_token(client, "buyer_noida")
    producer1_token = get_token(client, "fpo_sonipat")
    producer2_token = get_token(client, "fpo_meerut")

    delivery_date = str(today_ist() + timedelta(days=2))

    # Buyer 1 places order on L13 (Sonipat, P1)
    res = client.post(
        "/api/v1/orders",
        json={"listing_id": 13, "quantity_kg": 50.0, "delivery_date": delivery_date},
        headers={"Authorization": f"Bearer {buyer1_token}"},
    )
    assert res.status_code == 201
    order_id = res.json()["id"]

    # Buyer 2 tries to GET order -> 403
    res_b2_get = client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {buyer2_token}"},
    )
    assert res_b2_get.status_code == 403

    # Buyer 2 tries to CANCEL order -> 403
    res_b2_cancel = client.post(
        f"/api/v1/orders/{order_id}/transition",
        json={"to_status": "CANCELLED"},
        headers={"Authorization": f"Bearer {buyer2_token}"},
    )
    assert res_b2_cancel.status_code == 403

    # Non-owning producer tries to GET order -> 403
    res_p2_get = client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {producer2_token}"},
    )
    assert res_p2_get.status_code == 403

    # Non-owning producer tries to CONFIRM order -> 403
    res_p2_conf = client.post(
        f"/api/v1/orders/{order_id}/transition",
        json={"to_status": "CONFIRMED"},
        headers={"Authorization": f"Bearer {producer2_token}"},
    )
    assert res_p2_conf.status_code == 403

    # Owning producer CAN view and confirm
    res_p1_get = client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {producer1_token}"},
    )
    assert res_p1_get.status_code == 200
