import pytest

from app.modules.logistics.cost import (
    NoVehicleAvailableException,
    estimate_dedicated_trip,
    select_vehicles,
)

SAMPLE_VEHICLES = [
    {
        "vehicle_type": "MINI_TRUCK",
        "capacity_kg": 750.0,
        "cost_per_km": 12.0,
        "fixed_cost_per_trip": 400.0,
    },
    {
        "vehicle_type": "PICKUP",
        "capacity_kg": 1500.0,
        "cost_per_km": 16.0,
        "fixed_cost_per_trip": 600.0,
    },
    {
        "vehicle_type": "MEDIUM_TRUCK",
        "capacity_kg": 4000.0,
        "cost_per_km": 26.0,
        "fixed_cost_per_trip": 1200.0,
    },
]


def test_select_vehicles_small_load():
    # AC-LOG-02: 500 kg fits in MINI_TRUCK (750 kg)
    plan = select_vehicles(500.0, SAMPLE_VEHICLES)
    assert len(plan) == 1
    assert plan[0]["vehicle_type"] == "MINI_TRUCK"
    assert plan[0]["trips"] == 1


def test_select_vehicles_pickup_load():
    # 1200 kg requires PICKUP (1500 kg)
    plan = select_vehicles(1200.0, SAMPLE_VEHICLES)
    assert len(plan) == 1
    assert plan[0]["vehicle_type"] == "PICKUP"
    assert plan[0]["trips"] == 1


def test_select_vehicles_oversize_load():
    # AC-LOG-03: 5500 kg -> 1 MEDIUM_TRUCK (4000) + 1 PICKUP (1500)
    plan = select_vehicles(5500.0, SAMPLE_VEHICLES)
    assert len(plan) == 2
    assert plan[0]["vehicle_type"] == "MEDIUM_TRUCK"
    assert plan[0]["trips"] == 1
    assert plan[1]["vehicle_type"] == "PICKUP"
    assert plan[1]["trips"] == 1


def test_estimate_dedicated_trip_cost():
    # AC-LOG-04: Distance 78 km, load 1500 kg (PICKUP)
    # Trip cost = 600 + (16 * 78 * 2.0) = 600 + 2496 = 3096.0
    res = estimate_dedicated_trip(
        distance_km=78.0,
        quantity_kg=1500.0,
        vehicle_types=SAMPLE_VEHICLES,
        return_leg_factor=2.0,
    )
    assert res["cost_total"] == 3096.0
    assert res["cost_per_kg"] == round(3096.0 / 1500.0, 2)
    assert res["basis"] == "ESTIMATE"


def test_no_vehicles_available_raises():
    # AC-LOG-05
    with pytest.raises(NoVehicleAvailableException):
        select_vehicles(100.0, [])
