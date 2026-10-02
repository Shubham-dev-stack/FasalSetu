import math
from datetime import timedelta
from typing import Any

from fastapi import status
from sqlalchemy import case, update
from sqlalchemy.orm import Session

from app.core.dates import today_ist
from app.core.errors import AppException
from app.core.geo import road_distance_km
from app.db.models import Crop, Listing, Order, OrderEvent, Requirement, User
from app.modules.listings.service import evaluate_listing_expiry
from app.modules.logistics.cost import estimate_dedicated_trip
from app.modules.logistics.fleet import get_vehicle_types
from app.modules.matching.scoring import (
    GRADE_RANKS,
    compute_scores,
    evaluate_hard_filters,
    generate_reasons,
    load_matching_config,
)
from app.modules.orders.service import build_order_out
from app.schemas.matching import (
    AllocationItem,
    CandidateListingSummary,
    CandidateOut,
    CandidateProducerSummary,
    HubForecastContext,
    MatchingAcceptRequest,
    MatchingAcceptRequirementOut,
    MatchingAcceptResponse,
    MatchingScores,
    MatchingWeights,
    NearMissOut,
    OpportunityBuyerSummary,
    OpportunityListingSummary,
    OpportunityOut,
    OpportunityRequirementSummary,
    ProducerOpportunitiesResponse,
    RequirementCandidatesResponse,
    RequirementSummary,
)
from app.schemas.order import CropOrderSummary


def get_requirement_candidates(
    db: Session,
    requirement_id: int,
    current_user: User,
    max_results: int = 10,
) -> RequirementCandidatesResponse:
    # 1. Authorization check
    # Owner BUYER or ADMIN allowed
    if current_user.role != "ADMIN":
        if not current_user.buyer_profile:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Only buyers or operators can view requirement matching candidates.",
            )

    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Requirement with ID {requirement_id} not found.",
        )

    if current_user.role != "ADMIN" and current_user.buyer_profile:
        if req.buyer_id != current_user.buyer_profile.id:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="You do not own this requirement.",
            )

    today = today_ist()

    # Dynamic expiry evaluation
    if req.needed_by < today:
        req.status = "EXPIRED"
        db.commit()
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message="Requirement has expired.",
        )

    if req.status in ["CANCELLED", "EXPIRED"]:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message=f"Requirement is {req.status} and cannot be matched.",
        )

    rem_qty = float(req.quantity_kg) - float(req.quantity_fulfilled_kg)
    if rem_qty <= 0:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message="Requirement is already fully fulfilled.",
        )

    buyer = req.buyer
    buyer_coords = (buyer.lat, buyer.lng)

    # 2. Query potential candidate produce listings of same crop
    crop = db.query(Crop).filter(Crop.id == req.crop_id).first()
    if not crop:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Crop with ID {req.crop_id} not found.",
        )

    listings = (
        db.query(Listing)
        .filter(
            Listing.crop_id == req.crop_id,
            Listing.status == "ACTIVE",
            Listing.available_until >= today,
            Listing.quantity_available_kg >= 1.0,
        )
        .all()
    )

    cfg = load_matching_config()
    vehicle_types = get_vehicle_types(db)

    eligible_candidates: list[dict[str, Any]] = []
    near_misses: list[NearMissOut] = []

    for listing in listings:
        # Check query-time listing expiry
        evaluate_listing_expiry(listing, today)
        if listing.status != "ACTIVE":
            continue

        producer = listing.producer
        if not producer:
            continue
        producer_coords = (producer.lat, producer.lng)

        passed, fail_reason, fail_detail, metrics = evaluate_hard_filters(
            listing=listing,
            requirement=req,
            crop=crop,
            producer_coords=producer_coords,
            buyer_coords=buyer_coords,
            remaining_qty=rem_qty,
            vehicle_types=vehicle_types,
            cfg=cfg,
            today=today,
        )

        if not passed:
            near_misses.append(
                NearMissOut(
                    listing_id=listing.id,
                    excluded_reason=fail_reason,  # type: ignore
                    detail=fail_detail or "Failed filter",
                    landed_price_per_kg=metrics.get("landed_price_per_kg"),
                    distance_km=metrics.get("distance_km"),
                )
            )
            continue

        # Compute deterministic score
        scores, weights = compute_scores(
            landed_price=metrics["landed_price_per_kg"],
            max_landed_budget=float(req.max_landed_price_per_kg),
            distance_km=metrics["distance_km"],
            age_at_delivery_days=metrics["age_at_delivery"],
            shelf_life_days=crop.shelf_life_days,
            available_qty=float(listing.quantity_available_kg),
            requirement_qty=float(req.quantity_kg),
            cfg=cfg,
        )

        reasons = generate_reasons(
            landed_price=metrics["landed_price_per_kg"],
            max_landed_budget=float(req.max_landed_price_per_kg),
            distance_km=metrics["distance_km"],
            transit_hours=metrics["transit_hours"],
            age_at_delivery_days=metrics["age_at_delivery"],
            shelf_life_days=crop.shelf_life_days,
            available_qty=float(listing.quantity_available_kg),
            requirement_qty=float(req.quantity_kg),
        )

        eligible_candidates.append(
            {
                "listing": listing,
                "producer": producer,
                "available_kg": float(listing.quantity_available_kg),
                "distance_km": metrics["distance_km"],
                "transit_hours": metrics["transit_hours"],
                "earliest_delivery": metrics["earliest_delivery"],
                "age_at_delivery": metrics["age_at_delivery"],
                "ask_price_per_kg": metrics["ask_price_per_kg"],
                "transport_cost_per_kg": metrics["transport_cost_per_kg"],
                "platform_fee_per_kg": metrics["platform_fee_per_kg"],
                "landed_price_per_kg": metrics["landed_price_per_kg"],
                "scores": scores,
                "weights": weights,
                "reasons": reasons,
                "allocated_kg": 0.0,
            }
        )

    # 3. Deterministic Sorting:
    # 1. higher total_score (descending)
    # 2. lower landed_price_per_kg (ascending)
    # 3. lower listing_id (ascending)
    eligible_candidates.sort(
        key=lambda c: (
            -c["scores"]["total"],
            c["landed_price_per_kg"],
            c["listing"].id,
        )
    )

    # 4. Greedy Multi-Source Allocation
    remaining = rem_qty
    allocations: list[AllocationItem] = []

    for cand in eligible_candidates:
        if remaining <= 0:
            break

        avail = cand["available_kg"]
        q = min(avail, remaining)
        min_order = float(cand["listing"].min_order_kg)

        if q < min_order:
            # Below min order skip
            cand["allocated_kg"] = 0.0
            near_misses.append(
                NearMissOut(
                    listing_id=cand["listing"].id,
                    excluded_reason="BELOW_MIN_ORDER",
                    detail=f"Allocatable {q:,.0f} kg is below min order {min_order:,.0f} kg",
                    landed_price_per_kg=cand["landed_price_per_kg"],
                    distance_km=cand["distance_km"],
                )
            )
            continue

        cand["allocated_kg"] = q
        allocations.append(AllocationItem(listing_id=cand["listing"].id, quantity_kg=q))
        remaining -= q

    fulfilled_kg = round(rem_qty - remaining, 2)
    shortfall_kg = round(remaining, 2)

    if shortfall_kg <= 0.001:
        fill_status = "FULL"
        shortfall_kg = 0.0
    elif fulfilled_kg > 0:
        fill_status = "PARTIAL"
    else:
        fill_status = "NONE"

    # Truncate candidates to max_results and build candidate output objects
    clamped_max_results = min(max(1, max_results), 25)
    candidate_outs: list[CandidateOut] = []

    for rank_idx, cand in enumerate(eligible_candidates[:clamped_max_results], start=1):
        l_obj = cand["listing"]
        p_obj = cand["producer"]
        candidate_outs.append(
            CandidateOut(
                rank=rank_idx,
                listing=CandidateListingSummary(
                    id=l_obj.id,
                    producer=CandidateProducerSummary(
                        id=p_obj.id,
                        org_name=p_obj.org_name,
                        producer_type=p_obj.producer_type,
                        district=p_obj.district,
                        state=p_obj.state,
                    ),
                    grade=l_obj.grade,
                    ask_price_per_kg=float(l_obj.ask_price_per_kg),
                    harvest_date=l_obj.harvest_date,
                    available_from=l_obj.available_from,
                    available_until=l_obj.available_until,
                    min_order_kg=float(l_obj.min_order_kg),
                ),
                available_kg=cand["available_kg"],
                allocated_kg=cand["allocated_kg"],
                distance_km=round(cand["distance_km"], 1),
                distance_source="ESTIMATED_HAVERSINE",
                transit_hours=round(cand["transit_hours"], 1),
                age_at_delivery_days=cand["age_at_delivery"],
                ask_price_per_kg=cand["ask_price_per_kg"],
                transport_cost_per_kg=cand["transport_cost_per_kg"],
                platform_fee_per_kg=cand["platform_fee_per_kg"],
                landed_price_per_kg=cand["landed_price_per_kg"],
                scores=MatchingScores(**cand["scores"]),
                weights=MatchingWeights(**cand["weights"]),
                reasons=cand["reasons"],
            )
        )

    # Calculate earliest delivery date among allocated candidates
    earliest_delivery_date = None
    if eligible_candidates:
        earliest_delivery_date = min(c["earliest_delivery"] for c in eligible_candidates)

    # Near misses capped at 5
    trimmed_near_misses = near_misses[:5]

    return RequirementCandidatesResponse(
        requirement=RequirementSummary(
            id=req.id,
            crop=CropOrderSummary(id=crop.id, name=crop.name),
            grade_min=req.grade_min,
            quantity_kg=float(req.quantity_kg),
            quantity_fulfilled_kg=float(req.quantity_fulfilled_kg),
            max_landed_price_per_kg=float(req.max_landed_price_per_kg),
            needed_by=req.needed_by,
            status=req.status,
        ),
        fill_status=fill_status,  # type: ignore
        requested_kg=float(req.quantity_kg),
        fulfilled_kg=fulfilled_kg,
        shortfall_kg=shortfall_kg,
        earliest_delivery_date=earliest_delivery_date,
        allocations=allocations,
        candidates=candidate_outs,
        near_misses=trimmed_near_misses,
    )


def accept_matching_allocation(
    db: Session,
    current_user: User,
    data: MatchingAcceptRequest,
) -> MatchingAcceptResponse:
    # 1. Authorization: Authenticated BUYER only
    if not current_user.buyer_profile:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only authenticated buyers can accept matching allocations.",
        )

    buyer_profile = current_user.buyer_profile

    # 2. Requirement validation
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
            message="You do not own this requirement.",
        )

    if req.status not in ["OPEN", "PARTIALLY_FULFILLED"]:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="INVALID_TRANSITION",
            message=f"Requirement is in {req.status} status and cannot receive fulfillments.",
        )

    today = today_ist()
    if req.needed_by < today:
        req.status = "EXPIRED"
        db.commit()
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message="Requirement has expired.",
        )

    if data.delivery_date < today:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Delivery date cannot be in the past.",
        )

    if data.delivery_date > req.needed_by:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=f"Delivery date {data.delivery_date} cannot be after requirement needed by date {req.needed_by}.",
        )

    if not data.allocations:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Allocations list cannot be empty.",
        )

    rem_req_qty = float(req.quantity_kg) - float(req.quantity_fulfilled_kg)
    total_alloc_qty = sum(a.quantity_kg for a in data.allocations)
    if total_alloc_qty > rem_req_qty + 0.001:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=f"Total allocated quantity {total_alloc_qty} kg exceeds remaining requirement quantity {rem_req_qty} kg.",
        )

    vehicle_types = get_vehicle_types(db)

    # 3. Transactional Re-verification & Feasibility Check
    # Never trust client parameters; re-verify every line against current DB state
    created_orders: list[Order] = []

    try:
        for alloc in data.allocations:
            listing = db.query(Listing).filter(Listing.id == alloc.listing_id).first()
            if not listing or listing.status != "ACTIVE":
                db.rollback()
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="STALE_ALLOCATION",
                    message=f"Listing {alloc.listing_id} is no longer active.",
                )

            evaluate_listing_expiry(listing, today)
            if listing.status != "ACTIVE":
                db.rollback()
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="STALE_ALLOCATION",
                    message=f"Listing {alloc.listing_id} has expired.",
                )

            if listing.crop_id != req.crop_id:
                db.rollback()
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="STALE_ALLOCATION",
                    message=f"Listing {alloc.listing_id} crop does not match requirement.",
                )

            l_rank = GRADE_RANKS.get(listing.grade, 0)
            r_rank = GRADE_RANKS.get(req.grade_min, 0)
            if l_rank < r_rank:
                db.rollback()
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="STALE_ALLOCATION",
                    message=f"Listing {alloc.listing_id} grade {listing.grade} does not satisfy requirement min grade {req.grade_min}.",
                )

            if float(listing.quantity_available_kg) < alloc.quantity_kg:
                db.rollback()
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="STALE_ALLOCATION",
                    message=f"Listing {alloc.listing_id} availability has changed. Required: {alloc.quantity_kg} kg, Available: {listing.quantity_available_kg} kg.",
                )

            if alloc.quantity_kg < float(listing.min_order_kg):
                db.rollback()
                raise AppException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code="VALIDATION_ERROR",
                    message=f"Allocated quantity {alloc.quantity_kg} kg is below min order {listing.min_order_kg} kg.",
                )

            dist_km = road_distance_km(
                (listing.producer.lat, listing.producer.lng),
                (buyer_profile.lat, buyer_profile.lng),
                circuity=1.35,
            )
            trip_est = estimate_dedicated_trip(dist_km, alloc.quantity_kg, vehicle_types)
            transit_hours = trip_est["transit_hours"]
            transit_days = math.floor(transit_hours / 24.0)

            earliest_delivery = max(today, listing.available_from) + timedelta(days=transit_days)
            if data.delivery_date < earliest_delivery:
                db.rollback()
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="STALE_ALLOCATION",
                    message=f"Requested delivery date {data.delivery_date} is earlier than earliest feasible delivery {earliest_delivery}.",
                )

            transport_cost_per_kg = trip_est["cost_per_kg"]
            ask_price_per_kg = float(listing.ask_price_per_kg)
            platform_fee_per_kg = round(ask_price_per_kg * 0.02, 2)
            landed_price_per_kg = round(
                ask_price_per_kg + transport_cost_per_kg + platform_fee_per_kg, 2
            )

            if landed_price_per_kg > float(req.max_landed_price_per_kg):
                db.rollback()
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="STALE_ALLOCATION",
                    message=f"Landed price ₹{landed_price_per_kg:.2f}/kg exceeds max budget ₹{req.max_landed_price_per_kg:.2f}/kg.",
                )

            # Atomic conditional decrement on Listing
            result = db.execute(
                update(Listing)
                .where(
                    Listing.id == listing.id,
                    Listing.quantity_available_kg >= alloc.quantity_kg,
                    Listing.status == "ACTIVE",
                    Listing.available_until >= today,
                )
                .values(
                    quantity_available_kg=Listing.quantity_available_kg - alloc.quantity_kg,
                    status=case(
                        (Listing.quantity_available_kg - alloc.quantity_kg <= 0.0, "SOLD_OUT"),
                        else_="ACTIVE",
                    ),
                )
            )

            if result.rowcount == 0:
                db.rollback()
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="STALE_ALLOCATION",
                    message=f"Listing {listing.id} quantity changed concurrently.",
                )

            # Create Order
            order = Order(
                listing_id=listing.id,
                buyer_id=buyer_profile.id,
                producer_id=listing.producer_id,
                crop_id=listing.crop_id,
                quantity_kg=alloc.quantity_kg,
                agreed_price_per_kg=ask_price_per_kg,
                transport_cost_estimate_per_kg=transport_cost_per_kg,
                platform_fee_per_kg=platform_fee_per_kg,
                delivery_date=data.delivery_date,
                status="PLACED",
                origin="MATCHING",
                requirement_id=req.id,
                is_demo=listing.is_demo,
            )
            db.add(order)
            db.flush()

            # Record OrderEvent
            event = OrderEvent(
                order_id=order.id,
                from_status=None,
                to_status="PLACED",
                actor_user_id=current_user.id,
                actor_role="BUYER",
                note=f"Order accepted via matching engine from requirement #{req.id}",
            )
            db.add(event)
            created_orders.append(order)

        # Update Requirement fulfillment & status
        req.quantity_fulfilled_kg = float(req.quantity_fulfilled_kg) + total_alloc_qty
        if req.quantity_fulfilled_kg >= float(req.quantity_kg) - 0.001:
            req.status = "FULFILLED"
        else:
            req.status = "PARTIALLY_FULFILLED"

        db.commit()

    except AppException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="DATABASE_ERROR",
            message=f"Failed to accept allocation: {exc}",
        ) from exc

    # Refresh objects to load relationships for response
    for o in created_orders:
        db.refresh(o)
    db.refresh(req)

    return MatchingAcceptResponse(
        orders=[build_order_out(o) for o in created_orders],
        requirement=MatchingAcceptRequirementOut(
            id=req.id,
            status=req.status,
            quantity_fulfilled_kg=float(req.quantity_fulfilled_kg),
        ),
    )


def get_listing_opportunities(
    db: Session,
    listing_id: int,
    current_user: User,
    limit: int = 10,
) -> ProducerOpportunitiesResponse:
    # 1. Authorization: Owner PRODUCER or ADMIN
    if current_user.role != "ADMIN":
        if not current_user.producer_profile:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Only producers or operators can view listing opportunities.",
            )

    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Listing with ID {listing_id} not found.",
        )

    if current_user.role != "ADMIN" and current_user.producer_profile:
        if listing.producer_id != current_user.producer_profile.id:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="You do not own this produce listing.",
            )

    today = today_ist()
    evaluate_listing_expiry(listing, today)
    if listing.status != "ACTIVE":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message=f"Listing is {listing.status} and has no active matching opportunities.",
        )

    producer = listing.producer
    producer_coords = (producer.lat, producer.lng)
    crop = listing.crop
    cfg = load_matching_config()
    vehicle_types = get_vehicle_types(db)

    # 2. Query open / partially fulfilled requirements for this crop
    requirements = (
        db.query(Requirement)
        .filter(
            Requirement.crop_id == listing.crop_id,
            Requirement.status.in_(["OPEN", "PARTIALLY_FULFILLED"]),
            Requirement.needed_by >= today,
        )
        .all()
    )

    opportunities: list[dict[str, Any]] = []

    for req in requirements:
        buyer = req.buyer
        if not buyer:
            continue
        buyer_coords = (buyer.lat, buyer.lng)

        rem_qty = float(req.quantity_kg) - float(req.quantity_fulfilled_kg)
        if rem_qty <= 0:
            continue

        passed, _, _, metrics = evaluate_hard_filters(
            listing=listing,
            requirement=req,
            crop=crop,
            producer_coords=producer_coords,
            buyer_coords=buyer_coords,
            remaining_qty=rem_qty,
            vehicle_types=vehicle_types,
            cfg=cfg,
            today=today,
        )

        if not passed:
            continue

        scores, _ = compute_scores(
            landed_price=metrics["landed_price_per_kg"],
            max_landed_budget=float(req.max_landed_price_per_kg),
            distance_km=metrics["distance_km"],
            age_at_delivery_days=metrics["age_at_delivery"],
            shelf_life_days=crop.shelf_life_days,
            available_qty=float(listing.quantity_available_kg),
            requirement_qty=float(req.quantity_kg),
            cfg=cfg,
        )

        reasons = generate_reasons(
            landed_price=metrics["landed_price_per_kg"],
            max_landed_budget=float(req.max_landed_price_per_kg),
            distance_km=metrics["distance_km"],
            transit_hours=metrics["transit_hours"],
            age_at_delivery_days=metrics["age_at_delivery"],
            shelf_life_days=crop.shelf_life_days,
            available_qty=float(listing.quantity_available_kg),
            requirement_qty=float(req.quantity_kg),
        )

        opportunities.append(
            {
                "requirement": req,
                "buyer": buyer,
                "distance_km": metrics["distance_km"],
                "landed_price_per_kg": metrics["landed_price_per_kg"],
                "scores": scores,
                "reasons": reasons,
            }
        )

    # Sort opportunities: higher score descending, tie break higher max landed budget
    opportunities.sort(
        key=lambda o: (
            -o["scores"]["total"],
            -float(o["requirement"].max_landed_price_per_kg),
            o["distance_km"],
        )
    )

    clamped_limit = min(max(1, limit), 25)
    opportunity_outs: list[OpportunityOut] = []

    for opp in opportunities[:clamped_limit]:
        req_obj = opp["requirement"]
        b_obj = opp["buyer"]
        opportunity_outs.append(
            OpportunityOut(
                requirement=OpportunityRequirementSummary(
                    id=req_obj.id,
                    crop=CropOrderSummary(id=crop.id, name=crop.name),
                    grade_min=req_obj.grade_min,
                    quantity_kg=float(req_obj.quantity_kg),
                    quantity_fulfilled_kg=float(req_obj.quantity_fulfilled_kg),
                    max_landed_price_per_kg=float(req_obj.max_landed_price_per_kg),
                    needed_by=req_obj.needed_by,
                ),
                buyer=OpportunityBuyerSummary(
                    id=b_obj.id,
                    org_name=b_obj.org_name,
                    buyer_type=b_obj.buyer_type,
                    city=b_obj.city,
                    state=b_obj.state,
                ),
                distance_km=round(opp["distance_km"], 1),
                landed_price_per_kg=opp["landed_price_per_kg"],
                scores=MatchingScores(**opp["scores"]),
                reasons=opp["reasons"],
            )
        )

    # Retrieve Hub Forecast context
    hub_context = None
    try:
        from app.db.models import DemandHub
        from app.modules.forecasting.service import get_demand_forecast, haversine_km

        hubs = db.query(DemandHub).all()
        if hubs:
            nearest_hub = min(
                hubs,
                key=lambda h: haversine_km(producer.lat, producer.lng, h.lat, h.lng),
            )
            fc = get_demand_forecast(
                db=db,
                hub_id=nearest_hub.id,
                crop_id=listing.crop_id,
                horizon_days=7,
            )
            total_7d_demand = sum(item["point_forecast_kg"] for item in fc["forecast"])

            # Active supply allocated to this hub
            active_supply = (
                db.query(Listing)
                .join(Listing.producer)
                .filter(
                    Listing.crop_id == listing.crop_id,
                    Listing.status == "ACTIVE",
                    Listing.available_until >= today,
                )
                .all()
            )
            hub_supply = sum(
                float(lst.quantity_available_kg)
                for lst in active_supply
                if min(hubs, key=lambda h: haversine_km(lst.producer.lat, lst.producer.lng, h.lat, h.lng)).id
                == nearest_hub.id
            )

            ratio = hub_supply / total_7d_demand if total_7d_demand > 0 else 1.0
            if ratio < 0.7:
                stat = "SHORTAGE"
            elif ratio > 1.3:
                stat = "SURPLUS"
            else:
                stat = "BALANCED"

            hub_context = HubForecastContext(
                hub={"id": nearest_hub.id, "name": nearest_hub.name},
                forecast_7d_kg=round(total_7d_demand, 1),
                status=stat,
            )
    except Exception:
        hub_context = None

    return ProducerOpportunitiesResponse(
        listing=OpportunityListingSummary(
            id=listing.id,
            crop=CropOrderSummary(id=crop.id, name=crop.name),
            grade=listing.grade,
            quantity_available_kg=float(listing.quantity_available_kg),
            ask_price_per_kg=float(listing.ask_price_per_kg),
        ),
        opportunities=opportunity_outs,
        hub_context=hub_context,
    )
