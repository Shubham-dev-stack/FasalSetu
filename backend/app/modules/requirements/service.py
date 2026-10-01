from fastapi import status
from sqlalchemy.orm import Session

from app.core.dates import today_ist
from app.core.errors import AppException
from app.db.models import BuyerProfile, Crop, Requirement, User
from app.schemas.listing import CropSummary
from app.schemas.requirement import (
    BuyerSummary,
    LandedPriceGuidance,
    RequirementCreate,
    RequirementOut,
    RequirementUpdate,
)


def evaluate_dynamic_expiry(db: Session, requirement: Requirement) -> Requirement:
    """Evaluate Rule D-021: if needed_by is in the past for OPEN/PARTIALLY_FULFILLED, transition to EXPIRED."""
    today = today_ist()
    if requirement.needed_by < today and requirement.status in (
        "OPEN",
        "PARTIALLY_FULFILLED",
    ):
        requirement.status = "EXPIRED"
        db.commit()
        db.refresh(requirement)
    return requirement


def build_requirement_out(req: Requirement) -> RequirementOut:
    return RequirementOut(
        id=req.id,
        buyer=BuyerSummary(
            id=req.buyer.id,
            org_name=req.buyer.org_name,
            buyer_type=req.buyer.buyer_type,
            city=req.buyer.city,
            state=req.buyer.state,
            hub_id=req.buyer.hub_id,
            lat=req.buyer.lat,
            lng=req.buyer.lng,
        ),
        crop=CropSummary(
            id=req.crop.id,
            name=req.crop.name,
            category=req.crop.category,
            shelf_life_days=req.crop.shelf_life_days,
            perishability=req.crop.perishability,
        ),
        grade_min=req.grade_min,
        quantity_kg=req.quantity_kg,
        quantity_fulfilled_kg=req.quantity_fulfilled_kg,
        max_landed_price_per_kg=float(req.max_landed_price_per_kg),
        needed_by=req.needed_by,
        status=req.status,
        notes=req.notes,
        is_demo=req.is_demo,
        created_at=req.created_at,
        landed_guidance=LandedPriceGuidance(),
    )


def create_requirement(
    db: Session, user: User, data: RequirementCreate
) -> Requirement:
    profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user.id).first()
    if not profile:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message="Buyer profile not found for current user.",
        )

    crop = db.query(Crop).filter(Crop.id == data.crop_id).first()
    if not crop:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message="Crop not found.",
            details=[
                {
                    "field": "crop_id",
                    "issue": f"Crop with id {data.crop_id} does not exist",
                }
            ],
        )

    req = Requirement(
        buyer_id=profile.id,
        crop_id=data.crop_id,
        grade_min=data.grade_min,
        quantity_kg=data.quantity_kg,
        quantity_fulfilled_kg=0.0,
        max_landed_price_per_kg=data.max_landed_price_per_kg,
        needed_by=data.needed_by,
        status="OPEN",
        notes=data.notes,
        is_demo=profile.is_demo,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def get_requirements(
    db: Session,
    user: User,
    crop_id: int | None = None,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Requirement], int]:
    query = db.query(Requirement)

    if user.role == "BUYER":
        profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user.id).first()
        if not profile:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="NOT_FOUND",
                message="Buyer profile not found.",
            )
        query = query.filter(Requirement.buyer_id == profile.id)
    elif user.role != "ADMIN":
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Access forbidden.",
        )

    if crop_id is not None:
        query = query.filter(Requirement.crop_id == crop_id)
    if status_filter is not None:
        query = query.filter(Requirement.status == status_filter)

    total = query.count()
    items = (
        query.order_by(Requirement.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    updated_items = []
    for req in items:
        evaluate_dynamic_expiry(db, req)
        updated_items.append(req)

    return updated_items, total


def get_requirement_by_id(
    db: Session, user: User, requirement_id: int
) -> Requirement:
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Requirement with id {requirement_id} not found.",
        )

    if user.role == "BUYER":
        profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user.id).first()
        if not profile or req.buyer_id != profile.id:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="You do not have permission to access this requirement.",
            )
    elif user.role != "ADMIN":
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Access forbidden.",
        )

    evaluate_dynamic_expiry(db, req)
    return req


def update_requirement(
    db: Session, user: User, requirement_id: int, data: RequirementUpdate
) -> Requirement:
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Requirement with id {requirement_id} not found.",
        )

    if user.role != "BUYER":
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only buyers can update requirements.",
        )

    profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user.id).first()
    if not profile or req.buyer_id != profile.id:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="You do not have permission to update this requirement.",
        )

    # Evaluate dynamic expiry BEFORE any mutation
    evaluate_dynamic_expiry(db, req)

    if req.status == "EXPIRED":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message="Cannot update an expired requirement.",
        )
    if req.status == "CANCELLED":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message="Cannot update a cancelled requirement.",
        )
    if req.status == "FULFILLED":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message="Cannot update a fulfilled requirement.",
        )

    if data.quantity_kg is not None:
        if data.quantity_kg < req.quantity_fulfilled_kg:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="CONFLICT",
                message=f"quantity_kg cannot be less than quantity_fulfilled_kg ({req.quantity_fulfilled_kg}).",
                details=[
                    {
                        "field": "quantity_kg",
                        "issue": f"Value {data.quantity_kg} is below fulfilled amount {req.quantity_fulfilled_kg}",
                    }
                ],
            )
        req.quantity_kg = data.quantity_kg

    if data.max_landed_price_per_kg is not None:
        req.max_landed_price_per_kg = data.max_landed_price_per_kg

    if data.needed_by is not None:
        req.needed_by = data.needed_by

    if data.notes is not None:
        req.notes = data.notes

    if data.status == "CANCELLED":
        req.status = "CANCELLED"

    db.commit()
    db.refresh(req)
    return req
