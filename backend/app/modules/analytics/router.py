
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.models import User
from app.modules.analytics.service import (
    get_analytics_overview,
    get_analytics_supply_demand,
)
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    AnalyticsSupplyDemandResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Platform-wide impact analytics KPI overview and trends",
)
def analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve aggregate platform KPIs, price gap, and 14-day order trends.

    Accessible to any authenticated user (PRODUCER, BUYER, ADMIN/OPERATOR).
    All metrics are computed from platform transaction records, model outputs,
    and traditional-chain scenario assumptions.
    """
    return get_analytics_overview(db)


@router.get(
    "/supply-demand",
    response_model=AnalyticsSupplyDemandResponse,
    summary="Hub x Crop supply-vs-demand gap matrix",
)
def analytics_supply_demand(
    crop_id: int | None = Query(None, description="Filter by crop ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the Hub x Crop supply-vs-demand gap matrix with status chips.

    Accessible to any authenticated user.
    Each active listing is attributed to its nearest demand hub (Rule D-026).
    """
    return get_analytics_supply_demand(db, crop_id=crop_id)
