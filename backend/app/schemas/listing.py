from datetime import date, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.dates import today_ist


class ProducerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_name: str
    producer_type: str
    district: str
    state: str
    lat: float
    lng: float


class CropSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    shelf_life_days: int
    perishability: str


class LandedEstimate(BaseModel):
    distance_km: float
    distance_source: str
    transport_cost_per_kg: float
    platform_fee_per_kg: float
    landed_price_per_kg: float
    basis: str = "ESTIMATE"


class BenchmarkContext(BaseModel):
    nearest_hub_name: str | None = None
    benchmark_modal_per_kg: float | None = None
    benchmark_source: str | None = None


class ListingCreate(BaseModel):
    crop_id: int
    variety: str | None = Field(default=None, max_length=100)
    grade: str = Field(..., pattern="^(A|B|C)$")
    quantity_kg: float = Field(..., gt=0, le=100000.0)
    ask_price_per_kg: float = Field(..., gt=0, le=100000.0)
    min_order_kg: float = Field(..., gt=0, le=100000.0)
    harvest_date: date
    available_from: date
    available_until: date

    @model_validator(mode="after")
    def validate_listing_constraints(self) -> "ListingCreate":
        today = today_ist()

        if self.min_order_kg > self.quantity_kg:
            raise ValueError("min_order_kg cannot exceed quantity_kg")

        if self.harvest_date > today:
            raise ValueError("harvest_date cannot be in the future")

        if self.harvest_date < today - timedelta(days=30):
            raise ValueError("harvest_date cannot be older than 30 days")

        if self.available_until < self.available_from:
            raise ValueError("available_until cannot be earlier than available_from")

        if self.available_until < today:
            raise ValueError("available_until cannot be in the past")

        return self


class ListingUpdate(BaseModel):
    ask_price_per_kg: float | None = Field(default=None, gt=0, le=100000.0)
    quantity_kg: float | None = Field(default=None, gt=0, le=100000.0)
    min_order_kg: float | None = Field(default=None, gt=0, le=100000.0)
    available_until: date | None = None
    status: str | None = Field(default=None, pattern="^(WITHDRAWN)$")

    @model_validator(mode="after")
    def validate_update_constraints(self) -> "ListingUpdate":
        today = today_ist()
        if self.available_until is not None and self.available_until < today:
            raise ValueError("available_until cannot be in the past")
        return self


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producer: ProducerSummary
    crop: CropSummary
    variety: str | None = None
    grade: str
    quantity_kg: float
    quantity_available_kg: float
    ask_price_per_kg: float
    min_order_kg: float
    harvest_date: date
    available_from: date
    available_until: date
    status: str
    is_demo: bool
    harvest_age_days: int
    landed_estimate: LandedEstimate | None = None
    demand_status: str | None = None
    created_at: datetime


class ListingCreateResponse(BaseModel):
    listing: ListingOut
    warnings: list[str] = []
    benchmark_context: BenchmarkContext | None = None


class ListingDetailResponse(BaseModel):
    listing: ListingOut
    benchmark_context: BenchmarkContext | None = None


class ListingListResponse(BaseModel):
    items: list[ListingOut]
    total: int
