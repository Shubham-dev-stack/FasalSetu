from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.models import User
from app.modules.routes.service import (
    approve_route_plan,
    discard_route_plan,
    get_route_plan_detail,
    get_shipment_detail,
    list_route_plans,
    solve_and_store_route_plan,
    transition_shipment_status,
)
from app.schemas.routes import (
    OptimizeRequest,
    PlanApproveResponse,
    PlanListResponse,
    PlanResponse,
    ShipmentDetailResponse,
    ShipmentTransitionRequest,
)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/optimize", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def optimize_routes(
    data: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Solve and store a PROPOSED route plan per API.md §11."""
    if current_user.role.upper() not in ["ADMIN", "OPERATOR"]:
        from app.core.errors import AppException

        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only operators can optimize routes.",
        )
    return solve_and_store_route_plan(db, current_user, data)


@router.get("/plans", response_model=PlanListResponse)
def list_plans(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List route plans per API.md §11."""
    if current_user.role.upper() not in ["ADMIN", "OPERATOR"]:
        from app.core.errors import AppException

        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only operators can list route plans.",
        )
    return list_route_plans(db, limit, offset)


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get route plan details per API.md §11."""
    return get_route_plan_detail(db, plan_id, current_user)


@router.post("/plans/{plan_id}/approve", response_model=PlanApproveResponse)
def approve_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a PROPOSED route plan per API.md §11."""
    if current_user.role.upper() not in ["ADMIN", "OPERATOR"]:
        from app.core.errors import AppException

        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only operators can approve route plans.",
        )
    return approve_route_plan(db, plan_id, current_user)


@router.post("/plans/{plan_id}/discard", response_model=PlanResponse)
def discard_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Discard a PROPOSED route plan per API.md §11."""
    if current_user.role.upper() not in ["ADMIN", "OPERATOR"]:
        from app.core.errors import AppException

        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only operators can discard route plans.",
        )
    return discard_route_plan(db, plan_id, current_user)


@router.get("/shipments/{shipment_id}", response_model=ShipmentDetailResponse)
def get_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get shipment details per API.md §11."""
    return get_shipment_detail(db, shipment_id, current_user)


@router.post("/shipments/{shipment_id}/transition", response_model=ShipmentDetailResponse)
def transition_shipment(
    shipment_id: int,
    data: ShipmentTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition shipment status (PLANNED -> DISPATCHED -> DELIVERED) per API.md §11."""
    if current_user.role.upper() not in ["ADMIN", "OPERATOR"]:
        from app.core.errors import AppException

        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only operators can transition shipment status.",
        )
    return transition_shipment_status(db, shipment_id, data.to_status, current_user)
