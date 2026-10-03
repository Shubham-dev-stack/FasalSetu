
from fastapi import status
from sqlalchemy import case, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dates import today_ist
from app.core.errors import AppException
from app.core.geo import road_distance_km
from app.db.models import Listing, Order, OrderEvent, Requirement, User
from app.modules.listings.service import evaluate_listing_expiry
from app.modules.logistics.cost import estimate_dedicated_trip
from app.modules.logistics.fleet import get_vehicle_types
from app.schemas.order import (
    BuyerOrderSummary,
    CropOrderSummary,
    OrderCreate,
    OrderEventOut,
    OrderListResponse,
    OrderOut,
    OrderTransitionRequest,
    ProducerOrderSummary,
)

settings = get_settings()


def build_order_out(order: Order) -> OrderOut:
    farmgate = float(order.agreed_price_per_kg)
    transport = float(order.transport_cost_estimate_per_kg)
    fee = float(order.platform_fee_per_kg)
    landed_kg = round(farmgate + transport + fee, 2)
    total_amount = round(landed_kg * float(order.quantity_kg), 2)

    return OrderOut(
        id=order.id,
        listing_id=order.listing_id,
        requirement_id=order.requirement_id,
        buyer=BuyerOrderSummary(
            id=order.buyer.id,
            org_name=order.buyer.org_name,
            hub_id=order.buyer.hub_id,
        ),
        producer=ProducerOrderSummary(
            id=order.producer.id,
            org_name=order.producer.org_name,
            district=order.producer.district,
            state=order.producer.state,
        ),
        crop=CropOrderSummary(
            id=order.crop.id,
            name=order.crop.name,
        ),
        quantity_kg=float(order.quantity_kg),
        agreed_price_per_kg=farmgate,
        transport_cost_estimate_per_kg=transport,
        platform_fee_per_kg=fee,
        landed_price_per_kg_estimate=landed_kg,
        total_amount_estimate=total_amount,
        delivery_date=order.delivery_date,
        status=order.status,
        origin=order.origin,
        shipment_id=order.shipment_id,
        allocated_transport_cost_total=(
            float(order.allocated_transport_cost_total)
            if order.allocated_transport_cost_total is not None
            else None
        ),
        events=[
            OrderEventOut(
                id=e.id,
                order_id=e.order_id,
                from_status=e.from_status,
                to_status=e.to_status,
                actor_user_id=e.actor_user_id,
                actor_role=e.actor_role,
                note=e.note,
                at=e.at,
            )
            for e in order.events
        ],
        is_demo=order.is_demo,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def create_direct_order(
    db: Session, current_user: User, data: OrderCreate
) -> OrderOut:
    if not current_user.buyer_profile:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only authenticated buyers can place direct orders.",
        )

    buyer_profile = current_user.buyer_profile

    listing = db.query(Listing).filter(Listing.id == data.listing_id).first()
    if not listing:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Listing with ID {data.listing_id} not found.",
        )

    # Dynamic expiry check on listing
    evaluate_listing_expiry(listing, db)
    if listing.status != "ACTIVE":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="LISTING_UNAVAILABLE",
            message=f"Listing is {listing.status} and cannot be ordered.",
        )

    # Validate quantity against min_order_kg
    if data.quantity_kg < float(listing.min_order_kg):
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=f"Order quantity {data.quantity_kg} kg is below minimum order quantity {listing.min_order_kg} kg.",
            details=[
                {
                    "field": "quantity_kg",
                    "issue": f"Minimum order quantity is {listing.min_order_kg} kg",
                }
            ],
        )

    # Validate quantity against current available quantity
    if data.quantity_kg > float(listing.quantity_available_kg):
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="INSUFFICIENT_QUANTITY",
            message=f"Only {listing.quantity_available_kg} kg available.",
            details=[
                {
                    "field": "quantity_kg",
                    "issue": f"max {listing.quantity_available_kg}",
                }
            ],
        )

    # Strict requirement validation if requirement_id provided (Mandatory Correction #3)
    req: Requirement | None = None
    if data.requirement_id is not None:
        req = db.query(Requirement).filter(Requirement.id == data.requirement_id).first()
        if not req:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="NOT_FOUND",
                message=f"Requirement with ID {data.requirement_id} not found.",
            )

        if req.buyer_id != buyer_profile.id:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Requirement does not belong to you.",
            )

        if req.status not in ["OPEN", "PARTIALLY_FULFILLED"]:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="INVALID_TRANSITION",
                message=f"Requirement is in {req.status} status and cannot receive fulfillments.",
            )

        # Dynamic expiry on requirement
        if req.needed_by < today_ist():
            req.status = "EXPIRED"
            db.commit()
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="CONFLICT",
                message="Requirement has expired.",
            )

        remaining_qty = float(req.quantity_kg) - float(req.quantity_fulfilled_kg)
        if remaining_qty <= 0:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="INSUFFICIENT_QUANTITY",
                message="Requirement is already fully fulfilled.",
            )

        if data.quantity_kg > remaining_qty:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message=f"Order quantity {data.quantity_kg} kg exceeds remaining requirement requirement quantity {remaining_qty} kg.",
                details=[
                    {
                        "field": "quantity_kg",
                        "issue": f"Exceeds remaining requirement quantity {remaining_qty} kg",
                    }
                ],
            )

        if listing.crop_id != req.crop_id:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message="Listing crop does not match requirement crop.",
                details=[
                    {
                        "field": "crop_id",
                        "issue": f"Listing crop ID {listing.crop_id} does not match requirement crop ID {req.crop_id}",
                    }
                ],
            )

        # Grade hierarchy check: A > B > C
        grade_ranks = {"A": 3, "B": 2, "C": 1}
        listing_rank = grade_ranks.get(listing.grade, 0)
        req_min_rank = grade_ranks.get(req.grade_min, 0)
        if listing_rank < req_min_rank:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message=f"Listing grade {listing.grade} does not satisfy requirement minimum grade {req.grade_min}.",
                details=[
                    {
                        "field": "grade",
                        "issue": f"Grade {listing.grade} is below minimum grade {req.grade_min}",
                    }
                ],
            )

    # Logistics and Landed Price Calculation
    # Transport estimate calculated strictly using requested order quantity (Mandatory Correction #2)
    dist_km = road_distance_km(
        (listing.producer.lat, listing.producer.lng),
        (buyer_profile.lat, buyer_profile.lng),
        circuity=settings.ROAD_CIRCUITY_FACTOR,
    )
    vehicle_types = get_vehicle_types(db)
    trip_est = estimate_dedicated_trip(dist_km, data.quantity_kg, vehicle_types)
    transport_cost_estimate_per_kg = trip_est["cost_per_kg"]

    # Snapshot financial values onto Order record (Mandatory Correction #6)
    agreed_price_per_kg = float(listing.ask_price_per_kg)
    platform_fee_per_kg = round(agreed_price_per_kg * 0.02, 2)
    landed_price_per_kg_estimate = round(
        agreed_price_per_kg + transport_cost_estimate_per_kg + platform_fee_per_kg, 2
    )

    # Validate landed price against requirement budget if linked
    if req is not None and landed_price_per_kg_estimate > float(req.max_landed_price_per_kg):
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=f"Landed price ₹{landed_price_per_kg_estimate}/kg exceeds requirement max landed budget ₹{req.max_landed_price_per_kg}/kg.",
            details=[
                {
                    "field": "max_landed_price_per_kg",
                    "issue": f"Landed price ₹{landed_price_per_kg_estimate} exceeds max ₹{req.max_landed_price_per_kg}",
                }
            ],
        )

    # Concurrency-safe atomic reservation on Listing (Mandatory Correction #4 & AC-ORD-01/04)
    today = today_ist()
    result = db.execute(
        update(Listing)
        .where(
            Listing.id == listing.id,
            Listing.quantity_available_kg >= data.quantity_kg,
            Listing.status == "ACTIVE",
            Listing.available_until >= today,
        )
        .values(
            quantity_available_kg=case(
                (Listing.quantity_available_kg - data.quantity_kg <= 0.001, 0.0),
                else_=Listing.quantity_available_kg - data.quantity_kg,
            ),
            status=case(
                (Listing.quantity_available_kg - data.quantity_kg <= 0.001, "SOLD_OUT"),
                else_="ACTIVE",
            ),
        )
    )

    if result.rowcount == 0:
        db.refresh(listing)
        if listing.quantity_available_kg < data.quantity_kg:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="INSUFFICIENT_QUANTITY",
                message=f"Only {listing.quantity_available_kg} kg available.",
                details=[
                    {
                        "field": "quantity_kg",
                        "issue": f"max {listing.quantity_available_kg}",
                    }
                ],
            )
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="LISTING_UNAVAILABLE",
            message="Listing is no longer available.",
        )

    # Concurrency-safe fulfillment update on Requirement if linked (Mandatory Correction #4)
    if req is not None:
        req_result = db.execute(
            update(Requirement)
            .where(
                Requirement.id == req.id,
                Requirement.quantity_fulfilled_kg + data.quantity_kg <= Requirement.quantity_kg,
                Requirement.status.in_(["OPEN", "PARTIALLY_FULFILLED"]),
            )
            .values(
                quantity_fulfilled_kg=Requirement.quantity_fulfilled_kg + data.quantity_kg,
                status=case(
                    (
                        Requirement.quantity_fulfilled_kg + data.quantity_kg >= Requirement.quantity_kg,
                        "FULFILLED",
                    ),
                    else_="PARTIALLY_FULFILLED",
                ),
            )
        )
        if req_result.rowcount == 0:
            db.rollback()
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="INSUFFICIENT_QUANTITY",
                message="Requirement fulfillment capacity exceeded.",
            )

    # Create Order
    order = Order(
        listing_id=listing.id,
        requirement_id=data.requirement_id,
        buyer_id=buyer_profile.id,
        producer_id=listing.producer_id,
        crop_id=listing.crop_id,
        quantity_kg=data.quantity_kg,
        agreed_price_per_kg=agreed_price_per_kg,
        transport_cost_estimate_per_kg=transport_cost_estimate_per_kg,
        platform_fee_per_kg=platform_fee_per_kg,
        delivery_date=data.delivery_date,
        status="PLACED",
        origin="MARKETPLACE",
        shipment_id=None,
        allocated_transport_cost_total=None,
        is_demo=current_user.is_demo,
    )
    db.add(order)
    db.flush()

    # Create initial OrderEvent
    event = OrderEvent(
        order_id=order.id,
        from_status=None,
        to_status="PLACED",
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        note="Marketplace direct purchase",
    )
    db.add(event)
    db.commit()
    db.refresh(order)

    return build_order_out(order)


def transition_order_status(
    db: Session, order_id: int, current_user: User, data: OrderTransitionRequest
) -> OrderOut:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Order with ID {order_id} not found.",
        )

    current_status = order.status
    to_status = data.to_status
    user_role = current_user.role
    is_admin = user_role == "ADMIN"

    # Enforce Transition Matrix (API.md §7)
    if current_status == "PLACED":
        if to_status == "CONFIRMED":
            # Owning PRODUCER or ADMIN
            is_producer_owner = (
                user_role == "PRODUCER"
                and current_user.producer_profile is not None
                and order.producer_id == current_user.producer_profile.id
            )
            if not (is_producer_owner or is_admin):
                raise AppException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code="FORBIDDEN",
                    message="Only the selling producer or operator can confirm this order.",
                )
            order.status = "CONFIRMED"

        elif to_status == "REJECTED":
            # Owning PRODUCER or ADMIN
            is_producer_owner = (
                user_role == "PRODUCER"
                and current_user.producer_profile is not None
                and order.producer_id == current_user.producer_profile.id
            )
            if not (is_producer_owner or is_admin):
                raise AppException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code="FORBIDDEN",
                    message="Only the selling producer or operator can reject this order.",
                )
            order.status = "REJECTED"
            _release_order_inventory_and_fulfillment(db, order)

        elif to_status == "CANCELLED":
            # Owning BUYER or ADMIN
            is_buyer_owner = (
                user_role == "BUYER"
                and current_user.buyer_profile is not None
                and order.buyer_id == current_user.buyer_profile.id
            )
            if not (is_buyer_owner or is_admin):
                raise AppException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code="FORBIDDEN",
                    message="Only the ordering buyer or operator can cancel this order.",
                )
            order.status = "CANCELLED"
            _release_order_inventory_and_fulfillment(db, order)

        else:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="INVALID_TRANSITION",
                message=f"Invalid transition from {current_status} to {to_status}.",
            )

    elif current_status == "CONFIRMED":
        if to_status == "CANCELLED":
            # Owning BUYER, owning PRODUCER, or ADMIN — only while shipment_id is null
            if order.shipment_id is not None:
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="INVALID_TRANSITION",
                    message="Cannot cancel order after shipment has been planned or dispatched.",
                )

            is_buyer_owner = (
                user_role == "BUYER"
                and current_user.buyer_profile is not None
                and order.buyer_id == current_user.buyer_profile.id
            )
            is_producer_owner = (
                user_role == "PRODUCER"
                and current_user.producer_profile is not None
                and order.producer_id == current_user.producer_profile.id
            )
            if not (is_buyer_owner or is_producer_owner or is_admin):
                raise AppException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code="FORBIDDEN",
                    message="You do not have permission to cancel this confirmed order.",
                )

            order.status = "CANCELLED"
            _release_order_inventory_and_fulfillment(db, order)
        else:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="INVALID_TRANSITION",
                message=f"Invalid transition from {current_status} to {to_status}.",
            )

    else:
        # Terminal states or shipment-managed states
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="INVALID_TRANSITION",
            message=f"Order in status {current_status} cannot be transitioned via this endpoint.",
        )

    # Log order event
    event = OrderEvent(
        order_id=order.id,
        from_status=current_status,
        to_status=to_status,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        note=data.note,
    )
    db.add(event)
    db.commit()
    db.refresh(order)

    return build_order_out(order)


def _release_order_inventory_and_fulfillment(db: Session, order: Order) -> None:
    """Restores reserved inventory and reverses requirement fulfillment safely."""
    today = today_ist()

    # Restore listing quantity_available_kg
    db.execute(
        update(Listing)
        .where(Listing.id == order.listing_id)
        .values(
            quantity_available_kg=Listing.quantity_available_kg + order.quantity_kg,
            status=case(
                (Listing.available_until >= today, "ACTIVE"),
                else_="EXPIRED",
            ),
        )
    )

    # Restore requirement fulfillment if linked (never negative)
    if order.requirement_id is not None:
        db.execute(
            update(Requirement)
            .where(Requirement.id == order.requirement_id)
            .values(
                quantity_fulfilled_kg=case(
                    (
                        Requirement.quantity_fulfilled_kg - order.quantity_kg <= 0.0,
                        0.0,
                    ),
                    else_=Requirement.quantity_fulfilled_kg - order.quantity_kg,
                ),
                status=case(
                    (
                        Requirement.quantity_fulfilled_kg - order.quantity_kg <= 0.0,
                        "OPEN",
                    ),
                    else_="PARTIALLY_FULFILLED",
                ),
            )
        )


def get_order_detail(db: Session, order_id: int, current_user: User) -> OrderOut:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Order with ID {order_id} not found.",
        )

    # Object-level authorization check
    if current_user.role == "BUYER":
        if not current_user.buyer_profile or order.buyer_id != current_user.buyer_profile.id:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="You do not have permission to view this order.",
            )
    elif current_user.role == "PRODUCER":
        if not current_user.producer_profile or order.producer_id != current_user.producer_profile.id:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="You do not have permission to view this order.",
            )
    elif current_user.role == "ADMIN":
        pass  # Operator can view all orders
    else:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Forbidden.",
        )

    return build_order_out(order)


def list_orders(
    db: Session,
    current_user: User,
    status_filter: str | None = None,
    crop_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> OrderListResponse:
    query = db.query(Order)

    # Role scoping
    if current_user.role == "BUYER":
        if not current_user.buyer_profile:
            return OrderListResponse(items=[], total=0)
        query = query.filter(Order.buyer_id == current_user.buyer_profile.id)
    elif current_user.role == "PRODUCER":
        if not current_user.producer_profile:
            return OrderListResponse(items=[], total=0)
        query = query.filter(Order.producer_id == current_user.producer_profile.id)
    elif current_user.role == "ADMIN":
        pass  # Admin sees all
    else:
        return OrderListResponse(items=[], total=0)

    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Order.status == status_filter.upper())

    if crop_id is not None:
        query = query.filter(Order.crop_id == crop_id)

    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()

    return OrderListResponse(
        items=[build_order_out(o) for o in orders],
        total=total,
    )
