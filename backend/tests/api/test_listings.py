from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.dates import today_ist
from app.main import create_app

app = create_app()
client = TestClient(app)


def get_token(persona: str) -> str:
    resp = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_seed_listings_exist():
    # Verify seeded listings L1-L14 exist per Data.md §12
    resp = client.get("/api/v1/listings?limit=100")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 14
    items_by_id = {item["id"]: item for item in data["items"]}
    assert 1 in items_by_id
    assert 14 in items_by_id

    # Check L1: Producer P2 (Bulandshahr), Tomato, Grade B, 800 kg, Ask 22.50, Min 100
    l1 = items_by_id[1]
    assert l1["crop"]["name"] == "Tomato"
    assert l1["grade"] == "B"
    assert l1["quantity_kg"] == 800.0
    assert l1["ask_price_per_kg"] == 22.50
    assert l1["min_order_kg"] == 100.0
    assert l1["status"] == "ACTIVE"


def test_create_listing_success():
    # AC-LST-01: Valid listing creates ACTIVE listing with quantity_available_kg = quantity_kg
    token = get_token("fpo_sonipat")
    today = today_ist()

    payload = {
        "crop_id": 1,
        "variety": "Pusa Ruby",
        "grade": "A",
        "quantity_kg": 1500.0,
        "ask_price_per_kg": 24.0,
        "min_order_kg": 150.0,
        "harvest_date": str(today - timedelta(days=2)),
        "available_from": str(today),
        "available_until": str(today + timedelta(days=5)),
    }

    resp = client.post(
        "/api/v1/listings",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    listing = data["listing"]
    assert listing["quantity_kg"] == 1500.0
    assert listing["quantity_available_kg"] == 1500.0
    assert listing["status"] == "ACTIVE"
    assert listing["grade"] == "A"
    assert listing["producer"]["org_name"] == "Sonipat Kisan Collective [DEMO]"
    assert listing["harvest_age_days"] == 2
    assert "warnings" in data


def test_create_listing_invalid_quantity():
    # AC-LST-02: Quantity <= 0 or > 100000
    token = get_token("fpo_sonipat")
    today = today_ist()

    base_payload = {
        "crop_id": 1,
        "grade": "A",
        "ask_price_per_kg": 24.0,
        "min_order_kg": 50.0,
        "harvest_date": str(today),
        "available_from": str(today),
        "available_until": str(today + timedelta(days=5)),
    }

    # Zero quantity
    resp1 = client.post(
        "/api/v1/listings",
        json={**base_payload, "quantity_kg": 0.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 422

    # Negative quantity
    resp2 = client.post(
        "/api/v1/listings",
        json={**base_payload, "quantity_kg": -100.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 422

    # Exceeding 100,000 kg
    resp3 = client.post(
        "/api/v1/listings",
        json={**base_payload, "quantity_kg": 150000.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp3.status_code == 422


def test_create_listing_invalid_price():
    # AC-LST-03: Price <= 0 or > 100000
    token = get_token("fpo_sonipat")
    today = today_ist()

    base_payload = {
        "crop_id": 1,
        "grade": "A",
        "quantity_kg": 1000.0,
        "min_order_kg": 50.0,
        "harvest_date": str(today),
        "available_from": str(today),
        "available_until": str(today + timedelta(days=5)),
    }

    # Zero price
    resp = client.post(
        "/api/v1/listings",
        json={**base_payload, "ask_price_per_kg": 0.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_create_listing_price_warning_above_benchmark():
    # AC-LST-03: ask > 3x benchmark returns 201 with PRICE_FAR_ABOVE_BENCHMARK warning
    token = get_token("fpo_sonipat")
    today = today_ist()

    # Benchmark for tomato is ~22-25. Setting ask to 150 (which is > 3x)
    payload = {
        "crop_id": 1,
        "grade": "A",
        "quantity_kg": 500.0,
        "ask_price_per_kg": 150.0,
        "min_order_kg": 50.0,
        "harvest_date": str(today),
        "available_from": str(today),
        "available_until": str(today + timedelta(days=5)),
    }

    resp = client.post(
        "/api/v1/listings",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "PRICE_FAR_ABOVE_BENCHMARK" in data["warnings"]
    assert data["benchmark_context"] is not None
    assert data["benchmark_context"]["benchmark_modal_per_kg"] is not None


def test_create_listing_date_and_order_validations():
    # AC-LST-04: min_order>quantity, until<from, until<today, harvest in future or >30 days old
    token = get_token("fpo_sonipat")
    today = today_ist()

    base = {
        "crop_id": 1,
        "grade": "A",
        "quantity_kg": 500.0,
        "ask_price_per_kg": 25.0,
        "min_order_kg": 100.0,
        "harvest_date": str(today),
        "available_from": str(today),
        "available_until": str(today + timedelta(days=3)),
    }

    # min_order > quantity
    resp1 = client.post(
        "/api/v1/listings",
        json={**base, "min_order_kg": 600.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 422

    # until < from
    resp2 = client.post(
        "/api/v1/listings",
        json={
            **base,
            "available_from": str(today + timedelta(days=4)),
            "available_until": str(today + timedelta(days=2)),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 422

    # until in the past
    resp3 = client.post(
        "/api/v1/listings",
        json={
            **base,
            "available_from": str(today - timedelta(days=5)),
            "available_until": str(today - timedelta(days=2)),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp3.status_code == 422

    # harvest in the future
    resp4 = client.post(
        "/api/v1/listings",
        json={**base, "harvest_date": str(today + timedelta(days=1))},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp4.status_code == 422

    # harvest > 30 days old
    resp5 = client.post(
        "/api/v1/listings",
        json={**base, "harvest_date": str(today - timedelta(days=35))},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp5.status_code == 422


def test_create_listing_unknown_crop():
    # AC-LST-05: Unknown crop_id
    token = get_token("fpo_sonipat")
    today = today_ist()

    resp = client.post(
        "/api/v1/listings",
        json={
            "crop_id": 999,
            "grade": "A",
            "quantity_kg": 500.0,
            "ask_price_per_kg": 25.0,
            "min_order_kg": 50.0,
            "harvest_date": str(today),
            "available_from": str(today),
            "available_until": str(today + timedelta(days=3)),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_listing_detail():
    # Explicit ListingDetailResponse verification
    resp = client.get("/api/v1/listings/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "listing" in data
    assert data["listing"]["id"] == 1
    assert data["listing"]["crop"]["name"] == "Tomato"
    assert "benchmark_context" in data


def test_patch_listing_object_level_authz():
    # AC-LST-06 & AC-SEC-03: Producer A cannot patch Producer B's listing
    # L10 is owned by Producer P1 (Sonipat Kisan Collective)
    # Login as Karnal Farmer (Producer P5)
    token_karnal = get_token("farmer_karnal")

    resp = client.patch(
        "/api/v1/listings/10",
        json={"ask_price_per_kg": 35.0},
        headers={"Authorization": f"Bearer {token_karnal}"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_patch_listing_owner_update_and_withdraw():
    token_sonipat = get_token("fpo_sonipat")
    today = today_ist()

    # Create a fresh lot to edit and withdraw
    create_resp = client.post(
        "/api/v1/listings",
        json={
            "crop_id": 4,
            "grade": "B",
            "quantity_kg": 400.0,
            "ask_price_per_kg": 26.0,
            "min_order_kg": 50.0,
            "harvest_date": str(today),
            "available_from": str(today),
            "available_until": str(today + timedelta(days=4)),
        },
        headers={"Authorization": f"Bearer {token_sonipat}"},
    )
    assert create_resp.status_code == 201
    listing_id = create_resp.json()["listing"]["id"]

    # Update ask price
    resp = client.patch(
        f"/api/v1/listings/{listing_id}",
        json={"ask_price_per_kg": 29.50},
        headers={"Authorization": f"Bearer {token_sonipat}"},
    )
    assert resp.status_code == 200
    assert resp.json()["ask_price_per_kg"] == 29.50

    # Withdraw listing
    resp_withdraw = client.patch(
        f"/api/v1/listings/{listing_id}",
        json={"status": "WITHDRAWN"},
        headers={"Authorization": f"Bearer {token_sonipat}"},
    )
    assert resp_withdraw.status_code == 200
    assert resp_withdraw.json()["status"] == "WITHDRAWN"

    # AC-LST-07: Verify this withdrawn listing is excluded from default ACTIVE marketplace
    resp_mkt = client.get("/api/v1/listings?status=ACTIVE")
    assert resp_mkt.status_code == 200
    mkt_ids = [it["id"] for it in resp_mkt.json()["items"]]
    assert listing_id not in mkt_ids



def test_producer_mine_filter():
    token_sonipat = get_token("fpo_sonipat")
    resp = client.get(
        "/api/v1/listings?mine=true&status=ALL",
        headers={"Authorization": f"Bearer {token_sonipat}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["producer"]["org_name"] == "Sonipat Kisan Collective [DEMO]"
