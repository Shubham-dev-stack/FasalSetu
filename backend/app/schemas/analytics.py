
from pydantic import BaseModel, Field


class AnalyticsKPIs(BaseModel):
    committed_orders: int = Field(description="Number of orders in CONFIRMED, IN_TRANSIT, or DELIVERED status")
    committed_volume_kg: float = Field(description="Total kg quantity of committed orders")
    committed_value_inr: float = Field(description="Total farmgate value (agreed price * qty) in INR of committed orders")
    requirement_fill_rate_pct: float | None = Field(None, description="Fulfilled kg / requested kg across non-cancelled requirements")
    avg_logistics_cost_per_kg: float | None = Field(None, description="Average transport cost per kg across committed orders")
    route_savings_km: float = Field(description="Cumulative km savings across APPROVED route plans vs dedicated baseline")
    route_savings_inr: float = Field(description="Cumulative INR savings across APPROVED route plans vs dedicated baseline")
    avg_utilization_pct: float | None = Field(None, description="Average vehicle peak/capacity load utilization across approved shipments")


class AnalyticsPriceGap(BaseModel):
    avg_farmer_delta_pct: float | None = Field(None, description="Average % gain for farmer over mandi net realization")
    avg_buyer_delta_pct: float | None = Field(None, description="Average % price difference for buyer vs traditional retail")
    orders_considered: int = Field(description="Number of committed orders with benchmark & scenario evaluation")
    basis: str = Field("MODELLED_SCENARIO", description="Methodology basis flag")


class DailyOrdersPoint(BaseModel):
    date: str = Field(description="ISO date string YYYY-MM-DD")
    orders: int = Field(description="Committed orders count on this date")
    volume_kg: float = Field(description="Committed produce volume in kg on this date")


class AnalyticsModelContext(BaseModel):
    deployed_method: str = Field(description="Forecast deployed method (e.g., LIGHTGBM, SEASONAL_NAIVE_FALLBACK)")
    data_source: str = Field("SYNTHETIC", description="Provenance of demand data source")
    model_version: str | None = Field(None, description="Model training version or run id")


class AnalyticsOverviewResponse(BaseModel):
    as_of: str = Field(description="ISO timestamp / date of generation")
    data_note: str = Field(
        "All figures computed from synthetic demo records",
        description="Transparent disclaimer regarding synthetic demo baseline",
    )
    kpis: AnalyticsKPIs
    price_gap: AnalyticsPriceGap
    daily: list[DailyOrdersPoint] = Field(description="14-day daily committed orders and volume series")
    model: AnalyticsModelContext


class SupplyDemandRow(BaseModel):
    hub: str = Field(description="Hub name")
    hub_id: int = Field(description="Demand hub database ID")
    crop: str = Field(description="Crop name")
    crop_id: int = Field(description="Crop database ID")
    forecast_7d_kg: float = Field(description="Sum of 7-day predicted demand in kg")
    supply_kg: float = Field(description="Active available supply in kg attributed to this nearest hub")
    ratio: float = Field(description="Supply-to-demand ratio (supply / forecast_7d)")
    status: str = Field(description="Market status: SHORTAGE (<0.7), SURPLUS (>1.3), or BALANCED")


class AnalyticsSupplyDemandResponse(BaseModel):
    rows: list[SupplyDemandRow] = Field(description="Hub x Crop supply-vs-demand rows")
    method: str = Field(description="Forecasting method used for demand prediction")
    data_source: str = Field("SYNTHETIC", description="Provenance of underlying demand history")
    as_of: str = Field(description="ISO timestamp / date")
