import uuid
from datetime import datetime
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.core.geo import road_distance_km
from app.db.models import Order, OrderEvent, RoutePlan, Shipment, ShipmentStop, User, Vehicle
from app.modules.logistics.cost import estimate_dedicated_trip
from app.modules.logistics.fleet import get_vehicle_types
from app.modules.routes.optimizer import RouteOptimizer
from app.schemas.routes import (
    OptimizeRequest,
    PlanApproveResponse,
    PlanListResponse,
    PlanResponse,
    PlanShipmentOut,
    PlanSummaryItem,
    PlanTotals,
    PlanVehicleOut,
    ShipmentDetailResponse,
    StopOut,
    UnassignedOrder,
)


def calculate_order_baseline(
    order: Order,
    vehicle_types: list[dict[str, Any]],
    circuity: float = 1.35,
) -> tuple[float, float]:
    """Calculate dedicated baseline round trip for one order per ML.md §10 & §11.

    Baseline = 2 * direct km * vehicle rate + fixed cost.
    """
    pickup_coords = (order.producer.lat, order.producer.lng)
    delivery_coords = (order.buyer.lat, order.buyer.lng)
    direct_km = road_distance_km(pickup_coords, delivery_coords, circuity=circuity)

    trip_est = estimate_dedicated_trip(
        distance_km=direct_km,
        quantity_kg=float(order.quantity_kg),
        vehicle_types=vehicle_types,
        return_leg_factor=2.0,
    )
    round_trip_km = round(direct_km * 2.0, 2)
    return round_trip_km, float(trip_est["cost_total"])


def solve_and_store_route_plan(
    db: Session,
    current_user: User,
    data: OptimizeRequest,
) -> PlanResponse:
    """Optimize routes for eligible confirmed unrouted orders and store PROPOSED plan."""
    query = db.query(Order).filter(
        Order.status == "CONFIRMED",
        Order.shipment_id.is_(None),
    )
    if data.order_ids is not None:
        if len(data.order_ids) > 40:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message="Cannot optimize more than 40 orders in a single run.",
                details=[{"field": "order_ids", "issue": "Exceeds max limit 40"}],
            )
        query = query.filter(Order.id.in_(data.order_ids))

    orders = query.order_by(Order.id.asc()).all()
    if not orders:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="NO_ELIGIBLE_ORDERS",
            message="No confirmed unrouted orders eligible for optimization.",
        )

    # Check available vehicles
    vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.is_available.is_(True))
        .order_by(Vehicle.id.asc())
        .all()
    )
    if not vehicles:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="NO_VEHICLE_AVAILABLE",
            message="No vehicles available in the logistics fleet.",
        )

    vehicle_types = get_vehicle_types(db)

    # Format orders for optimizer and compute baselines
    order_dicts = []
    total_baseline_km = 0.0
    total_baseline_cost = 0.0

    for o in orders:
        b_km, b_cost = calculate_order_baseline(o, vehicle_types)
        total_baseline_km += b_km
        total_baseline_cost += b_cost

        order_dicts.append(
            {
                "order_id": o.id,
                "crop_name": o.crop.name,
                "quantity_kg": float(o.quantity_kg),
                "producer_name": o.producer.org_name,
                "buyer_name": o.buyer.org_name,
                "pickup_lat": o.producer.lat,
                "pickup_lng": o.producer.lng,
                "delivery_lat": o.buyer.lat,
                "delivery_lng": o.buyer.lng,
                "baseline_km": b_km,
                "baseline_cost": b_cost,
            }
        )

    vehicle_dicts = [
        {
            "id": v.id,
            "name": v.name,
            "vehicle_type": v.vehicle_type,
            "capacity_kg": float(v.capacity_kg),
            "cost_per_km": float(v.cost_per_km),
            "fixed_cost_per_trip": float(v.fixed_cost_per_trip),
            "avg_speed_kmph": float(v.avg_speed_kmph),
            "depot_name": v.depot_name,
            "depot_lat": float(v.depot_lat),
            "depot_lng": float(v.depot_lng),
        }
        for v in vehicles
    ]

    optimizer = RouteOptimizer(
        orders=order_dicts,
        vehicles=vehicle_dicts,
        time_limit_s=data.time_limit_s,
    )
    opt_result = optimizer.solve()

    # Calculate plan totals
    opt_km = sum(s["total_distance_km"] for s in opt_result["shipments"])
    opt_cost = sum(s["total_cost"] for s in opt_result["shipments"])
    savings_km = round(total_baseline_km - opt_km, 2)
    savings_cost = round(total_baseline_cost - opt_cost, 2)
    savings_pct = (
        round((savings_cost / total_baseline_cost) * 100, 1)
        if total_baseline_cost > 0
        else 0.0
    )

    used_vehicles = len(opt_result["shipments"])
    avg_util = (
        round(
            sum(s["utilization_pct"] for s in opt_result["shipments"]) / used_vehicles,
            1,
        )
        if used_vehicles > 0
        else 0.0
    )

    totals = PlanTotals(
        optimized_km=round(opt_km, 2),
        optimized_cost=round(opt_cost, 2),
        baseline_km=round(total_baseline_km, 2),
        baseline_cost=round(total_baseline_cost, 2),
        savings_km=savings_km,
        savings_cost=savings_cost,
        savings_pct_cost=savings_pct,
        vehicles_used=used_vehicles,
        avg_utilization_pct=avg_util,
    )

    plan_id = str(uuid.uuid4())
    shipments_out = [
        PlanShipmentOut(
            temp_id=s["temp_id"],
            shipment_id=None,
            vehicle=PlanVehicleOut(**s["vehicle"]),
            total_distance_km=s["total_distance_km"],
            total_cost=s["total_cost"],
            peak_load_kg=s["peak_load_kg"],
            utilization_pct=s["utilization_pct"],
            est_duration_min=s["est_duration_min"],
            stops=[StopOut(**st) for st in s["stops"]],
            geometry=s["geometry"],
        )
        for s in opt_result["shipments"]
    ]

    unassigned_out = [
        UnassignedOrder(
            order_id=u["order_id"],
            quantity_kg=u["quantity_kg"],
            reason=u["reason"],
        )
        for u in opt_result["unassigned"]
    ]

    # Storable result dictionary
    result_dict = {
        "plan_id": plan_id,
        "status": "PROPOSED",
        "method": opt_result["method"],
        "solver_status": opt_result.get("solver_status"),
        "solve_time_ms": opt_result.get("solve_time_ms", 0),
        "distance_source": "ESTIMATED_HAVERSINE",
        "totals": totals.model_dump(),
        "baseline_note": "Baseline = each order shipped on its own dedicated round trip (modelled, not measured).",
        "shipments": [s.model_dump() for s in shipments_out],
        "unassigned": [u.model_dump() for u in unassigned_out],
        "skipped_order_ids": [],
        "warnings": [],
    }

    db_plan = RoutePlan(
        id=plan_id,
        status="PROPOSED",
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        method=opt_result["method"],
        solver_status=opt_result.get("solver_status"),
        solve_time_ms=opt_result.get("solve_time_ms", 0),
        distance_source="ESTIMATED_HAVERSINE",
        order_ids=[o.id for o in orders],
        num_orders=len(orders),
        num_unassigned=len(unassigned_out),
        baseline_km=totals.baseline_km,
        optimized_km=totals.optimized_km,
        baseline_cost=totals.baseline_cost,
        optimized_cost=totals.optimized_cost,
        result_json=result_dict,
    )
    db.add(db_plan)
    db.commit()

    return PlanResponse(**result_dict)


def list_route_plans(
    db: Session,
    limit: int = 50,
    offset: int = 0,
) -> PlanListResponse:
    query = db.query(RoutePlan).order_by(RoutePlan.created_at.desc())
    total = query.count()
    plans = query.offset(offset).limit(limit).all()

    items = [
        PlanSummaryItem(
            plan_id=p.id,
            status=p.status,
            created_at=p.created_at.isoformat() if p.created_at else "",
            method=p.method,
            num_orders=p.num_orders,
            num_unassigned=p.num_unassigned,
            optimized_km=float(p.optimized_km),
            optimized_cost=float(p.optimized_cost),
            baseline_cost=float(p.baseline_cost),
        )
        for p in plans
    ]
    return PlanListResponse(items=items, total=total)


def get_route_plan_detail(
    db: Session,
    plan_id: str,
    current_user: User,
) -> PlanResponse:
    plan = db.query(RoutePlan).filter(RoutePlan.id == plan_id).first()
    if not plan:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Route plan {plan_id} not found.",
        )

    res_json = dict(plan.result_json)
    # Authorization filter: PRODUCER/BUYER only see approved plans containing their orders, filtered to their stops
    if current_user.role in ["producer", "farmer", "fpo"]:
        if plan.status != "APPROVED":
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Producers can only view approved route plans.",
            )
        # Verify ownership
        producer_id = current_user.producer_profile.id if current_user.producer_profile else -1
        user_orders = (
            db.query(Order.id)
            .filter(Order.producer_id == producer_id, Order.id.in_(plan.order_ids))
            .all()
        )
        user_order_ids = {o[0] for o in user_orders}
        if not user_order_ids:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="No orders belonging to you in this route plan.",
            )

    elif current_user.role in ["buyer", "buyer_retail", "buyer_trader"]:
        if plan.status != "APPROVED":
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Buyers can only view approved route plans.",
            )
        buyer_id = current_user.buyer_profile.id if current_user.buyer_profile else -1
        user_orders = (
            db.query(Order.id)
            .filter(Order.buyer_id == buyer_id, Order.id.in_(plan.order_ids))
            .all()
        )
        user_order_ids = {o[0] for o in user_orders}
        if not user_order_ids:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="No orders belonging to you in this route plan.",
            )

    return PlanResponse(**res_json)


def approve_route_plan(
    db: Session,
    plan_id: str,
    current_user: User,
) -> PlanApproveResponse:
    """Approve a PROPOSED plan, create shipments/stops, and allocate costs to orders."""
    plan = db.query(RoutePlan).filter(RoutePlan.id == plan_id).first()
    if not plan:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Route plan {plan_id} not found.",
        )

    if plan.status != "PROPOSED":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="INVALID_TRANSITION",
            message=f"Plan is in {plan.status} status and cannot be approved.",
        )

    # Concurrency check: Ensure every planned order is still CONFIRMED and unrouted (AC-RTE-10)
    all_plan_order_ids = set(plan.order_ids or [])
    result_json = dict(plan.result_json)
    for shp in result_json.get("shipments", []):
        for st in shp.get("stops", []):
            if st.get("order_id"):
                all_plan_order_ids.add(st["order_id"])

    orders_in_db = (
        db.query(Order)
        .filter(Order.id.in_(all_plan_order_ids))
        .all()
    )
    if len(orders_in_db) != len(all_plan_order_ids):
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="STALE_PLAN",
            message="One or more orders in this plan no longer exist.",
        )

    for o in orders_in_db:
        if o.status != "CONFIRMED" or o.shipment_id is not None:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="STALE_PLAN",
                message=f"Order #{o.id} is no longer in CONFIRMED unrouted state.",
            )

    order_map = {o.id: o for o in orders_in_db}
    created_shipments: list[ShipmentDetailResponse] = []

    try:
        for shp_data in result_json.get("shipments", []):
            vehicle_id = shp_data["vehicle"]["id"]
            shipment = Shipment(
                plan_id=plan.id,
                vehicle_id=vehicle_id,
                status="PLANNED",
                total_distance_km=shp_data["total_distance_km"],
                total_cost=shp_data["total_cost"],
                total_load_kg=shp_data["peak_load_kg"],
                peak_load_kg=shp_data["peak_load_kg"],
                utilization_pct=shp_data["utilization_pct"],
                est_duration_min=shp_data["est_duration_min"],
                created_at=datetime.utcnow(),
            )
            db.add(shipment)
            db.flush()

            shp_data["shipment_id"] = shipment.id

            # Create stops
            shp_order_ids = set()
            for st_data in shp_data.get("stops", []):
                oid = st_data.get("order_id")
                if oid:
                    shp_order_ids.add(oid)
                stop = ShipmentStop(
                    shipment_id=shipment.id,
                    sequence=st_data["sequence"],
                    stop_type=st_data["stop_type"],
                    order_id=oid,
                    label=st_data["label"],
                    lat=st_data["lat"],
                    lng=st_data["lng"],
                    load_after_kg=st_data["load_after_kg"],
                    cum_distance_km=st_data["cum_distance_km"],
                    eta_min_from_start=st_data["eta_min_from_start"],
                )
                db.add(stop)

            # Link orders and allocate transport cost by kg-km share (ML.md §10)
            # kg_km share = (qty * direct_km) / sum(qty * direct_km)
            shp_orders = [order_map[oid] for oid in shp_order_ids if oid in order_map]
            order_kg_kms = {}
            for o in shp_orders:
                direct_km = road_distance_km(
                    (o.producer.lat, o.producer.lng),
                    (o.buyer.lat, o.buyer.lng),
                    circuity=1.35,
                )
                order_kg_kms[o.id] = float(o.quantity_kg) * direct_km

            total_kg_km = sum(order_kg_kms.values())
            total_shipment_cost = float(shp_data["total_cost"])

            running_allocated = 0.0
            for idx, o in enumerate(shp_orders):
                o.shipment_id = shipment.id
                if total_kg_km > 0:
                    if idx == len(shp_orders) - 1:
                        # Remainder to guarantee sum == total_cost ±0.01 (AC-RTE-09)
                        allocated = round(total_shipment_cost - running_allocated, 2)
                    else:
                        share = order_kg_kms[o.id] / total_kg_km
                        allocated = round(total_shipment_cost * share, 2)
                        running_allocated += allocated
                else:
                    allocated = round(total_shipment_cost / len(shp_orders), 2)

                o.allocated_transport_cost_total = allocated

                # Log order event
                evt = OrderEvent(
                    order_id=o.id,
                    from_status=o.status,
                    to_status=o.status,
                    actor_user_id=current_user.id,
                    actor_role=current_user.role.upper(),
                    note=f"Assigned to shipment #{shipment.id} under route plan {plan.id}",
                )
                db.add(evt)

            created_shipments.append(
                ShipmentDetailResponse(
                    id=shipment.id,
                    plan_id=plan.id,
                    vehicle_id=vehicle_id,
                    vehicle_name=shp_data["vehicle"]["name"],
                    vehicle_type=shp_data["vehicle"]["vehicle_type"],
                    status="PLANNED",
                    total_distance_km=shp_data["total_distance_km"],
                    total_cost=shp_data["total_cost"],
                    peak_load_kg=shp_data["peak_load_kg"],
                    utilization_pct=shp_data["utilization_pct"],
                    est_duration_min=shp_data["est_duration_min"],
                    stops=[StopOut(**st) for st in shp_data["stops"]],
                    order_ids=list(shp_order_ids),
                )
            )

        # Update plan status to APPROVED
        plan.status = "APPROVED"
        plan.approved_at = datetime.utcnow()
        result_json["status"] = "APPROVED"
        plan.result_json = result_json

        db.commit()
    except Exception:
        db.rollback()
        raise

    return PlanApproveResponse(
        plan=PlanResponse(**result_json),
        shipments=created_shipments,
    )


def discard_route_plan(
    db: Session,
    plan_id: str,
    current_user: User,
) -> PlanResponse:
    plan = db.query(RoutePlan).filter(RoutePlan.id == plan_id).first()
    if not plan:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Route plan {plan_id} not found.",
        )

    if plan.status != "PROPOSED":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="INVALID_TRANSITION",
            message=f"Plan is in {plan.status} status and cannot be discarded.",
        )

    plan.status = "DISCARDED"
    res_json = dict(plan.result_json)
    res_json["status"] = "DISCARDED"
    plan.result_json = res_json

    db.commit()
    return PlanResponse(**res_json)


def get_shipment_detail(
    db: Session,
    shipment_id: int,
    current_user: User,
) -> ShipmentDetailResponse:
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Shipment {shipment_id} not found.",
        )

    orders = db.query(Order).filter(Order.shipment_id == shipment.id).all()
    order_ids = [o.id for o in orders]

    # Role checks
    is_admin = current_user.role.upper() in ["ADMIN", "OPERATOR"]
    if not is_admin:
        is_party = False
        if current_user.producer_profile:
            is_party = any(o.producer_id == current_user.producer_profile.id for o in orders)
        if current_user.buyer_profile:
            is_party = is_party or any(o.buyer_id == current_user.buyer_profile.id for o in orders)
        if not is_party:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="You do not have access to this shipment.",
            )

    stops_out = [
        StopOut(
            sequence=st.sequence,
            stop_type=st.stop_type,
            order_id=st.order_id,
            label=st.label,
            lat=st.lat,
            lng=st.lng,
            load_after_kg=float(st.load_after_kg),
            cum_distance_km=float(st.cum_distance_km),
            eta_min_from_start=st.eta_min_from_start,
        )
        for st in shipment.stops
    ]

    return ShipmentDetailResponse(
        id=shipment.id,
        plan_id=shipment.plan_id,
        vehicle_id=shipment.vehicle_id,
        vehicle_name=shipment.stops[0].label if shipment.stops else "Fleet Vehicle",
        vehicle_type="TRUCK",
        status=shipment.status,
        total_distance_km=float(shipment.total_distance_km),
        total_cost=float(shipment.total_cost),
        peak_load_kg=float(shipment.peak_load_kg),
        utilization_pct=float(shipment.utilization_pct),
        est_duration_min=shipment.est_duration_min,
        stops=stops_out,
        order_ids=order_ids,
    )


def transition_shipment_status(
    db: Session,
    shipment_id: int,
    to_status: str,
    current_user: User,
) -> ShipmentDetailResponse:
    """Manual status transition for shipment per API.md §11: PLANNED -> DISPATCHED -> DELIVERED."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Shipment {shipment_id} not found.",
        )

    valid_transitions = {
        "PLANNED": ["DISPATCHED"],
        "DISPATCHED": ["DELIVERED"],
    }
    allowed = valid_transitions.get(shipment.status, [])
    if to_status not in allowed:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="INVALID_TRANSITION",
            message=f"Cannot transition shipment from {shipment.status} to {to_status}.",
        )

    orders = db.query(Order).filter(Order.shipment_id == shipment.id).all()

    shipment.status = to_status
    if to_status == "DISPATCHED":
        shipment.dispatched_at = datetime.utcnow()
        for o in orders:
            old_s = o.status
            o.status = "IN_TRANSIT"
            evt = OrderEvent(
                order_id=o.id,
                from_status=old_s,
                to_status="IN_TRANSIT",
                actor_user_id=current_user.id,
                actor_role=current_user.role.upper(),
                note=f"Shipment #{shipment.id} dispatched",
            )
            db.add(evt)
    elif to_status == "DELIVERED":
        shipment.delivered_at = datetime.utcnow()
        for o in orders:
            old_s = o.status
            o.status = "DELIVERED"
            evt = OrderEvent(
                order_id=o.id,
                from_status=old_s,
                to_status="DELIVERED",
                actor_user_id=current_user.id,
                actor_role=current_user.role.upper(),
                note=f"Shipment #{shipment.id} delivered",
            )
            db.add(evt)

    db.commit()
    db.refresh(shipment)
    return get_shipment_detail(db, shipment.id, current_user)
