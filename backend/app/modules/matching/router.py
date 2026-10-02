from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.db.models import User
from app.modules.matching.service import (
    accept_matching_allocation,
    get_listing_opportunities,
    get_requirement_candidates,
)
from app.schemas.matching import (
    MatchingAcceptRequest,
    MatchingAcceptResponse,
    ProducerOpportunitiesResponse,
    RequirementCandidatesResponse,
)

router = APIRouter(prefix="/matching", tags=["matching"])


@router.get(
    "/requirements/{id}/candidates",
    response_model=RequirementCandidatesResponse,
)
def get_candidates_for_requirement(
    id: int,
    max_results: int = Query(default=10, ge=1, le=25),
    current_user: User = Depends(require_role(["BUYER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    return get_requirement_candidates(
        db=db,
        requirement_id=id,
        current_user=current_user,
        max_results=max_results,
    )


@router.post(
    "/accept",
    response_model=MatchingAcceptResponse,
    status_code=status.HTTP_201_CREATED,
)
def accept_allocation(
    data: MatchingAcceptRequest,
    current_user: User = Depends(require_role(["BUYER"])),
    db: Session = Depends(get_db),
):
    return accept_matching_allocation(
        db=db,
        current_user=current_user,
        data=data,
    )


@router.get(
    "/listings/{id}/opportunities",
    response_model=ProducerOpportunitiesResponse,
)
def get_opportunities_for_listing(
    id: int,
    limit: int = Query(default=10, ge=1, le=25),
    current_user: User = Depends(require_role(["PRODUCER", "ADMIN"])),
    db: Session = Depends(get_db),
):
    return get_listing_opportunities(
        db=db,
        listing_id=id,
        current_user=current_user,
        limit=limit,
    )
