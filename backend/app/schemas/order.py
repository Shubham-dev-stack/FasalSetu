from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.dates import today_ist


class BuyerOrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_name: str
    hub_id: int | None = None


class ProducerOrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_name: str
    district: str
    state: str


class CropOrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class OrderEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    from_status: str | None = None
    to_status: str
    actor_user_id: int
    actor_role: str
    note: str | None = None
    at: datetime


class OrderCreate(BaseModel):
    listing_id: int
    quantity_kg: float = Field(..., gt=0, le=100000.0)
    delivery_date: date
    requirement_id: int | None = None

    @model_validator(mode="after")
    def validate_create_constraints(self) -> "OrderCreate":
        today = today_ist()
        if self.delivery_date < today:
            raise ValueError("delivery_date cannot be in the past")
        return self


class OrderTransitionRequest(BaseModel):
    to_status: str = Field(..., pattern="^(CONFIRMED|REJECTED|CANCELLED)$")
    note: str | None = Field(default=None, max_length=500)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    requirement_id: int | None = None
    buyer: BuyerOrderSummary
    producer: ProducerOrderSummary
    crop: CropOrderSummary
    quantity_kg: float
    agreed_price_per_kg: float
    transport_cost_estimate_per_kg: float
    platform_fee_per_kg: float
    landed_price_per_kg_estimate: float
    total_amount_estimate: float
    delivery_date: date
    status: str
    origin: str
    shipment_id: int | None = None
    allocated_transport_cost_total: float | None = None
    events: list[OrderEventOut] = []
    is_demo: bool = False
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    items: list[OrderOut]
    total: int
