from pydantic import BaseModel, Field


class VehiclePlanLegOut(BaseModel):
    vehicle_type: str
    capacity_kg: float
    load_kg: float
    trips: int
    trip_cost: float
    total_cost: float


class LogisticsEstimateRequest(BaseModel):
    listing_id: int
    quantity_kg: float = Field(..., gt=0)
    buyer_id: int | None = None
    dest_lat: float | None = None
    dest_lng: float | None = None


class LogisticsEstimateResponse(BaseModel):
    distance_km: float
    distance_source: str = "ESTIMATED_HAVERSINE"
    vehicle_plan: list[VehiclePlanLegOut]
    trips: int
    cost_total: float
    cost_per_kg: float
    transit_hours: float
    basis: str = "ESTIMATE"


class VehicleOut(BaseModel):
    id: int
    name: str
    vehicle_type: str
    capacity_kg: float
    cost_per_km: float
    fixed_cost_per_trip: float
    avg_speed_kmph: float
    depot_name: str
    depot_lat: float
    depot_lng: float
    is_available: bool
    is_demo: bool


class VehicleListResponse(BaseModel):
    items: list[VehicleOut]
