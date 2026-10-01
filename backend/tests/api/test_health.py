from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check_returns_ok():
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] in ["ok", "error"]
    assert "model" in data
    assert isinstance(data["model"]["loaded"], bool)
    assert "demo_mode" in data
    assert data["version"] == "0.1.0"
