from fastapi.testclient import TestClient

from app.main import create_app

app = create_app()
client = TestClient(app)


def get_token(persona: str) -> str:
    resp = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_get_producer_profile_success():
    token = get_token("fpo_sonipat")
    resp = client.get(
        "/api/v1/producers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["producer_type"] == "FPO"
    assert "Sonipat" in data["org_name"]
    assert data["district"] == "Sonipat"
    assert data["member_farmers"] == 120
    assert data["lat"] == 28.99
    assert data["lng"] == 77.02



def test_get_producer_profile_unauthorized_for_buyer():
    # AC-AUTH-03: Role guard
    token = get_token("buyer_gurugram")
    resp = client.get(
        "/api/v1/producers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    data = resp.json()
    assert data["error"]["code"] == "FORBIDDEN"


def test_get_producer_profile_unauthenticated():
    resp = client.get("/api/v1/producers/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_patch_producer_profile_success():
    token = get_token("fpo_sonipat")
    resp = client.patch(
        "/api/v1/producers/me",
        json={"locality": "Rai Industrial Zone", "member_farmers": 290},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["locality"] == "Rai Industrial Zone"
    assert data["member_farmers"] == 290

    # Restore to original seeded state
    restore_resp = client.patch(
        "/api/v1/producers/me",
        json={"locality": None, "member_farmers": 120},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["member_farmers"] == 120



def test_patch_producer_profile_invalid_coordinates():
    token = get_token("fpo_sonipat")
    # Lat outside India (ge=6.0, le=38.0)
    resp = client.patch(
        "/api/v1/producers/me",
        json={"lat": 45.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_patch_producer_member_farmers_rejected_for_farmer():
    # Individual farmer cannot specify member_farmers
    token = get_token("farmer_karnal")
    resp = client.patch(
        "/api/v1/producers/me",
        json={"member_farmers": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert any(d["field"] == "member_farmers" for d in data["error"]["details"])
