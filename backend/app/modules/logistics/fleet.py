from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Vehicle


def get_vehicle_types(db: Session) -> list[dict[str, Any]]:
    """Load available vehicle types from DB, falling back to config defaults."""
    vehicles = db.query(Vehicle).filter(Vehicle.is_available.is_(True)).all()
    if vehicles:
        seen = set()
        v_types = []
        for v in sorted(vehicles, key=lambda x: x.capacity_kg):
            if v.vehicle_type not in seen:
                seen.add(v.vehicle_type)
                v_types.append(
                    {
                        "vehicle_type": v.vehicle_type,
                        "capacity_kg": float(v.capacity_kg),
                        "cost_per_km": float(v.cost_per_km),
                        "fixed_cost_per_trip": float(v.fixed_cost_per_trip),
                    }
                )
        return v_types

    # Fallback default types per config/logistics.yaml
    return [
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
