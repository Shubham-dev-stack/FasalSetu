from fastapi.testclient import TestClient

from app.main import create_app


def get_buyer_token(client: TestClient, persona: str = "buyer_gurugram") -> str:
    res = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_marketplace_browse_and_landed_estimate():
    app = create_app()
    client = TestClient(app)

    token = get_buyer_token(client, "buyer_gurugram")
    headers = {"Authorization": f"Bearer {token}"}

    # Query listings as buyer_gurugram (has buyer_profile with lat/lng)
    res = client.get("/api/v1/listings", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] > 0

    # Verify landed estimate is present for buyer callers (AC-MKT-02)
    first_item = data["items"][0]
    est = first_item.get("landed_estimate")
    assert est is not None
    assert est["distance_km"] > 0
    assert est["transport_cost_per_kg"] > 0
    assert est["platform_fee_per_kg"] >= 0
    expected_landed = round(
        first_item["ask_price_per_kg"]
        + est["transport_cost_per_kg"]
        + est["platform_fee_per_kg"],
        2,
    )
    assert abs(est["landed_price_per_kg"] - expected_landed) <= 0.01


def test_marketplace_filters_and_sorting():
    app = create_app()
    client = TestClient(app)

    # 1. Filter by crop Tomato (crop_id=1)
    res = client.get("/api/v1/listings?crop_id=1")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["crop"]["id"] == 1
        assert item["crop"]["name"] == "Tomato"

    # 2. Filter by grade_min=A
    res = client.get("/api/v1/listings?grade_min=A")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["grade"] == "A"

    # 3. Filter by state (e.g. Haryana)
    res = client.get("/api/v1/listings?state=Haryana")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert "Haryana" in item["producer"]["state"]

    # 4. Filter by max_price
    res = client.get("/api/v1/listings?max_price=22.00")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["ask_price_per_kg"] <= 22.00

    # 5. Sorting by price asc
    res = client.get("/api/v1/listings?sort=price")
    assert res.status_code == 200
    items = res.json()["items"]
    prices = [i["ask_price_per_kg"] for i in items]
    assert prices == sorted(prices)

    # 6. Sorting by freshness (harvest_date desc)
    res = client.get("/api/v1/listings?sort=freshness")
    assert res.status_code == 200
    items = res.json()["items"]
    dates = [i["harvest_date"] for i in items]
    assert dates == sorted(dates, reverse=True)


def test_marketplace_empty_results():
    app = create_app()
    client = TestClient(app)

    # Query with impossible max price
    res = client.get("/api/v1/listings?max_price=1.00")
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_listing_detail_with_landed_estimate():
    app = create_app()
    client = TestClient(app)

    token = get_buyer_token(client, "buyer_gurugram")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/listings/1", headers=headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["listing"]["id"] == 1
    est = detail["listing"]["landed_estimate"]
    assert est is not None
    assert est["distance_km"] > 0
    assert est["transport_cost_per_kg"] > 0
