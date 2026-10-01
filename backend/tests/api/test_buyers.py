from fastapi.testclient import TestClient

from app.main import create_app

app = create_app()
client = TestClient(app)


def get_token(persona: str) -> str:
    resp = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_get_buyer_profile_success():
    token = get_token("buyer_gurugram")
    resp = client.get(
        "/api/v1/buyers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["buyer_type"] == "RESTAURANT"
    assert "Gurugram" in data["org_name"]
    assert data["city"] == "Gurugram"
    assert data["state"] == "Haryana"
    assert data["hub_id"] == 2
    assert data["lat"] == 28.47
    assert data["lng"] == 77.05
    assert data["is_demo"] is True


def test_get_buyer_profile_unauthorized_for_producer():
    token = get_token("fpo_sonipat")
    resp = client.get(
        "/api/v1/buyers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    data = resp.json()
    assert data["error"]["code"] == "FORBIDDEN"


def test_get_buyer_profile_unauthenticated():
    resp = client.get("/api/v1/buyers/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_patch_buyer_profile_success():
    token = get_token("buyer_gurugram")
    resp = client.patch(
        "/api/v1/buyers/me",
        json={"org_name": "Gurugram Premium Dine Hub", "city": "Gurugram Central"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["org_name"] == "Gurugram Premium Dine Hub"
    assert data["city"] == "Gurugram Central"

    # Reset back for seed consistency
    client.patch(
        "/api/v1/buyers/me",
        json={"org_name": "Gurugram Restaurant Group [DEMO]", "city": "Gurugram"},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_patch_buyer_profile_invalid_coordinates():
    token = get_token("buyer_gurugram")
    # Latitude out of bounds (< 6.0)
    resp = client.patch(
        "/api/v1/buyers/me",
        json={"lat": 4.5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422

    # Longitude out of bounds (> 98.0)
    resp = client.patch(
        "/api/v1/buyers/me",
        json={"lng": 105.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_patch_buyer_profile_invalid_hub():
    token = get_token("buyer_gurugram")
    resp = client.patch(
        "/api/v1/buyers/me",
        json={"hub_id": 9999},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
