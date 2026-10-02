import json
import time
from datetime import timedelta

import numpy as np
from fastapi.testclient import TestClient

from app.core.dates import today_ist
from app.main import create_app


def get_token(client: TestClient, persona: str) -> str:
    res = client.post("/api/v1/auth/demo-login", json={"persona": persona})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def measure_endpoint(client: TestClient, method: str, url: str, headers: dict = None, n: int = 50) -> dict:
    durations_ms = []
    for _ in range(n):
        t0 = time.perf_counter()
        if method == "GET":
            res = client.get(url, headers=headers)
        elif method == "POST":
            res = client.post(url, headers=headers)
        t1 = time.perf_counter()
        assert res.status_code in [200, 201], f"{url} returned {res.status_code}: {res.text}"
        durations_ms.append((t1 - t0) * 1000.0)

    return {
        "p50_ms": float(np.percentile(durations_ms, 50)),
        "p95_ms": float(np.percentile(durations_ms, 95)),
        "p99_ms": float(np.percentile(durations_ms, 99)),
        "min_ms": float(np.min(durations_ms)),
        "max_ms": float(np.max(durations_ms)),
        "mean_ms": float(np.mean(durations_ms)),
    }


def main():
    print("=" * 60)
    print("FASALSETU PHASE 12: BENCHMARK & DEMO VERIFICATION LOG")
    print("=" * 60)

    app = create_app()
    client = TestClient(app)

    op_token = get_token(client, "operator")
    fpo_token = get_token(client, "fpo_sonipat")
    buyer_token = get_token(client, "buyer_gurugram")

    # 1. Reset demo state
    print("\n[1] Resetting demo state...")
    reset_res = client.post("/api/v1/system/reset-demo", headers=auth_header(op_token))
    assert reset_res.status_code == 200
    print("Reset response counts:", reset_res.json()["counts"])

    # 2. Measure R1 candidates before live listing
    print("\n[2] Checking R1 before live listing...")
    r1_pre = client.get("/api/v1/matching/requirements/1/candidates", headers=auth_header(buyer_token)).json()
    r1_pre_status = r1_pre["fill_status"]
    r1_pre_count = len(r1_pre["candidates"])
    r1_pre_fulfilled = r1_pre["fulfilled_kg"]
    print(f"R1 pre-listing: fill_status={r1_pre_status}, count={r1_pre_count}, fulfilled={r1_pre_fulfilled} kg")

    # 3. Create live listing L15
    print("\n[3] Creating live listing L15 (Tomato A, 2000 kg, INR23.00)...")
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
    create_res = client.post("/api/v1/listings", json=listing_payload, headers=auth_header(fpo_token)).json()
    new_listing_id = create_res["listing"]["id"]
    print(f"Created listing ID={new_listing_id}, status={create_res['listing']['status']}")

    # 4. Check R1 candidates after live listing
    print("\n[4] Checking R1 candidates after live listing...")
    r1_post = client.get("/api/v1/matching/requirements/1/candidates", headers=auth_header(buyer_token)).json()
    rank1 = r1_post["candidates"][0]
    rank1_id = rank1["listing"]["id"]
    rank1_landed = rank1["landed_price_per_kg"]
    r1_post_fill = r1_post["fill_status"]
    print(f"R1 rank-1 listing ID: {rank1_id}, fill_status={r1_post_fill}, landed={rank1_landed} INR/kg")

    # 5. Accept allocation
    print("\n[5] Accepting allocation for R1...")
    accept_res = client.post(
        "/api/v1/matching/accept",
        json={
            "requirement_id": 1,
            "allocations": r1_post["allocations"],
            "delivery_date": str(today_ist() + timedelta(days=1)),
        },
        headers=auth_header(buyer_token),
    ).json()
    created_order_id = accept_res["orders"][0]["id"]
    print(f"Order created ID={created_order_id}, status={accept_res['orders'][0]['status']}")

    # 6. Confirm order
    print("\n[6] Confirming order...")
    conf_res = client.post(
        f"/api/v1/orders/{created_order_id}/transition",
        json={"to_status": "CONFIRMED", "notes": "Demo confirmed"},
        headers=auth_header(op_token),
    ).json()
    print(f"Order status now: {conf_res['status']}")

    # 7. Optimize routes
    print("\n[7] Optimizing routes for confirmed pool...")
    t0_opt = time.perf_counter()
    opt_res = client.post(
        "/api/v1/routes/optimize",
        json={"time_limit_s": 5},
        headers=auth_header(op_token),
    ).json()
    t1_opt = time.perf_counter()
    opt_solve_time_s = t1_opt - t0_opt
    plan_id = opt_res["plan_id"]
    method = opt_res["method"]
    totals = opt_res["totals"]
    print(f"Plan ID={plan_id}, method={method}, solve_time={opt_solve_time_s:.2f}s, vehicles_used={totals['vehicles_used']}")
    print(f"Optimized km={totals['optimized_km']:.1f}, baseline km={totals['baseline_km']:.1f}")
    print(f"Optimized cost=INR{totals['optimized_cost']:.2f}, baseline cost=INR{totals['baseline_cost']:.2f}")

    # 8. Approve plan
    print("\n[8] Approving plan...")
    appr_res = client.post(f"/api/v1/routes/plans/{plan_id}/approve", headers=auth_header(op_token)).json()
    print(f"Plan status: {appr_res['plan']['status']}, shipments: {len(appr_res['shipments'])}")

    # 9. Price breakdown
    print("\n[9] Inspecting price breakdown for new order...")
    price_res = client.get(f"/api/v1/pricing/breakdown?order_id={created_order_id}", headers=auth_header(op_token)).json()
    per_kg = price_res["per_kg"]
    print(f"Waterfall (INR/kg): farmgate={per_kg['farmgate']:.2f} / transport={per_kg['transport']:.2f} / fee={per_kg['platform_fee']:.2f} / landed={per_kg['landed']:.2f}")

    # 10. Model card
    print("\n[10] Model card metrics...")
    model_res = client.get("/api/v1/forecasts/model-info").json()
    deployed_method = model_res["deployed_method"]
    val_mae = model_res["metrics"]["validation"]["lgbm"]["mae"]
    test_mae = model_res["metrics"]["test"]["lgbm"]["mae"]
    b2_test_mae = model_res["metrics"]["test"]["b1_seasonal_naive"]["mae"]
    print(f"Deployed: {deployed_method}, Val MAE: {val_mae:.2f}, Test MAE: {test_mae:.2f} (B1 Seasonal Naive: {b2_test_mae:.2f})")

    # 11. Analytics KPIs
    print("\n[11] Analytics overview KPIs...")
    anl_res = client.get("/api/v1/analytics/overview", headers=auth_header(op_token)).json()
    kpis = anl_res["kpis"]
    print(f"Committed orders: {kpis['committed_orders']}")
    print(f"Committed volume: {kpis['committed_volume_kg']} kg")
    print(f"Committed value: INR{kpis['committed_value_inr']}")
    print(f"Fill rate: {kpis['requirement_fill_rate_pct']}%")
    print(f"Route savings: {kpis['route_savings_km']:.1f} km, INR{kpis['route_savings_inr']:.2f}")

    # 12. Latency Benchmarking across 50 requests
    print("\n[12] Running NFR latency benchmarks (50 iterations each)...")
    benchmarks = {}
    benchmarks["GET /health"] = measure_endpoint(client, "GET", "/api/v1/health")
    benchmarks["GET /reference"] = measure_endpoint(client, "GET", "/api/v1/reference")
    benchmarks["GET /listings"] = measure_endpoint(client, "GET", "/api/v1/listings?limit=50", auth_header(buyer_token))
    benchmarks["GET /listings/1"] = measure_endpoint(client, "GET", "/api/v1/listings/1", auth_header(buyer_token))
    benchmarks["GET /requirements"] = measure_endpoint(client, "GET", "/api/v1/requirements?limit=50", auth_header(buyer_token))
    benchmarks["GET /forecasts/demand"] = measure_endpoint(client, "GET", "/api/v1/forecasts/demand?hub_id=1&crop_id=1")
    benchmarks["GET /matching/candidates"] = measure_endpoint(client, "GET", "/api/v1/matching/requirements/4/candidates", auth_header(op_token))
    benchmarks["GET /pricing/breakdown"] = measure_endpoint(client, "GET", f"/api/v1/pricing/breakdown?order_id={created_order_id}", auth_header(op_token))
    benchmarks["GET /analytics/overview"] = measure_endpoint(client, "GET", "/api/v1/analytics/overview", auth_header(op_token))
    benchmarks["GET /analytics/supply-demand"] = measure_endpoint(client, "GET", "/api/v1/analytics/supply-demand", auth_header(op_token))

    print("\nLatency Benchmark Results:")
    print(f"{'Endpoint':<35} | {'p50 (ms)':<10} | {'p95 (ms)':<10} | {'Target (PRD §15)'}")
    print("-" * 75)
    for ep, stats in benchmarks.items():
        target = "< 300 ms" if "forecast" in ep else "< 500 ms"
        print(f"{ep:<35} | {stats['p50_ms']:<10.2f} | {stats['p95_ms']:<10.2f} | {target}")

    # Reset again to leave clean state
    print("\nResetting demo state to clean baseline...")
    client.post("/api/v1/system/reset-demo", headers=auth_header(op_token))
    print("Done!")

    # Dump full json log for documentation
    output_data = {
        "r1_pre": {
            "fill_status": r1_pre_status,
            "count": r1_pre_count,
            "fulfilled_kg": r1_pre_fulfilled,
        },
        "r1_post": {
            "rank1_id": rank1_id,
            "fill_status": r1_post_fill,
            "landed_price_per_kg": rank1_landed,
        },
        "plan": {
            "method": method,
            "solve_time_s": round(opt_solve_time_s, 2),
            "vehicles_used": totals["vehicles_used"],
            "optimized_km": totals["optimized_km"],
            "baseline_km": totals["baseline_km"],
            "optimized_cost": totals["optimized_cost"],
            "baseline_cost": totals["baseline_cost"],
            "savings_cost": totals["savings_cost"],
            "savings_pct_cost": totals["savings_pct_cost"],
        },
        "waterfall": {
            "farmgate": per_kg["farmgate"],
            "transport": per_kg["transport"],
            "fee": per_kg["platform_fee"],
            "landed": per_kg["landed"],
        },
        "model_card": {
            "deployed_method": deployed_method,
            "val_mae": val_mae,
            "test_mae": test_mae,
            "baseline_seasonal_naive_mae": b2_test_mae,
        },
        "analytics": kpis,
        "benchmarks": benchmarks,
    }

    with open("scripts/benchmark_results.json", "w") as f:
        json.dump(output_data, f, indent=2)
    print("Benchmark results saved to scripts/benchmark_results.json")


if __name__ == "__main__":
    main()
