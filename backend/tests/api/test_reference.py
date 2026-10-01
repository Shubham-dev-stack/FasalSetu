from fastapi.testclient import TestClient

from app.main import create_app

app = create_app()
client = TestClient(app)


def test_get_reference_endpoint():
    resp = client.get("/api/v1/reference")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["crops"]) == 5
    assert len(data["hubs"]) == 5
    assert "grades" in data["enums"]
    assert "public_config" in data
    assert data["public_config"]["platform_fee_pct"] == 2.0
