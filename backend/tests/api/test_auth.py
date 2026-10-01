from fastapi.testclient import TestClient

from app.main import create_app

app = create_app()
client = TestClient(app)


def test_login_success():
    # AC-AUTH-01
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "fpo_sonipat@demo.fasalsetu.local",
            "password": "demo1234",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "PRODUCER"
    assert data["user"]["email"] == "fpo_sonipat@demo.fasalsetu.local"


def test_login_invalid_password_returns_401():
    # AC-AUTH-02: Wrong password
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "fpo_sonipat@demo.fasalsetu.local",
            "password": "wrongpassword",
        },
    )
    assert resp.status_code == 401
    data = resp.json()
    assert data["error"]["code"] == "UNAUTHENTICATED"
    assert data["error"]["message"] == "Invalid email or password."


def test_login_unknown_email_returns_401():
    # AC-AUTH-02: Unknown email produces identical message
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unknown_email@demo.fasalsetu.local",
            "password": "demo1234",
        },
    )
    assert resp.status_code == 401
    data = resp.json()
    assert data["error"]["code"] == "UNAUTHENTICATED"
    assert data["error"]["message"] == "Invalid email or password."


def test_demo_login_success():
    # AC-AUTH-04
    for persona in [
        "fpo_sonipat",
        "fpo_meerut",
        "farmer_karnal",
        "buyer_gurugram",
        "buyer_noida",
        "operator",
    ]:
        resp = client.post("/api/v1/auth/demo-login", json={"persona": persona})
        assert resp.status_code == 200
        assert "access_token" in resp.json()


def test_demo_login_invalid_persona_returns_422():
    resp = client.post(
        "/api/v1/auth/demo-login", json={"persona": "invalid_persona_xyz"}
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_get_me_authenticated():
    login_resp = client.post("/api/v1/auth/demo-login", json={"persona": "fpo_sonipat"})
    token = login_resp.json()["access_token"]

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "fpo_sonipat@demo.fasalsetu.local"


def test_get_me_unauthenticated_returns_401():
    # AC-AUTH-03
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_register_producer_success():
    import uuid
    rand_email = f"new_producer_{uuid.uuid4().hex[:8]}@fasalsetu.local"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": rand_email,
            "password": "validPassword123",
            "role": "PRODUCER",
            "display_name": "New Test Producer",
            "profile": {
                "producer_type": "FARMER",
                "org_name": "Test Farm",
                "lat": 28.50,
                "lng": 77.10,
            },
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == rand_email
    assert data["user"]["role"] == "PRODUCER"


def test_register_duplicate_email_returns_409():
    import uuid
    rand_email = f"duplicate_{uuid.uuid4().hex[:8]}@fasalsetu.local"
    payload = {
        "email": rand_email,
        "password": "validPassword123",
        "role": "PRODUCER",
        "display_name": "Duplicate Test",
        "profile": {
            "producer_type": "FARMER",
            "org_name": "Duplicate Farm",
            "lat": 28.50,
            "lng": 77.10,
        },
    }
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201
    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["code"] == "CONFLICT"
