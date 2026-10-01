from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProducerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    producer_type: str
    org_name: str
    state: str
    district: str
    locality: str | None = None
    lat: float
    lng: float
    member_farmers: int | None = None
    is_demo: bool
    created_at: datetime


class ProducerProfileUpdate(BaseModel):
    org_name: str | None = Field(default=None, min_length=2, max_length=255)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    district: str | None = Field(default=None, min_length=2, max_length=100)
    locality: str | None = Field(default=None, max_length=255)
    lat: float | None = Field(default=None, ge=6.0, le=38.0)
    lng: float | None = Field(default=None, ge=68.0, le=98.0)
    member_farmers: int | None = Field(default=None, ge=1)


class HubSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    state: str
    lat: float
    lng: float


class BuyerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    buyer_type: str
    org_name: str
    hub_id: int
    hub: HubSummary | None = None
    city: str
    state: str
    lat: float
    lng: float
    is_demo: bool
    created_at: datetime


class BuyerProfileUpdate(BaseModel):
    org_name: str | None = Field(default=None, min_length=2, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    hub_id: int | None = Field(default=None, ge=1)
    lat: float | None = Field(default=None, ge=6.0, le=38.0)
    lng: float | None = Field(default=None, ge=68.0, le=98.0)
