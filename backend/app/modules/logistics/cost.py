import math
from typing import Any


class NoVehicleAvailableException(Exception):
    pass


def select_vehicles(
    quantity_kg: float, vehicle_types: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Select vehicle allocation for a given quantity in kg.

    Rule (ML.md §11):
    - If q <= max_cap: smallest vehicle type with capacity >= q (1 trip).
    - Else: n_full = floor(q / max_cap) trips of the largest type +
      (if remainder r > 0: smallest type with capacity >= r).
    """
    if not vehicle_types:
        raise NoVehicleAvailableException(
            "No vehicles available in fleet configuration."
        )

    sorted_types = sorted(vehicle_types, key=lambda v: v["capacity_kg"])
    max_vehicle = sorted_types[-1]
    max_cap = max_vehicle["capacity_kg"]

    plan: list[dict[str, Any]] = []

    if quantity_kg <= max_cap:
        for v in sorted_types:
            if v["capacity_kg"] >= quantity_kg:
                plan.append(
                    {
                        "vehicle_type": v["vehicle_type"],
                        "capacity_kg": v["capacity_kg"],
                        "cost_per_km": v["cost_per_km"],
                        "fixed_cost_per_trip": v["fixed_cost_per_trip"],
                        "load_kg": round(quantity_kg, 1),
                        "trips": 1,
                    }
                )
                break
    else:
        n_full = math.floor(quantity_kg / max_cap)
        if n_full > 0:
            plan.append(
                {
                    "vehicle_type": max_vehicle["vehicle_type"],
                    "capacity_kg": max_vehicle["capacity_kg"],
                    "cost_per_km": max_vehicle["cost_per_km"],
                    "fixed_cost_per_trip": max_vehicle["fixed_cost_per_trip"],
                    "load_kg": float(max_cap),
                    "trips": n_full,
                }
            )
        remainder = round(quantity_kg - (n_full * max_cap), 1)
        if remainder > 0:
            for v in sorted_types:
                if v["capacity_kg"] >= remainder:
                    plan.append(
                        {
                            "vehicle_type": v["vehicle_type"],
                            "capacity_kg": v["capacity_kg"],
                            "cost_per_km": v["cost_per_km"],
                            "fixed_cost_per_trip": v["fixed_cost_per_trip"],
                            "load_kg": remainder,
                            "trips": 1,
                        }
                    )
                    break

    return plan


def estimate_dedicated_trip(
    distance_km: float,
    quantity_kg: float,
    vehicle_types: list[dict[str, Any]],
    return_leg_factor: float = 2.0,
    avg_speed_kmph: float = 30.0,
    service_minutes_per_stop: float = 20.0,
    distance_source: str = "ESTIMATED_HAVERSINE",
) -> dict[str, Any]:
    """Calculate dedicated-trip transport cost and time per ML.md §11."""
    if quantity_kg <= 0:
        raise ValueError("Quantity must be greater than zero.")

    plan = select_vehicles(quantity_kg, vehicle_types)

    total_cost = 0.0
    total_trips = 0

    formatted_plan = []
    for leg in plan:
        trip_cost = leg["fixed_cost_per_trip"] + (
            leg["cost_per_km"] * distance_km * return_leg_factor
        )
        total_for_leg = trip_cost * leg["trips"]
        total_cost += total_for_leg
        total_trips += leg["trips"]
        formatted_plan.append(
            {
                "vehicle_type": leg["vehicle_type"],
                "capacity_kg": leg["capacity_kg"],
                "load_kg": leg["load_kg"],
                "trips": leg["trips"],
                "trip_cost": round(trip_cost, 2),
                "total_cost": round(total_for_leg, 2),
            }
        )

    cost_per_kg = round(total_cost / quantity_kg, 2)
    # Transit hours = distance / speed + (2 * service_minutes) / 60
    transit_hours = round(
        (distance_km / avg_speed_kmph) + ((2.0 * service_minutes_per_stop) / 60.0), 2
    )

    return {
        "distance_km": round(distance_km, 2),
        "distance_source": distance_source,
        "vehicle_plan": formatted_plan,
        "trips": total_trips,
        "cost_total": round(total_cost, 2),
        "cost_per_kg": cost_per_kg,
        "transit_hours": transit_hours,
        "basis": "ESTIMATE",
    }
