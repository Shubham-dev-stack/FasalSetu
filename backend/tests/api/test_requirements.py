from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.dates import today_ist
from app.db.models import Requirement
from app.main import create_app

app = create_app()
client = TestClient(app)


def get_token(persona: str) -> str:
    resp = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_create_requirement_success():
    """AC-REQ-01: Valid buyer creates requirement."""
    token = get_token("buyer_gurugram")
    today = today_ist()
    payload = {
        "crop_id": 1,
        "grade_min": "B",
        "quantity_kg": 1200.0,
        "max_landed_price_per_kg": 30.0,
        "needed_by": (today + timedelta(days=4)).isoformat(),
        "notes": "Test demand for Gurugram kitchen",
    }
    resp = client.post(
        "/api/v1/requirements",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "OPEN"
    assert data["quantity_fulfilled_kg"] == 0.0
    assert data["quantity_kg"] == 1200.0
    assert data["max_landed_price_per_kg"] == 30.0
    assert data["crop"]["name"] == "Tomato"
    assert data["buyer"]["org_name"] == "Gurugram Restaurant Group [DEMO]"
    assert data["landed_guidance"]["note"] == "Includes farmgate ask + transport + 2% platform fee"


def test_producer_forbidden_on_requirements():
    """AC-REQ-02 & Correction 4: Producers receive 403 on all requirement endpoints."""
    token = get_token("fpo_sonipat")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /requirements -> 403
    resp_list = client.get("/api/v1/requirements", headers=headers)
    assert resp_list.status_code == 403
    assert resp_list.json()["error"]["code"] == "FORBIDDEN"

    # 2. GET /requirements/{id} -> 403
    resp_detail = client.get("/api/v1/requirements/1", headers=headers)
    assert resp_detail.status_code == 403
    assert resp_detail.json()["error"]["code"] == "FORBIDDEN"

    # 3. POST /requirements -> 403
    today = today_ist()
    payload = {
        "crop_id": 1,
        "grade_min": "A",
        "quantity_kg": 500.0,
        "max_landed_price_per_kg": 25.0,
        "needed_by": (today + timedelta(days=2)).isoformat(),
    }
    resp_create = client.post("/api/v1/requirements", json=payload, headers=headers)
    assert resp_create.status_code == 403
    assert resp_create.json()["error"]["code"] == "FORBIDDEN"

    # 4. PATCH /requirements/{id} -> 403
    resp_patch = client.patch(
        "/api/v1/requirements/1",
        json={"notes": "Producer unauthorized"},
        headers=headers,
    )
    assert resp_patch.status_code == 403
    assert resp_patch.json()["error"]["code"] == "FORBIDDEN"


def test_create_requirement_validation_errors():
    """AC-REQ-03: Invalid inputs fail validation."""
    token = get_token("buyer_gurugram")
    headers = {"Authorization": f"Bearer {token}"}
    today = today_ist()

    # Past needed_by
    resp = client.post(
        "/api/v1/requirements",
        json={
            "crop_id": 1,
            "grade_min": "B",
            "quantity_kg": 500.0,
            "max_landed_price_per_kg": 25.0,
            "needed_by": (today - timedelta(days=1)).isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 422

    # Zero or negative quantity
    resp = client.post(
        "/api/v1/requirements",
        json={
            "crop_id": 1,
            "grade_min": "B",
            "quantity_kg": 0.0,
            "max_landed_price_per_kg": 25.0,
            "needed_by": (today + timedelta(days=2)).isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 422

    # Negative price
    resp = client.post(
        "/api/v1/requirements",
        json={
            "crop_id": 1,
            "grade_min": "B",
            "quantity_kg": 500.0,
            "max_landed_price_per_kg": -10.0,
            "needed_by": (today + timedelta(days=2)).isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 422

    # Invalid grade
    resp = client.post(
        "/api/v1/requirements",
        json={
            "crop_id": 1,
            "grade_min": "D",
            "quantity_kg": 500.0,
            "max_landed_price_per_kg": 25.0,
            "needed_by": (today + timedelta(days=2)).isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 422

    # Non-existent crop
    resp = client.post(
        "/api/v1/requirements",
        json={
            "crop_id": 9999,
            "grade_min": "A",
            "quantity_kg": 500.0,
            "max_landed_price_per_kg": 25.0,
            "needed_by": (today + timedelta(days=2)).isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 404


def test_get_requirements_scoped_to_buyer():
    """Verify buyer only lists their own requirements."""
    token = get_token("buyer_noida")  # Buyer B2 (owns R3)
    resp = client.get(
        "/api/v1/requirements",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["buyer"]["org_name"] == "Noida RWA Group-Buying Collective [DEMO]"


def test_get_requirement_by_id_and_cross_buyer_forbidden():
    """Verify detail response and cross-buyer 403 protection."""
    token_b1 = get_token("buyer_gurugram")  # Buyer 1 owns R1
    token_b2 = get_token("buyer_noida")  # Buyer 2

    # Owner accesses R1
    resp = client.get(
        "/api/v1/requirements/1",
        headers={"Authorization": f"Bearer {token_b1}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["requirement"]["id"] == 1
    assert data["landed_guidance"]["formula"] == "max_landed_price >= farmgate_ask + transport_cost + platform_fee (2%)"

    # Non-owner accesses R1 -> 403 Forbidden
    resp_cross = client.get(
        "/api/v1/requirements/1",
        headers={"Authorization": f"Bearer {token_b2}"},
    )
    assert resp_cross.status_code == 403
    assert resp_cross.json()["error"]["code"] == "FORBIDDEN"


def test_patch_requirement_lifecycle_and_cancellation():
    """Verify buyer can update fields and cancel, and subsequent edits fail with 409."""
    token = get_token("buyer_gurugram")
    headers = {"Authorization": f"Bearer {token}"}
    today = today_ist()

    # Create requirement to test
    create_resp = client.post(
        "/api/v1/requirements",
        json={
            "crop_id": 2,
            "grade_min": "B",
            "quantity_kg": 1000.0,
            "max_landed_price_per_kg": 25.0,
            "needed_by": (today + timedelta(days=5)).isoformat(),
            "notes": "Original notes",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    req_id = create_resp.json()["id"]

    # Update notes and price
    patch_resp = client.patch(
        f"/api/v1/requirements/{req_id}",
        json={"notes": "Updated notes", "max_landed_price_per_kg": 26.5},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["notes"] == "Updated notes"
    assert patch_resp.json()["max_landed_price_per_kg"] == 26.5

    # Cancel requirement
    cancel_resp = client.patch(
        f"/api/v1/requirements/{req_id}",
        json={"status": "CANCELLED"},
        headers=headers,
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    # Subsequent edit on CANCELLED must return 409 CONFLICT
    fail_resp = client.patch(
        f"/api/v1/requirements/{req_id}",
        json={"notes": "Trying to edit cancelled"},
        headers=headers,
    )
    assert fail_resp.status_code == 409
    assert fail_resp.json()["error"]["code"] == "CONFLICT"


def test_dynamic_expiry_on_get_and_patch():
    """Rule D-021: needed_by in past dynamically expires and rejects PATCH with 409."""
    token = get_token("buyer_gurugram")
    headers = {"Authorization": f"Bearer {token}"}
    today = today_ist()

    # Create requirement
    create_resp = client.post(
        "/api/v1/requirements",
        json={
            "crop_id": 3,
            "grade_min": "B",
            "quantity_kg": 800.0,
            "max_landed_price_per_kg": 20.0,
            "needed_by": (today + timedelta(days=3)).isoformat(),
        },
        headers=headers,
    )
    req_id = create_resp.json()["id"]

    # Directly set needed_by to yesterday in DB to test dynamic expiry
    db = SessionLocal()
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    req.needed_by = today - timedelta(days=1)
    db.commit()
    db.close()

    # GET triggers dynamic expiry
    get_resp = client.get(f"/api/v1/requirements/{req_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["requirement"]["status"] == "EXPIRED"

    # PATCH on expired requirement is rejected with 409 CONFLICT
    patch_resp = client.patch(
        f"/api/v1/requirements/{req_id}",
        json={"notes": "Edit expired"},
        headers=headers,
    )
    assert patch_resp.status_code == 409
    assert patch_resp.json()["error"]["code"] == "CONFLICT"


def test_patch_cannot_reduce_quantity_below_fulfilled():
    """Verify buyer cannot reduce quantity_kg below quantity_fulfilled_kg."""
    token = get_token("buyer_gurugram")
    headers = {"Authorization": f"Bearer {token}"}
    today = today_ist()

    create_resp = client.post(
        "/api/v1/requirements",
        json={
            "crop_id": 1,
            "grade_min": "A",
            "quantity_kg": 2000.0,
            "max_landed_price_per_kg": 30.0,
            "needed_by": (today + timedelta(days=5)).isoformat(),
        },
        headers=headers,
    )
    req_id = create_resp.json()["id"]

    # Simulate partial fulfillment in DB
    db = SessionLocal()
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    req.quantity_fulfilled_kg = 500.0
    req.status = "PARTIALLY_FULFILLED"
    db.commit()
    db.close()

    # Attempt to reduce quantity_kg to 400.0 (< 500.0)
    patch_resp = client.patch(
        f"/api/v1/requirements/{req_id}",
        json={"quantity_kg": 400.0},
        headers=headers,
    )
    assert patch_resp.status_code == 409
    assert patch_resp.json()["error"]["code"] == "CONFLICT"


def test_seed_requirements_r1_to_r8_present():
    """Verify seeded open requirements R1-R8 per Data.md §12."""
    db = SessionLocal()
    reqs = db.query(Requirement).order_by(Requirement.id).all()
    db.close()

    assert len(reqs) >= 8
    r1 = next(r for r in reqs if r.id == 1)
    assert r1.crop_id == 1
    assert r1.grade_min == "B"
    assert r1.quantity_kg == 1500.0
    assert float(r1.max_landed_price_per_kg) == 29.0
    assert r1.status == "OPEN"

    r8 = next(r for r in reqs if r.id == 8)
    assert r8.crop_id == 1
    assert r8.grade_min == "A"
    assert r8.quantity_kg == 2500.0
    assert float(r8.max_landed_price_per_kg) == 22.0
