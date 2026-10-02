from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.models import User
from app.modules.pricing.service import get_order_price_breakdown, get_pricing_benchmark
from app.schemas.pricing import OrderPriceBreakdownResponse, PricingBenchmarkResponse

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/breakdown", response_model=OrderPriceBreakdownResponse)
def get_breakdown(
    order_id: int = Query(..., description="Order ID to retrieve price breakdown for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve per-order price waterfall breakdown per API.md §12 / PRD FR-90."""
    return get_order_price_breakdown(db=db, order_id=order_id, current_user=current_user)


@router.get("/benchmark", response_model=PricingBenchmarkResponse)
def get_benchmark(
    crop_id: int = Query(..., description="Crop ID to get benchmark for"),
    hub_id: int | None = Query(None, description="Demand hub ID (mutually exclusive with lat/lng)"),
    lat: float | None = Query(None, description="Latitude to find nearest hub"),
    lng: float | None = Query(None, description="Longitude to find nearest hub"),
    quantity_kg: float = Query(1000.0, description="Representative quantity basis in kg"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve benchmark price, 30-day trend, and fair-price band per API.md §12 / PRD FR-91."""
    return get_pricing_benchmark(
        db=db,
        crop_id=crop_id,
        hub_id=hub_id,
        lat=lat,
        lng=lng,
        quantity_kg=quantity_kg,
    )
