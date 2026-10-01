from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.db.models import BuyerProfile, DemandHub, ProducerProfile, User
from app.schemas.profile import BuyerProfileUpdate, ProducerProfileUpdate


def get_producer_profile_for_user(db: Session, user: User) -> ProducerProfile:
    profile = (
        db.query(ProducerProfile).filter(ProducerProfile.user_id == user.id).first()
    )
    if not profile:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message="Producer profile not found for the authenticated user.",
        )
    return profile


def update_producer_profile_for_user(
    db: Session, user: User, data: ProducerProfileUpdate
) -> ProducerProfile:
    profile = get_producer_profile_for_user(db, user)

    # Validate member_farmers constraint: only FPO can specify member_farmers
    if data.member_farmers is not None and profile.producer_type != "FPO":
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="member_farmers is only applicable to FPO producers.",
            details=[
                {
                    "field": "member_farmers",
                    "issue": "Cannot set member_farmers on FARMER producer type",
                }
            ],
        )

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(profile, field, val)

    db.commit()
    db.refresh(profile)
    return profile


def get_buyer_profile_for_user(db: Session, user: User) -> BuyerProfile:
    profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user.id).first()
    if not profile:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message="Buyer profile not found for the authenticated user.",
        )
    return profile


def update_buyer_profile_for_user(
    db: Session, user: User, data: BuyerProfileUpdate
) -> BuyerProfile:
    profile = get_buyer_profile_for_user(db, user)

    if data.hub_id is not None:
        hub = db.query(DemandHub).filter(DemandHub.id == data.hub_id).first()
        if not hub:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message="Specified demand hub does not exist.",
                details=[
                    {
                        "field": "hub_id",
                        "issue": f"Demand hub with id {data.hub_id} not found",
                    }
                ],
            )

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(profile, field, val)

    db.commit()
    db.refresh(profile)
    return profile
