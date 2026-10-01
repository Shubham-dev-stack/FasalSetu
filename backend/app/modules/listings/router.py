from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_optional_current_user, require_role
from app.db.models import User
from app.modules.listings.service import (
    create_listing,
    get_listing_detail,
    list_listings,
    update_listing,
)
from app.schemas.listing import (
    ListingCreate,
    ListingCreateResponse,
    ListingDetailResponse,
    ListingListResponse,
    ListingOut,
    ListingUpdate,
)

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post(
    "",
    response_model=ListingCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_listing(
    data: ListingCreate,
    current_user: User = Depends(require_role(["PRODUCER"])),
    db: Session = Depends(get_db),
):
    return create_listing(db, current_user, data)


@router.get("", response_model=ListingListResponse)
def get_all_listings(
    crop_id: int | None = Query(default=None),
    grade_min: str | None = Query(default=None),
    state: str | None = Query(default=None),
    max_price: float | None = Query(default=None),
    harvested_within_days: int | None = Query(default=None),
    status: str | None = Query(default="ACTIVE"),
    mine: bool = Query(default=False),
    sort: str | None = Query(default=None),
    buyer_lat: float | None = Query(default=None),
    buyer_lng: float | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    return list_listings(
        db=db,
        current_user=current_user,
        crop_id=crop_id,
        grade_min=grade_min,
        state=state,
        max_price=max_price,
        harvested_within_days=harvested_within_days,
        status_filter=status,
        mine=mine,
        sort=sort,
        buyer_lat=buyer_lat,
        buyer_lng=buyer_lng,
        limit=limit,
        offset=offset,
    )


@router.get("/{listing_id}", response_model=ListingDetailResponse)
def get_one_listing(listing_id: int, db: Session = Depends(get_db)):
    return get_listing_detail(db, listing_id)


@router.patch("/{listing_id}", response_model=ListingOut)
def patch_existing_listing(
    listing_id: int,
    data: ListingUpdate,
    current_user: User = Depends(require_role(["PRODUCER"])),
    db: Session = Depends(get_db),
):
    return update_listing(db, listing_id, current_user, data)
