from pydantic import BaseModel, Field


class OptimizeRequest(BaseModel):
    order_ids: list[int] | None = None
    time_limit_s: int = Field(default=5, ge=1, le=30)
    distance_mode: str = "HAVERSINE"  # HAVERSINE | OSRM


class StopOut(BaseModel):
    sequence: int
    stop_type: str  # DEPOT_START | PICKUP | DROP | DEPOT_END
    order_id: int | None = None
    label: str
    lat: float
    lng: float
    load_after_kg: float
    cum_distance_km: float
    eta_min_from_start: int


class PlanVehicleOut(BaseModel):
    id: int
    name: str
    vehicle_type: str
    capacity_kg: float


class PlanShipmentOut(BaseModel):
    temp_id: str
    shipment_id: int | None = None
    vehicle: PlanVehicleOut
    total_distance_km: float
    total_cost: float
    peak_load_kg: float
    utilization_pct: float
    est_duration_min: int
    stops: list[StopOut]
    geometry: list[list[float]] = []


class PlanTotals(BaseModel):
    optimized_km: float
    optimized_cost: float
    baseline_km: float
    baseline_cost: float
    savings_km: float
    savings_cost: float
    savings_pct_cost: float
    vehicles_used: int
    avg_utilization_pct: float


class UnassignedOrder(BaseModel):
    order_id: int
    quantity_kg: float
    reason: str  # CAPACITY | DURATION | NO_FEASIBLE_INSERTION


class PlanResponse(BaseModel):
    plan_id: str
    status: str  # PROPOSED | APPROVED | DISCARDED
    method: str  # ORTOOLS | GREEDY_FALLBACK
    solver_status: str | None = None
    solve_time_ms: int
    distance_source: str = "ESTIMATED_HAVERSINE"
    totals: PlanTotals
    baseline_note: str = (
        "Baseline = each order shipped on its own dedicated round trip (modelled, not measured)."
    )
    shipments: list[PlanShipmentOut]
    unassigned: list[UnassignedOrder]
    skipped_order_ids: list[int] = []
    warnings: list[str] = []


class PlanSummaryItem(BaseModel):
    plan_id: str
    status: str
    created_at: str
    method: str
    num_orders: int
    num_unassigned: int
    optimized_km: float
    optimized_cost: float
    baseline_cost: float


class PlanListResponse(BaseModel):
    items: list[PlanSummaryItem]
    total: int


class ShipmentDetailResponse(BaseModel):
    id: int
    plan_id: str
    vehicle_id: int
    vehicle_name: str
    vehicle_type: str
    status: str  # PLANNED | DISPATCHED | DELIVERED
    total_distance_km: float
    total_cost: float
    peak_load_kg: float
    utilization_pct: float
    est_duration_min: int
    stops: list[StopOut]
    order_ids: list[int]


class PlanApproveResponse(BaseModel):
    plan: PlanResponse
    shipments: list[ShipmentDetailResponse]


class ShipmentTransitionRequest(BaseModel):
    to_status: str  # DISPATCHED | DELIVERED
