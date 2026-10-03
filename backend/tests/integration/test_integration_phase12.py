from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.dates import today_ist
from app.main import create_app

settings = get_settings()



def get_token(client: TestClient, persona: str) -> str:
    res = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_demo_reset_endpoint_authorization_and_modes():
    """Verify AC-AUTH-03, AC-AUTH-04, AC-SYS-02 on POST /system/reset-demo."""
    app = create_app()
    client = TestClient(app)

    # 1. Unauthenticated -> 401 UNAUTHENTICATED
    res_unauth = client.post("/api/v1/system/reset-demo")
    assert res_unauth.status_code == 401
    assert res_unauth.json()["error"]["code"] == "UNAUTHENTICATED"

    # 2. Non-operator persona (buyer) -> 403 FORBIDDEN
    buyer_token = get_token(client, "buyer_gurugram")
    res_buyer = client.post("/api/v1/system/reset-demo", headers=auth_header(buyer_token))
    assert res_buyer.status_code == 403
    assert res_buyer.json()["error"]["code"] == "FORBIDDEN"

    # 3. Non-operator persona (farmer) -> 403 FORBIDDEN
    farmer_token = get_token(client, "farmer_karnal")
    res_farmer = client.post("/api/v1/system/reset-demo", headers=auth_header(farmer_token))
    assert res_farmer.status_code == 403
    assert res_farmer.json()["error"]["code"] == "FORBIDDEN"

    # 4. Operator persona -> 200 with counts and reset status
    op_token = get_token(client, "operator")
    res_op = client.post("/api/v1/system/reset-demo", headers=auth_header(op_token))
    assert res_op.status_code == 200, res_op.text
    data = res_op.json()
    assert data["status"] == "reset"
    assert "counts" in data
    counts = data["counts"]
    assert counts.get("crops") == 5
    assert counts.get("hubs") == 5
    assert counts.get("listings") == 14
    assert counts.get("requirements") == 8
    assert counts.get("orders") == 10

    # 5. Alias endpoint /system/reset-demo without /api/v1
    res_alias = client.post("/system/reset-demo", headers=auth_header(op_token))
    assert res_alias.status_code == 200
    assert res_alias.json()["status"] == "reset"

    # 6. DEMO_MODE=False -> 404 DEMO_DISABLED
    try:
        settings.DEMO_MODE = False
        res_disabled = client.post("/api/v1/system/reset-demo", headers=auth_header(op_token))
        assert res_disabled.status_code == 404
        assert res_disabled.json()["error"]["code"] == "DEMO_DISABLED"
    finally:
        settings.DEMO_MODE = True

    # 7. In production with ALLOW_DEMO_RESET=False -> 404 DEMO_DISABLED
    try:
        settings.APP_ENV = "production"
        settings.ALLOW_DEMO_RESET = False
        res_prod_disabled = client.post("/api/v1/system/reset-demo", headers=auth_header(op_token))
        assert res_prod_disabled.status_code == 404
        assert res_prod_disabled.json()["error"]["code"] == "DEMO_DISABLED"

        # 8. In production, operator demo-login is blocked -> 403 FORBIDDEN (F-11b)
        res_op_demo_login = client.post("/api/v1/auth/demo-login", json={"persona": "operator"})
        assert res_op_demo_login.status_code == 403
        assert res_op_demo_login.json()["error"]["code"] == "FORBIDDEN"
    finally:
        settings.APP_ENV = "dev"
        settings.ALLOW_DEMO_RESET = True


def test_full_demo_script_and_zero_drift_idempotency():
    """Verify AC-INT-01, AC-INT-02, AC-INT-03:

    Executes the authoritative Demo.md §4 path end-to-end:
    PREDICT -> MATCH -> MOVE -> SELL -> ANALYSE
    Then resets and runs the entire path a second time to prove zero-drift idempotency.
    """
    app = create_app()
    client = TestClient(app)

    op_token = get_token(client, "operator")
    fpo_token = get_token(client, "fpo_sonipat")
    buyer_token = get_token(client, "buyer_gurugram")

    # Repeat the entire demo flow twice from fresh resets
    for _run_iteration in [1, 2]:
        # 1. Reset demo state
        reset_res = client.post("/api/v1/system/reset-demo", headers=auth_header(op_token))
        assert reset_res.status_code == 200
        assert reset_res.json()["counts"]["listings"] == 14
        assert reset_res.json()["counts"]["requirements"] == 8

        # 2. Check R1 candidates prior to live listing (illustrates initial partial/tight supply)
        # R1: Gurugram Restaurant Group, Tomato, 1,500 kg, max landed ₹29.00
        r1_pre = client.get("/api/v1/matching/requirements/1/candidates", headers=auth_header(buyer_token))
        assert r1_pre.status_code == 200, r1_pre.text
        pre_data = r1_pre.json()
        assert pre_data["fill_status"] in ["PARTIAL", "NONE"]
        assert pre_data["fulfilled_kg"] < 1500.0

        # 3. PREDICT: FPO Sonipat checks demand forecast and hub comparison
        hub_rank_res = client.get(
            "/api/v1/forecasts/hubs",
            headers=auth_header(fpo_token),
            params={"crop_id": 1},
        )
        assert hub_rank_res.status_code == 200, hub_rank_res.text
        hub_rank_data = hub_rank_res.json()
        assert len(hub_rank_data["hubs"]) > 0

        # 4. FPO Sonipat publishes live listing (Demo.md §3)
        # Tomato, Grade A, 2,000 kg, ₹23.00/kg, min order 200 kg, harvest today, available today -> today+3
        listing_payload = {
            "crop_id": 1,
            "variety": "Hybrid",
            "grade": "A",
            "quantity_kg": 2000.0,
            "ask_price_per_kg": 23.00,
            "min_order_kg": 200.0,
            "harvest_date": str(today_ist()),
            "available_from": str(today_ist()),
            "available_until": str(today_ist() + timedelta(days=3)),
        }
        create_res = client.post("/api/v1/listings", json=listing_payload, headers=auth_header(fpo_token))
        assert create_res.status_code == 201, create_res.text
        listing_data = create_res.json()["listing"]
        new_listing_id = listing_data["id"]
        assert listing_data["status"] == "ACTIVE"
        assert listing_data["quantity_available_kg"] == 2000.0

        # 5. MATCH: Buyer Gurugram checks R1 matches again
        r1_post = client.get("/api/v1/matching/requirements/1/candidates", headers=auth_header(buyer_token))
        assert r1_post.status_code == 200, r1_post.text
        post_data = r1_post.json()
        assert len(post_data["candidates"]) > 0
        rank1 = post_data["candidates"][0]

        # Assert rank 1 is the new Sonipat listing
        assert rank1["listing"]["id"] == new_listing_id
        assert rank1["rank"] == 1
        assert rank1["distance_km"] < 100.0  # ~78 km road estimate
        assert post_data["fill_status"] == "FULL"
        assert post_data["fulfilled_kg"] == 1500.0
        assert rank1["landed_price_per_kg"] <= 29.00

        # 6. Accept allocation
        accept_payload = {
            "requirement_id": 1,
            "allocations": post_data["allocations"],
            "delivery_date": str(today_ist() + timedelta(days=1)),
        }
        accept_res = client.post(
            "/api/v1/matching/accept",
            json=accept_payload,
            headers=auth_header(buyer_token),
        )
        assert accept_res.status_code == 201, accept_res.text
        order_info = accept_res.json()["orders"][0]
        created_order_id = order_info["id"]
        assert order_info["status"] == "PLACED"
        assert order_info["quantity_kg"] == 1500.0

        # Verify listing available quantity decremented to 500 kg
        l_res = client.get(f"/api/v1/listings/{new_listing_id}", headers=auth_header(buyer_token))
        assert l_res.status_code == 200
        assert l_res.json()["listing"]["quantity_available_kg"] == 500.0

        # 7. Operator confirms order
        confirm_res = client.post(
            f"/api/v1/orders/{created_order_id}/transition",
            json={"to_status": "CONFIRMED", "notes": "Confirmed by operator for demo dispatch"},
            headers=auth_header(op_token),
        )
        assert confirm_res.status_code == 200, confirm_res.text
        assert confirm_res.json()["status"] == "CONFIRMED"

        # 8. MOVE: Operator optimizes routes for all confirmed unrouted orders
        opt_res = client.post(
            "/api/v1/routes/optimize",
            json={"time_limit_s": 5},
            headers=auth_header(op_token),
        )
        assert opt_res.status_code == 201, opt_res.text
        plan_data = opt_res.json()
        assert plan_data["status"] == "PROPOSED"
        plan_id = plan_data["plan_id"]
        assert plan_data["totals"]["vehicles_used"] >= 1
        assert plan_data["totals"]["optimized_km"] > 0
        assert plan_data["totals"]["baseline_km"] >= plan_data["totals"]["optimized_km"]

        # 9. Operator approves route plan
        appr_res = client.post(
            f"/api/v1/routes/plans/{plan_id}/approve",
            headers=auth_header(op_token),
        )
        assert appr_res.status_code == 200, appr_res.text
        appr_data = appr_res.json()
        assert appr_data["plan"]["status"] == "APPROVED"
        assert len(appr_data["shipments"]) > 0

        # Verify order has allocated transport cost populated
        order_res = client.get(f"/api/v1/orders/{created_order_id}", headers=auth_header(op_token))
        assert order_res.status_code == 200
        assert order_res.json()["allocated_transport_cost_total"] is not None
        assert float(order_res.json()["allocated_transport_cost_total"]) > 0

        # 10. SELL: Verify price waterfall breakdown
        price_res = client.get(
            f"/api/v1/pricing/breakdown?order_id={created_order_id}",
            headers=auth_header(op_token),
        )
        assert price_res.status_code == 200, price_res.text
        price_data = price_res.json()
        per_kg = price_data["per_kg"]
        assert per_kg["farmgate"] == 23.00
        assert per_kg["platform_fee"] == round(23.00 * 0.02, 2)
        expected_landed = round(per_kg["farmgate"] + per_kg["transport"] + per_kg["platform_fee"], 2)
        assert abs(per_kg["landed"] - expected_landed) <= 0.02
        assert price_data["benchmark"]["modal_price_per_kg"] > 0
        assert price_data["scenario"]["farmer_mandi_net_per_kg"] > 0
        assert price_data["scenario"]["buyer_traditional_per_kg"] > 0
        assert price_data["transport_basis"] in ["ESTIMATE", "ALLOCATED_ROUTE"]

        # 11. ANALYSE: Verify Analytics updated with committed orders and route savings
        anl_res = client.get("/api/v1/analytics/overview", headers=auth_header(op_token))
        assert anl_res.status_code == 200, anl_res.text
        anl_data = anl_res.json()
        kpis = anl_data["kpis"]
        assert kpis["committed_orders"] >= 11  # 10 seeded + 1 live demo
        assert kpis["committed_volume_kg"] >= 7850.0
        assert kpis["route_savings_inr"] is not None
        assert kpis["route_savings_km"] is not None

        # Verify supply-demand matrix returns 25 cells (5 crops x 5 hubs)
        mat_res = client.get("/api/v1/analytics/supply-demand", headers=auth_header(op_token))
        assert mat_res.status_code == 200, mat_res.text
        mat_data = mat_res.json()
        assert len(mat_data["rows"]) == 25


def test_edge_cases_and_near_misses_from_demo():
    """Verify Demo.md §5 edge cases:

    - R3 (Cauliflower 1000 kg) -> PARTIAL with shortfall
    - R8 (Tomato A 2500 kg @ ₹22) -> NONE with near-miss over budget
    - R2 (Onion 6500 kg) -> Multi-source allocation
    """
    app = create_app()
    client = TestClient(app)
    op_token = get_token(client, "operator")
    client.post("/api/v1/system/reset-demo", headers=auth_header(op_token))

    buyer_token = get_token(client, "buyer_noida")

    # 1. R3: Cauliflower 1,000 kg (id=3)
    r3_res = client.get("/api/v1/matching/requirements/3/candidates", headers=auth_header(buyer_token))
    assert r3_res.status_code == 200
    r3_data = r3_res.json()
    assert r3_data["fill_status"] == "PARTIAL"
    assert r3_data["shortfall_kg"] > 0

    # 2. R8: Tomato A, 2,500 kg, ₹22.00 max landed (id=8) -> NONE with near-miss over budget
    r8_res = client.get("/api/v1/matching/requirements/8/candidates", headers=auth_header(op_token))
    assert r8_res.status_code == 200
    r8_data = r8_res.json()
    assert r8_data["fill_status"] == "NONE"
    assert len(r8_data["near_misses"]) > 0
    assert any(nm["excluded_reason"] == "BUDGET" for nm in r8_data["near_misses"])

    # 3. R2: Onion 6,500 kg (id=2) -> MULTI source allocation
    r2_res = client.get("/api/v1/matching/requirements/2/candidates", headers=auth_header(op_token))
    assert r2_res.status_code == 200
    r2_data = r2_res.json()
    assert r2_data["fill_status"] in ["FULL", "PARTIAL"]
    assert len(r2_data["allocations"]) >= 2



def test_object_level_security_regression():
    """Verify AC-SEC-03:

    - Producer A cannot PATCH Producer B's listing
    - Buyer A cannot read Buyer B's requirement
    - Buyer A cannot read Buyer B's order
    """
    app = create_app()
    client = TestClient(app)
    farmer_karnal_token = get_token(client, "farmer_karnal")
    buyer_gurugram_token = get_token(client, "buyer_gurugram")
    buyer_noida_token = get_token(client, "buyer_noida")

    # L1 belongs to P1 (Sonipat). Farmer Karnal (P3) attempts to PATCH -> 403
    patch_res = client.patch(
        "/api/v1/listings/1",
        json={"ask_price_per_kg": 99.00},
        headers=auth_header(farmer_karnal_token),
    )
    assert patch_res.status_code == 403
    assert patch_res.json()["error"]["code"] == "FORBIDDEN"

    # R1 belongs to Buyer B1 (Gurugram). Buyer B2 (Noida) attempts to GET -> 403
    r_res = client.get("/api/v1/requirements/1", headers=auth_header(buyer_noida_token))
    assert r_res.status_code == 403
    assert r_res.json()["error"]["code"] == "FORBIDDEN"

    # O1 belongs to Buyer B5. Buyer Gurugram (B1) attempts to GET -> 403
    o_res = client.get("/api/v1/orders/1", headers=auth_header(buyer_gurugram_token))
    assert o_res.status_code == 403
    assert o_res.json()["error"]["code"] == "FORBIDDEN"


def test_concurrent_order_reservation_no_oversell():
    """Verify AC-ORD-04 under real multi-threaded concurrency contention.

    Create a listing with 500 kg available.
    Spawn 5 concurrent threads each trying to buy 200 kg.
    Verify: exactly 2 succeed (400 kg reserved), 3 fail with insufficient quantity (409 Conflict),
    and available quantity remains exactly 100 kg with zero oversell.
    """
    from concurrent.futures import ThreadPoolExecutor

    app = create_app()
    client = TestClient(app)
    fpo_token = get_token(client, "fpo_sonipat")
    buyer_token = get_token(client, "buyer_gurugram")
    today = today_ist()

    # 1. Create a fresh listing with 500 kg
    lst_res = client.post(
        "/api/v1/listings",
        headers=auth_header(fpo_token),
        json={
            "crop_id": 1,
            "grade": "A",
            "quantity_kg": 500.0,
            "ask_price_per_kg": 25.0,
            "min_order_kg": 50.0,
            "harvest_date": today.isoformat(),
            "available_from": today.isoformat(),
            "available_until": (today + timedelta(days=3)).isoformat(),
        },
    )
    assert lst_res.status_code == 201
    listing_id = lst_res.json()["listing"]["id"]

    # 2. Concurrently attempt 5 orders of 200 kg each
    def place_order(_i):
        c = TestClient(app)
        return c.post(
            "/api/v1/orders",
            headers=auth_header(buyer_token),
            json={
                "listing_id": listing_id,
                "quantity_kg": 200.0,
                "delivery_date": today.isoformat(),
            },
        )

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(place_order, i) for i in range(5)]
        results = [f.result() for f in futures]

    successes = [r for r in results if r.status_code == 201]
    failures = [r for r in results if r.status_code == 409]

    assert len(successes) == 2, f"Expected exactly 2 successes, got {len(successes)}"
    assert len(failures) == 3, f"Expected 3 failures, got {len(failures)}"
    for f in failures:
        assert f.json()["error"]["code"] == "INSUFFICIENT_QUANTITY"

    # 3. Check final listing quantity: exactly 100 kg remains
    check_res = client.get(f"/api/v1/listings/{listing_id}", headers=auth_header(buyer_token))
    assert check_res.status_code == 200
    assert check_res.json()["listing"]["quantity_available_kg"] == 100.0

