from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.forecasting.service import (
    get_demand_forecast,
    get_forecast_model_info,
    get_hubs_forecast_and_opportunity,
)
from app.schemas.forecast import (
    ForecastDemandResponse,
    ForecastHubsResponse,
    ModelInfoResponse,
)

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.get(
    "/demand",
    response_model=ForecastDemandResponse,
    status_code=status.HTTP_200_OK,
)
def get_hub_crop_demand_forecast(
    hub_id: int = Query(..., description="Target demand hub ID"),
    crop_id: int = Query(..., description="Target crop ID"),
    horizon_days: int = Query(default=7, ge=1, le=7, description="Forecast horizon in days (1-7)"),
    cutoff_date: date | None = Query(default=None, description="Optional cutoff date (defaults to latest observed)"),
    db: Session = Depends(get_db),
):
    """Retrieve 1-7 day ahead demand forecast with 80% interval and 28-day history."""
    return get_demand_forecast(
        db=db,
        hub_id=hub_id,
        crop_id=crop_id,
        horizon_days=horizon_days,
        cutoff_date=cutoff_date,
    )


@router.get(
    "/hubs",
    response_model=ForecastHubsResponse,
    status_code=status.HTTP_200_OK,
)
def compare_hubs_demand_and_opportunity(
    crop_id: int = Query(..., description="Target crop ID"),
    horizon_days: int = Query(default=7, ge=1, le=7, description="Forecast horizon in days (1-7)"),
    cutoff_date: date | None = Query(default=None, description="Optional cutoff date"),
    db: Session = Depends(get_db),
):
    """Compare all 5 demand hubs for a crop and rank by supply deficit / opportunity."""
    return get_hubs_forecast_and_opportunity(
        db=db,
        crop_id=crop_id,
        horizon_days=horizon_days,
        cutoff_date=cutoff_date,
    )


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    status_code=status.HTTP_200_OK,
)
def get_model_card_info():
    """Retrieve model metadata, deployment gate decision, and validation/test metrics."""
    return get_forecast_model_info()
