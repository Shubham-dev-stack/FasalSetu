from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.dates import today_ist
from app.schemas.listing import CropSummary


class BuyerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_name: str
    buyer_type: str
    city: str
    state: str
    hub_id: int
    lat: float
    lng: float


class LandedPriceGuidance(BaseModel):
    formula: str = "max_landed_price >= farmgate_ask + transport_cost + platform_fee (2%)"
    note: str = "Includes farmgate ask + transport + 2% platform fee"


class RequirementCreate(BaseModel):
    crop_id: int
    grade_min: str = Field(..., pattern="^(A|B|C)$")
    quantity_kg: float = Field(..., gt=0, le=100000.0)
    max_landed_price_per_kg: float = Field(..., gt=0, le=100000.0)
    needed_by: date
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_create_constraints(self) -> "RequirementCreate":
        today = today_ist()
        if self.needed_by < today:
            raise ValueError("needed_by cannot be in the past")
        return self


class RequirementUpdate(BaseModel):
    quantity_kg: float | None = Field(default=None, gt=0, le=100000.0)
    max_landed_price_per_kg: float | None = Field(default=None, gt=0, le=100000.0)
    needed_by: date | None = None
    notes: str | None = Field(default=None, max_length=1000)
    status: str | None = Field(default=None, pattern="^(CANCELLED)$")

    @model_validator(mode="after")
    def validate_update_constraints(self) -> "RequirementUpdate":
        today = today_ist()
        if self.needed_by is not None and self.needed_by < today:
            raise ValueError("needed_by cannot be in the past")
        return self


class RequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    buyer: BuyerSummary
    crop: CropSummary
    grade_min: str
    quantity_kg: float
    quantity_fulfilled_kg: float
    max_landed_price_per_kg: float
    needed_by: date
    status: str
    notes: str | None = None
    is_demo: bool
    created_at: datetime
    landed_guidance: LandedPriceGuidance | None = None


class RequirementDetailResponse(BaseModel):
    requirement: RequirementOut
    landed_guidance: LandedPriceGuidance | None = None


class RequirementListResponse(BaseModel):
    items: list[RequirementOut]
    total: int
