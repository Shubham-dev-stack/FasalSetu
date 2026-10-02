from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.order import CropOrderSummary, OrderOut


class MatchingScores(BaseModel):
    price: float
    distance: float
    freshness: float
    fill: float
    total: float


class MatchingWeights(BaseModel):
    price: float
    distance: float
    freshness: float
    fill: float


class CandidateProducerSummary(BaseModel):
    id: int
    org_name: str
    producer_type: str | None = None
    district: str | None = None
    state: str | None = None


class CandidateListingSummary(BaseModel):
    id: int
    producer: CandidateProducerSummary
    grade: str
    ask_price_per_kg: float
    harvest_date: date
    available_from: date
    available_until: date
    min_order_kg: float


class CandidateOut(BaseModel):
    rank: int
    listing: CandidateListingSummary
    available_kg: float
    allocated_kg: float
    distance_km: float
    distance_source: str = "ESTIMATED_HAVERSINE"
    transit_hours: float
    age_at_delivery_days: int
    ask_price_per_kg: float
    transport_cost_per_kg: float
    platform_fee_per_kg: float
    landed_price_per_kg: float
    scores: MatchingScores
    weights: MatchingWeights
    reasons: list[str]


class AllocationItem(BaseModel):
    listing_id: int
    quantity_kg: float = Field(..., gt=0)


class NearMissOut(BaseModel):
    listing_id: int
    excluded_reason: Literal[
        "BUDGET", "GRADE", "DISTANCE", "FRESHNESS", "AVAILABILITY", "BELOW_MIN_ORDER"
    ]
    detail: str
    landed_price_per_kg: float | None = None
    distance_km: float | None = None


class RequirementSummary(BaseModel):
    id: int
    crop: CropOrderSummary
    grade_min: str
    quantity_kg: float
    quantity_fulfilled_kg: float
    max_landed_price_per_kg: float
    needed_by: date
    status: str


class RequirementCandidatesResponse(BaseModel):
    requirement: RequirementSummary
    fill_status: Literal["FULL", "PARTIAL", "NONE"]
    requested_kg: float
    fulfilled_kg: float
    shortfall_kg: float
    earliest_delivery_date: date | None = None
    allocations: list[AllocationItem]
    candidates: list[CandidateOut]
    near_misses: list[NearMissOut]


class MatchingAcceptRequest(BaseModel):
    requirement_id: int
    allocations: list[AllocationItem] = Field(..., min_length=1)
    delivery_date: date


class MatchingAcceptRequirementOut(BaseModel):
    id: int
    status: str
    quantity_fulfilled_kg: float


class MatchingAcceptResponse(BaseModel):
    orders: list[OrderOut]
    requirement: MatchingAcceptRequirementOut


class OpportunityBuyerSummary(BaseModel):
    id: int
    org_name: str
    buyer_type: str
    city: str | None = None
    state: str | None = None


class OpportunityRequirementSummary(BaseModel):
    id: int
    crop: CropOrderSummary
    grade_min: str
    quantity_kg: float
    quantity_fulfilled_kg: float
    max_landed_price_per_kg: float
    needed_by: date


class OpportunityOut(BaseModel):
    requirement: OpportunityRequirementSummary
    buyer: OpportunityBuyerSummary
    distance_km: float
    landed_price_per_kg: float
    scores: MatchingScores
    reasons: list[str]


class HubForecastContext(BaseModel):
    hub: dict
    forecast_7d_kg: float
    status: Literal["SHORTAGE", "BALANCED", "SURPLUS"]


class OpportunityListingSummary(BaseModel):
    id: int
    crop: CropOrderSummary
    grade: str
    quantity_available_kg: float
    ask_price_per_kg: float


class ProducerOpportunitiesResponse(BaseModel):
    listing: OpportunityListingSummary
    opportunities: list[OpportunityOut]
    hub_context: HubForecastContext | None = None
