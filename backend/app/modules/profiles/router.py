from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.db.models import User
from app.modules.profiles.service import (
    get_buyer_profile_for_user,
    get_producer_profile_for_user,
    update_buyer_profile_for_user,
    update_producer_profile_for_user,
)
from app.schemas.profile import (
    BuyerProfileOut,
    BuyerProfileUpdate,
    ProducerProfileOut,
    ProducerProfileUpdate,
)

producers_router = APIRouter(prefix="/producers", tags=["producers"])
buyers_router = APIRouter(prefix="/buyers", tags=["buyers"])


@producers_router.get("/me", response_model=ProducerProfileOut)
def get_my_producer_profile(
    current_user: User = Depends(require_role(["PRODUCER"])),
    db: Session = Depends(get_db),
):
    return get_producer_profile_for_user(db, current_user)


@producers_router.patch("/me", response_model=ProducerProfileOut)
def update_my_producer_profile(
    data: ProducerProfileUpdate,
    current_user: User = Depends(require_role(["PRODUCER"])),
    db: Session = Depends(get_db),
):
    return update_producer_profile_for_user(db, current_user, data)


@buyers_router.get("/me", response_model=BuyerProfileOut)
def get_my_buyer_profile(
    current_user: User = Depends(require_role(["BUYER"])),
    db: Session = Depends(get_db),
):
    return get_buyer_profile_for_user(db, current_user)


@buyers_router.patch("/me", response_model=BuyerProfileOut)
def update_my_buyer_profile(
    data: BuyerProfileUpdate,
    current_user: User = Depends(require_role(["BUYER"])),
    db: Session = Depends(get_db),
):
    return update_buyer_profile_for_user(db, current_user, data)


router = APIRouter()
router.include_router(producers_router)
router.include_router(buyers_router)
