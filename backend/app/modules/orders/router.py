from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_role
from app.db.models import User
from app.modules.orders.service import (
    create_direct_order,
    get_order_detail,
    list_orders,
    transition_order_status,
)
from app.schemas.order import (
    OrderCreate,
    OrderListResponse,
    OrderOut,
    OrderTransitionRequest,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
)
def create_new_order(
    data: OrderCreate,
    current_user: User = Depends(require_role(["BUYER"])),
    db: Session = Depends(get_db),
):
    return create_direct_order(db=db, current_user=current_user, data=data)


@router.get("", response_model=OrderListResponse)
def get_orders(
    status: str | None = Query(default=None),
    crop_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_orders(
        db=db,
        current_user=current_user,
        status_filter=status,
        crop_id=crop_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{order_id}", response_model=OrderOut)
def get_one_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_order_detail(db=db, order_id=order_id, current_user=current_user)


@router.post("/{order_id}/transition", response_model=OrderOut)
def transition_order(
    order_id: int,
    data: OrderTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transition_order_status(
        db=db, order_id=order_id, current_user=current_user, data=data
    )
