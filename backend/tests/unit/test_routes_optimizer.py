from app.modules.routes.distance import calculate_distance_matrix, calculate_duration_minutes
from app.modules.routes.optimizer import RouteOptimizer


def test_distance_matrix_and_duration():
    points = [(28.98, 77.03), (28.99, 77.02), (28.47, 77.05)]
    matrix = calculate_distance_matrix(points, circuity=1.35)
    assert len(matrix) == 3
    assert len(matrix[0]) == 3
    assert matrix[0][0] == 0.0
    assert matrix[0][1] > 0
    assert matrix[0][2] > 0

    duration = calculate_duration_minutes(60.0, speed_kmph=30.0, service_minutes=20.0)
    # 60 km at 30 km/h = 120 min + 20 min service = 140 min
    assert duration == 140


def test_optimizer_ac_rte_01_and_02_capacities_and_pairings():
    """Verify AC-RTE-01 (load never exceeds vehicle capacity) and AC-RTE-02 (pickup precedes drop on same vehicle)."""
    vehicles = [
        {
            "id": 1,
            "name": "PK-01",
            "vehicle_type": "PICKUP",
            "capacity_kg": 1500.0,
            "cost_per_km": 16.0,
            "fixed_cost_per_trip": 600.0,
            "avg_speed_kmph": 30.0,
            "depot_name": "Sonipat Depot",
            "depot_lat": 28.98,
            "depot_lng": 77.03,
        }
    ]
    orders = [
        {
            "order_id": 101,
            "crop_name": "Tomato",
            "quantity_kg": 600.0,
            "producer_name": "Farmer P1",
            "buyer_name": "Buyer B1",
            "pickup_lat": 28.99,
            "pickup_lng": 77.02,
            "delivery_lat": 28.47,
            "delivery_lng": 77.05,
            "baseline_cost": 2500.0,
        },
        {
            "order_id": 102,
            "crop_name": "Tomato",
            "quantity_kg": 500.0,
            "producer_name": "Farmer P2",
            "buyer_name": "Buyer B2",
            "pickup_lat": 28.95,
            "pickup_lng": 77.10,
            "delivery_lat": 28.50,
            "delivery_lng": 77.15,
            "baseline_cost": 2200.0,
        },
    ]

    optimizer = RouteOptimizer(orders=orders, vehicles=vehicles, time_limit_s=5)
    res = optimizer.solve()

    assert len(res["shipments"]) == 1
    shp = res["shipments"][0]
    # AC-RTE-01: Load never exceeds vehicle capacity
    for st in shp["stops"]:
        assert st["load_after_kg"] <= 1500.0

    # AC-RTE-02: For each order, pickup precedes drop
    order_stops = {}
    for st in shp["stops"]:
        oid = st["order_id"]
        if oid:
            if oid not in order_stops:
                order_stops[oid] = {}
            order_stops[oid][st["stop_type"]] = st["sequence"]

    for _oid, seqs in order_stops.items():
        assert "PICKUP" in seqs
        assert "DROP" in seqs
        assert seqs["PICKUP"] < seqs["DROP"]


def test_optimizer_ac_rte_05_oversized_load_unassigned():
    """Verify AC-RTE-05: Infeasible / oversized load is placed in unassigned rather than crashing."""
    vehicles = [
        {
            "id": 1,
            "name": "MT-01",
            "vehicle_type": "MINI_TRUCK",
            "capacity_kg": 750.0,
            "cost_per_km": 12.0,
            "fixed_cost_per_trip": 400.0,
            "avg_speed_kmph": 30.0,
            "depot_name": "Sonipat Depot",
            "depot_lat": 28.98,
            "depot_lng": 77.03,
        }
    ]
    # Order requires 2000 kg, vehicle capacity is only 750 kg
    orders = [
        {
            "order_id": 999,
            "crop_name": "Potato",
            "quantity_kg": 2000.0,
            "producer_name": "Farmer P1",
            "buyer_name": "Buyer B1",
            "pickup_lat": 28.99,
            "pickup_lng": 77.02,
            "delivery_lat": 28.47,
            "delivery_lng": 77.05,
            "baseline_cost": 4000.0,
        }
    ]

    optimizer = RouteOptimizer(orders=orders, vehicles=vehicles, time_limit_s=5)
    res = optimizer.solve()

    assert len(res["unassigned"]) == 1
    assert res["unassigned"][0]["order_id"] == 999
    assert res["unassigned"][0]["reason"] == "CAPACITY"
