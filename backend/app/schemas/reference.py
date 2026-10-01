from typing import Any

from pydantic import BaseModel, ConfigDict


class CropOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    agmarknet_commodity_name: str
    shelf_life_days: int
    max_transit_hours: int
    perishability: str
    notes: str | None = None


class HubOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str
    state: str
    lat: float
    lng: float
    reference_market_name: str


class ReferenceResponse(BaseModel):
    crops: list[CropOut]
    hubs: list[HubOut]
    enums: dict[str, list[str]]
    public_config: dict[str, Any]
