from datetime import timedelta

from fastapi import status
from sqlalchemy.orm import Session

from app.core.dates import today_ist
from app.core.errors import AppException
from app.core.geo import haversine_km, road_distance_km
from app.db.models import Crop, DemandHub, Listing, MarketPrice, ProducerProfile, User
from app.modules.logistics.cost import estimate_dedicated_trip
from app.modules.logistics.fleet import get_vehicle_types
from app.schemas.listing import (
    BenchmarkContext,
    CropSummary,
    LandedEstimate,
    ListingCreate,
    ListingCreateResponse,
    ListingDetailResponse,
    ListingListResponse,
    ListingOut,
    ListingUpdate,
    ProducerSummary,
)


def get_nearest_hub_and_benchmark(
    db: Session, lat: float, lng: float, crop_id: int
) -> tuple[DemandHub | None, float | None, str | None]:
    """Find the nearest demand hub to (lat, lng) and look up the latest market price

    prioritizing AGMARKNET_SNAPSHOT (is_synthetic=False) over SYNTHETIC_DEMO (is_synthetic=True).
    """
    hubs = db.query(DemandHub).all()
    if not hubs:
        return None, None, None

    nearest_hub = min(
        hubs, key=lambda h: haversine_km(lat, lng, h.lat, h.lng)
    )


    today = today_ist()
    # 1. Real Agmarknet snapshot check (within last 30 days)
    real_price = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.hub_id == nearest_hub.id,
            MarketPrice.crop_id == crop_id,
            MarketPrice.is_synthetic.is_(False),
            MarketPrice.source == "AGMARKNET_SNAPSHOT",
            MarketPrice.price_date <= today,
            MarketPrice.price_date >= today - timedelta(days=30),
        )
        .order_by(MarketPrice.price_date.desc())
        .first()
    )
    if real_price:
        return (
            nearest_hub,
            float(real_price.modal_price_per_kg),
            "AGMARKNET_SNAPSHOT",
        )

    # 2. Synthetic demo benchmark price
    synthetic_price = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.hub_id == nearest_hub.id,
            MarketPrice.crop_id == crop_id,
            MarketPrice.is_synthetic.is_(True),
            MarketPrice.source == "SYNTHETIC_DEMO",
            MarketPrice.price_date <= today,
        )
        .order_by(MarketPrice.price_date.desc())
        .first()
    )
    if synthetic_price:
        return (
            nearest_hub,
            float(synthetic_price.modal_price_per_kg),
            "SYNTHETIC_DEMO",
        )

    return nearest_hub, None, None


def evaluate_listing_expiry(listing: Listing, db: Session | None = None) -> Listing:
    """Evaluate query-time expiration (Rule D-021)."""
    if listing.status == "ACTIVE" and listing.available_until < today_ist():
        listing.status = "EXPIRED"
        if db:
            db.add(listing)
            db.commit()
    return listing


def build_listing_out(
    listing: Listing, landed_estimate: LandedEstimate | None = None
) -> ListingOut:
    today = today_ist()
    harvest_age_days = max(0, (today - listing.harvest_date).days)

    return ListingOut(
        id=listing.id,
        producer=ProducerSummary.model_validate(listing.producer),
        crop=CropSummary.model_validate(listing.crop),
        variety=listing.variety,
        grade=listing.grade,
        quantity_kg=float(listing.quantity_kg),
        quantity_available_kg=float(listing.quantity_available_kg),
        ask_price_per_kg=float(listing.ask_price_per_kg),
        min_order_kg=float(listing.min_order_kg),
        harvest_date=listing.harvest_date,
        available_from=listing.available_from,
        available_until=listing.available_until,
        status=listing.status,
        is_demo=listing.is_demo,
        harvest_age_days=harvest_age_days,
        landed_estimate=landed_estimate,
        demand_status=None,
        created_at=listing.created_at,
    )


def create_listing(
    db: Session, current_user: User, data: ListingCreate
) -> ListingCreateResponse:
    if not current_user.producer_profile:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="User has no associated producer profile.",
        )

    crop = db.query(Crop).filter(Crop.id == data.crop_id).first()
    if not crop:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=f"Crop with ID {data.crop_id} does not exist.",
            details=[{"field": "crop_id", "issue": "Unknown crop ID"}],
        )

    profile = current_user.producer_profile
    nearest_hub, benchmark_modal, benchmark_src = get_nearest_hub_and_benchmark(
        db, profile.lat, profile.lng, data.crop_id
    )

    warnings: list[str] = []
    if benchmark_modal and data.ask_price_per_kg > 3 * benchmark_modal:
        warnings.append("PRICE_FAR_ABOVE_BENCHMARK")

    listing = Listing(
        producer_id=profile.id,
        crop_id=data.crop_id,
        variety=data.variety,
        grade=data.grade,
        quantity_kg=data.quantity_kg,
        quantity_available_kg=data.quantity_kg,
        ask_price_per_kg=data.ask_price_per_kg,
        min_order_kg=data.min_order_kg,
        harvest_date=data.harvest_date,
        available_from=data.available_from,
        available_until=data.available_until,
        status="ACTIVE",
        is_demo=current_user.is_demo,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    benchmark_context = BenchmarkContext(
        nearest_hub_name=nearest_hub.name if nearest_hub else None,
        benchmark_modal_per_kg=benchmark_modal,
        benchmark_source=benchmark_src,
    )

    return ListingCreateResponse(
        listing=build_listing_out(listing),
        warnings=warnings,
        benchmark_context=benchmark_context,
    )


def compute_listing_landed_estimate(
    listing: Listing,
    b_lat: float,
    b_lng: float,
    vehicle_types: list[dict],
) -> LandedEstimate:
    p_lat = listing.producer.lat
    p_lng = listing.producer.lng
    dist_km = road_distance_km((p_lat, p_lng), (b_lat, b_lng), circuity=1.35)
    rep_qty = float(listing.min_order_kg)
    trip_est = estimate_dedicated_trip(dist_km, rep_qty, vehicle_types)
    transport_per_kg = trip_est["cost_per_kg"]
    fee_per_kg = round(float(listing.ask_price_per_kg) * 0.02, 2)
    landed_per_kg = round(float(listing.ask_price_per_kg) + transport_per_kg + fee_per_kg, 2)
    return LandedEstimate(
        distance_km=dist_km,
        distance_source="ESTIMATED_HAVERSINE",
        transport_cost_per_kg=transport_per_kg,
        platform_fee_per_kg=fee_per_kg,
        landed_price_per_kg=landed_per_kg,
        basis="ESTIMATE",
    )


def get_listing_detail(
    db: Session,
    listing_id: int,
    current_user: User | None = None,
    buyer_lat: float | None = None,
    buyer_lng: float | None = None,
) -> ListingDetailResponse:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Listing with ID {listing_id} not found.",
        )

    evaluate_listing_expiry(listing, db)

    nearest_hub, benchmark_modal, benchmark_src = get_nearest_hub_and_benchmark(
        db, listing.producer.lat, listing.producer.lng, listing.crop_id
    )

    benchmark_context = BenchmarkContext(
        nearest_hub_name=nearest_hub.name if nearest_hub else None,
        benchmark_modal_per_kg=benchmark_modal,
        benchmark_source=benchmark_src,
    )

    b_lat = buyer_lat
    b_lng = buyer_lng
    if b_lat is None and current_user and current_user.buyer_profile:
        b_lat = current_user.buyer_profile.lat
        b_lng = current_user.buyer_profile.lng

    landed_estimate = None
    if b_lat is not None and b_lng is not None:
        vehicle_types = get_vehicle_types(db)
        landed_estimate = compute_listing_landed_estimate(listing, b_lat, b_lng, vehicle_types)

    return ListingDetailResponse(
        listing=build_listing_out(listing, landed_estimate=landed_estimate),
        benchmark_context=benchmark_context,
    )


def update_listing(
    db: Session, listing_id: int, current_user: User, data: ListingUpdate
) -> ListingOut:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Listing with ID {listing_id} not found.",
        )

    # Object-level authorization (AC-SEC-03, AC-LST-06)
    if (
        not current_user.producer_profile
        or listing.producer_id != current_user.producer_profile.id
    ):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="You do not own this produce listing.",
        )

    evaluate_listing_expiry(listing, db)

    # Status check: SOLD_OUT and EXPIRED listings cannot be edited except to withdraw
    if listing.status in ["SOLD_OUT", "EXPIRED"] and data.status != "WITHDRAWN":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="LISTING_UNAVAILABLE",
            message=f"Cannot edit listing in {listing.status} state except to withdraw.",
        )

    if listing.status == "WITHDRAWN":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="LISTING_UNAVAILABLE",
            message="Withdrawn listings cannot be modified.",
        )

    # Reserved quantity validation
    reserved_kg = listing.quantity_kg - listing.quantity_available_kg
    if data.quantity_kg is not None:
        if data.quantity_kg < reserved_kg:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="LISTING_UNAVAILABLE",
                message=f"Cannot reduce total quantity ({data.quantity_kg} kg) below already reserved volume ({reserved_kg} kg).",
            )
        listing.quantity_available_kg = data.quantity_kg - reserved_kg
        listing.quantity_kg = data.quantity_kg

    if data.min_order_kg is not None:
        if data.min_order_kg > listing.quantity_kg:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message="min_order_kg cannot exceed quantity_kg.",
                details=[{"field": "min_order_kg", "issue": "Exceeds total quantity"}],
            )
        listing.min_order_kg = data.min_order_kg

    if data.ask_price_per_kg is not None:
        listing.ask_price_per_kg = data.ask_price_per_kg

    if data.available_until is not None:
        listing.available_until = data.available_until

    if data.status == "WITHDRAWN":
        listing.status = "WITHDRAWN"

    db.commit()
    db.refresh(listing)

    return build_listing_out(listing)


def list_listings(
    db: Session,
    current_user: User | None = None,
    crop_id: int | None = None,
    grade_min: str | None = None,
    state: str | None = None,
    max_price: float | None = None,
    harvested_within_days: int | None = None,
    status_filter: str | None = "ACTIVE",
    mine: bool = False,
    sort: str | None = None,
    buyer_lat: float | None = None,
    buyer_lng: float | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ListingListResponse:
    query = db.query(Listing).join(ProducerProfile).join(Crop)

    # Evaluate expiry on active listings queried
    # Mine filter check
    if mine:
        if not current_user or current_user.role != "PRODUCER" or not current_user.producer_profile:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="mine=true is only allowed for authenticated producers.",
            )
        query = query.filter(Listing.producer_id == current_user.producer_profile.id)
    else:
        # Marketplace view
        if status_filter and status_filter.upper() == "ACTIVE":
            # Rule AC-LST-07: Exclude expired, withdrawn, or sold-out listings
            today = today_ist()
            query = query.filter(
                Listing.status == "ACTIVE",
                Listing.available_until >= today,
                Listing.quantity_available_kg > 0,
            )

    if status_filter and status_filter.upper() != "ALL" and not (not mine and status_filter.upper() == "ACTIVE"):
        query = query.filter(Listing.status == status_filter.upper())

    if crop_id is not None:
        query = query.filter(Listing.crop_id == crop_id)

    if grade_min:
        allowed_grades = {"A": ["A"], "B": ["A", "B"], "C": ["A", "B", "C"]}.get(
            grade_min.upper(), ["A", "B", "C"]
        )
        query = query.filter(Listing.grade.in_(allowed_grades))

    if state:
        query = query.filter(ProducerProfile.state.ilike(f"%{state}%"))

    if max_price is not None:
        query = query.filter(Listing.ask_price_per_kg <= max_price)

    if harvested_within_days is not None:
        min_harvest = today_ist() - timedelta(days=harvested_within_days)
        query = query.filter(Listing.harvest_date >= min_harvest)

    b_lat = buyer_lat
    b_lng = buyer_lng
    if b_lat is None and current_user and current_user.buyer_profile:
        b_lat = current_user.buyer_profile.lat
        b_lng = current_user.buyer_profile.lng

    # Sorting
    if sort == "price":
        query = query.order_by(Listing.ask_price_per_kg.asc())
    elif sort == "freshness":
        query = query.order_by(Listing.harvest_date.desc())
    elif sort in ["landed", "distance"] and b_lat is not None and b_lng is not None:
        # Distance and Landed sorting require in-memory calculation
        pass
    else:
        query = query.order_by(Listing.created_at.desc())

    if b_lat is not None and b_lng is not None:
        vehicle_types = get_vehicle_types(db)
        if sort in ["landed", "distance"]:
            all_candidates = query.all()
            with_est = []
            for item in all_candidates:
                evaluate_listing_expiry(item, db)
                est = compute_listing_landed_estimate(item, b_lat, b_lng, vehicle_types)
                with_est.append((item, est))

            if sort == "landed":
                with_est.sort(key=lambda x: x[1].landed_price_per_kg)
            elif sort == "distance":
                with_est.sort(key=lambda x: x[1].distance_km)

            total = len(with_est)
            paged = with_est[offset : offset + limit]
            items = [build_listing_out(item, landed_estimate=est) for item, est in paged]
            return ListingListResponse(items=items, total=total)
        else:
            total = query.count()
            listings = query.offset(offset).limit(limit).all()
            items = []
            for item in listings:
                evaluate_listing_expiry(item, db)
                est = compute_listing_landed_estimate(item, b_lat, b_lng, vehicle_types)
                items.append(build_listing_out(item, landed_estimate=est))
            return ListingListResponse(items=items, total=total)

    total = query.count()
    listings = query.offset(offset).limit(limit).all()

    # Dynamic expiry check for fetched listings
    items: list[ListingOut] = []
    for item in listings:
        evaluate_listing_expiry(item, db)
        items.append(build_listing_out(item))

    return ListingListResponse(items=items, total=total)

