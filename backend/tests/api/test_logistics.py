from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.db.models import Vehicle
from app.main import app

client = TestClient(app)


def get_token(persona: str) -> str:
    res = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_get_logistics_vehicles_public():
    """Verify GET /api/v1/logistics/vehicles returns seeded fleet vehicles."""
    res = client.get("/api/v1/logistics/vehicles")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 5
    first = data["items"][0]
    assert "id" in first
    assert "name" in first
    assert "vehicle_type" in first
    assert "capacity_kg" in first
    assert "cost_per_km" in first
    assert "fixed_cost_per_trip" in first
    assert "avg_speed_kmph" in first
    assert "depot_name" in first
    assert "depot_lat" in first
    assert "depot_lng" in first
    assert "is_available" in first
    assert "is_demo" in first


def test_logistics_estimate_with_dest_coords():
    """Verify POST /api/v1/logistics/estimate with explicit coordinates."""
    # Listing 1 (Sonipat, lat 28.99, lng 77.02)
    # Target Noida: lat 28.57, lng 77.32
    res = client.post(
        "/api/v1/logistics/estimate",
        json={
            "listing_id": 1,
            "quantity_kg": 500.0,
            "dest_lat": 28.57,
            "dest_lng": 77.32,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["distance_km"] > 0
    assert data["distance_source"] == "ESTIMATED_HAVERSINE"
    assert data["trips"] == 1
    assert data["cost_total"] > 0
    assert data["cost_per_kg"] == round(data["cost_total"] / 500.0, 2)
    assert data["transit_hours"] > 0
    assert data["basis"] == "ESTIMATE"
    assert len(data["vehicle_plan"]) == 1
    assert data["vehicle_plan"][0]["vehicle_type"] == "MINI_TRUCK"
    assert data["vehicle_plan"][0]["load_kg"] == 500.0


def test_logistics_estimate_with_buyer_id():
    """Verify POST /api/v1/logistics/estimate with buyer_id."""
    # Buyer 1 (Gurugram B1)
    res = client.post(
        "/api/v1/logistics/estimate",
        json={
            "listing_id": 1,
            "quantity_kg": 1200.0,
            "buyer_id": 1,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["trips"] == 1
    assert len(data["vehicle_plan"]) == 1
    assert data["vehicle_plan"][0]["vehicle_type"] == "PICKUP"
    assert data["vehicle_plan"][0]["load_kg"] == 1200.0


def test_logistics_estimate_with_auth_buyer_default():
    """Verify POST /api/v1/logistics/estimate defaults to authenticated buyer coordinates."""
    token = get_token("buyer_gurugram")
    res = client.post(
        "/api/v1/logistics/estimate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "listing_id": 1,
            "quantity_kg": 800.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["trips"] == 1
    assert data["vehicle_plan"][0]["vehicle_type"] == "PICKUP"


def test_logistics_estimate_multi_trip_large_quantity():
    """AC-LOG-03: Multi-trip allocation when quantity exceeds largest vehicle capacity (4000 kg)."""
    # 5500 kg -> 1x MEDIUM_TRUCK (4000 kg) + 1x PICKUP (1500 kg)
    res = client.post(
        "/api/v1/logistics/estimate",
        json={
            "listing_id": 1,
            "quantity_kg": 5500.0,
            "dest_lat": 28.57,
            "dest_lng": 77.32,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["trips"] == 2
    assert len(data["vehicle_plan"]) == 2
    types = [v["vehicle_type"] for v in data["vehicle_plan"]]
    assert "MEDIUM_TRUCK" in types
    assert "PICKUP" in types
    assert data["cost_per_kg"] == round(data["cost_total"] / 5500.0, 2)


def test_logistics_estimate_listing_not_found():
    """Verify 404 NOT_FOUND for unknown listing."""
    res = client.post(
        "/api/v1/logistics/estimate",
        json={
            "listing_id": 99999,
            "quantity_kg": 500.0,
            "dest_lat": 28.57,
            "dest_lng": 77.32,
        },
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_logistics_estimate_buyer_not_found():
    """Verify 404 NOT_FOUND for unknown buyer_id."""
    res = client.post(
        "/api/v1/logistics/estimate",
        json={
            "listing_id": 1,
            "quantity_kg": 500.0,
            "buyer_id": 99999,
        },
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_logistics_estimate_missing_destination():
    """Verify 422 VALIDATION_ERROR when no destination coords, buyer_id, or buyer auth provided."""
    res = client.post(
        "/api/v1/logistics/estimate",
        json={
            "listing_id": 1,
            "quantity_kg": 500.0,
        },
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_logistics_estimate_invalid_quantity():
    """Verify 422 for non-positive quantity."""
    res = client.post(
        "/api/v1/logistics/estimate",
        json={
            "listing_id": 1,
            "quantity_kg": -10.0,
            "dest_lat": 28.57,
            "dest_lng": 77.32,
        },
    )
    assert res.status_code == 422


def test_logistics_estimate_no_vehicles_available():
    """AC-LOG-05: Returns 409 NO_VEHICLE_AVAILABLE when no vehicles are available in fleet."""
    db = SessionLocal()
    try:
        # Temporarily mark all vehicles unavailable
        vehicles = db.query(Vehicle).all()
        for v in vehicles:
            v.is_available = False
        db.commit()

        res = client.post(
            "/api/v1/logistics/estimate",
            json={
                "listing_id": 1,
                "quantity_kg": 500.0,
                "dest_lat": 28.57,
                "dest_lng": 77.32,
            },
        )
        assert res.status_code == 409
        assert res.json()["error"]["code"] == "NO_VEHICLE_AVAILABLE"
    finally:
        # Restore vehicles
        for v in vehicles:
            v.is_available = True
        db.commit()
        db.close()
