from typing import Any

from pydantic import BaseModel, ConfigDict


class ForecastHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str
    demand_kg: float
    is_synthetic: bool = True


class ForecastDailyItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str
    day_of_week: str
    point_forecast_kg: float
    interval_lo_kg: float | None = None
    interval_hi_kg: float | None = None


class ForecastDemandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hub_id: int
    hub_name: str
    crop_id: int
    crop_name: str
    cutoff_date: str
    horizon_days: int
    method: str
    model_version: str
    demand_data_source: str = "SYNTHETIC"
    price_feature_sources: list[str] = ["SYNTHETIC_DEMO", "AGMARKNET_SNAPSHOT"]
    reproducibility: str
    disclaimer: str
    history: list[ForecastHistoryItem]
    forecast: list[ForecastDailyItem]


class HubOpportunityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hub_id: int
    hub_name: str
    state: str
    lat: float
    lng: float
    total_forecast_kg: float
    avg_daily_forecast_kg: float
    active_supply_kg: float
    supply_demand_ratio: float
    opportunity_label: str
    method: str


class ForecastHubsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crop_id: int
    crop_name: str
    cutoff_date: str
    horizon_days: int
    demand_data_source: str = "SYNTHETIC"
    disclaimer: str
    hubs: list[HubOpportunityItem]


class ModelInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_id: str
    model_version: str
    trained_at: str
    git_commit: str
    dataset_hash_sha256: str
    generator_version: str
    demand_data_source: str
    price_feature_sources: list[str]
    reproducibility: str
    deployed_method: str
    deployment_gate: dict[str, Any]
    metrics: dict[str, Any]
    split_spec: dict[str, Any]
    disclaimer: str
