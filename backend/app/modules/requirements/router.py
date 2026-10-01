from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.db.models import User
from app.modules.requirements.service import (
    build_requirement_out,
    create_requirement,
    get_requirement_by_id,
    get_requirements,
    update_requirement,
)
from app.schemas.requirement import (
    LandedPriceGuidance,
    RequirementCreate,
    RequirementDetailResponse,
    RequirementListResponse,
    RequirementOut,
    RequirementUpdate,
)

router = APIRouter(prefix="/requirements", tags=["requirements"])


@router.post("", response_model=RequirementOut, status_code=status.HTTP_201_CREATED)
def create_new_requirement(
    data: RequirementCreate,
    current_user: User = Depends(require_role(["BUYER"])),
    db: Session = Depends(get_db),
):
    req = create_requirement(db, current_user, data)
    return build_requirement_out(req)


@router.get("", response_model=RequirementListResponse)
def list_requirements(
    crop_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_role(["BUYER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    items, total = get_requirements(
        db,
        current_user,
        crop_id=crop_id,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    return RequirementListResponse(
        items=[build_requirement_out(r) for r in items],
        total=total,
    )


@router.get("/{id}", response_model=RequirementDetailResponse)
def get_single_requirement(
    id: int,
    current_user: User = Depends(require_role(["BUYER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    req = get_requirement_by_id(db, current_user, id)
    return RequirementDetailResponse(
        requirement=build_requirement_out(req),
        landed_guidance=LandedPriceGuidance(),
    )


@router.patch("/{id}", response_model=RequirementOut)
def update_single_requirement(
    id: int,
    data: RequirementUpdate,
    current_user: User = Depends(require_role(["BUYER"])),
    db: Session = Depends(get_db),
):
    req = update_requirement(db, current_user, id, data)
    return build_requirement_out(req)
