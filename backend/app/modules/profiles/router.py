from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.db.models import User
from app.modules.profiles.service import (
    get_producer_profile_for_user,
    update_producer_profile_for_user,
)
from app.schemas.profile import ProducerProfileOut, ProducerProfileUpdate

router = APIRouter(prefix="/producers", tags=["producers"])


@router.get("/me", response_model=ProducerProfileOut)
def get_my_producer_profile(
    current_user: User = Depends(require_role(["PRODUCER"])),
    db: Session = Depends(get_db),
):
    return get_producer_profile_for_user(db, current_user)


@router.patch("/me", response_model=ProducerProfileOut)
def update_my_producer_profile(
    data: ProducerProfileUpdate,
    current_user: User = Depends(require_role(["PRODUCER"])),
    db: Session = Depends(get_db),
):
    return update_producer_profile_for_user(db, current_user, data)
