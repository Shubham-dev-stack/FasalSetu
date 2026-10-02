import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.dates import today_ist
from app.db.models import (
    Crop,
    DemandHub,
    Listing,
    Order,
    ProducerProfile,
    Requirement,
    RoutePlan,
    Shipment,
)
from app.modules.forecasting.service import (
    get_demand_forecast,
    get_forecast_model_info,
    haversine_km,
)
from app.modules.pricing.service import (
    compute_traditional_scenario,
    get_latest_market_price,
    load_pricing_config,
)
from app.schemas.analytics import (
    AnalyticsKPIs,
    AnalyticsModelContext,
    AnalyticsOverviewResponse,
    AnalyticsPriceGap,
    AnalyticsSupplyDemandResponse,
    DailyOrdersPoint,
    SupplyDemandRow,
)

logger = logging.getLogger("fasalsetu.analytics.service")

COMMITTED_ORDER_STATUSES = {"CONFIRMED", "IN_TRANSIT", "DELIVERED"}


def get_analytics_overview(db: Session) -> AnalyticsOverviewResponse:
    """Compute platform-level KPI overview, 14-day trends, and modelled price gap.

    Authoritative sources:
    - Orders: committed in {CONFIRMED, IN_TRANSIT, DELIVERED}
    - Requirements: non-cancelled (status != 'CANCELLED')
    - Route plans: status == 'APPROVED'
    - Shipments: from approved route plans
    - Price gap: evaluated against APMC benchmark and ML.md §12 traditional scenario
    """
    today = today_ist()
    pricing_cfg = load_pricing_config()
    model_info = get_forecast_model_info()

    # 1. Committed Orders KPIs
    committed_orders = (
        db.query(Order)
        .filter(Order.status.in_(COMMITTED_ORDER_STATUSES))
        .all()
    )
    committed_count = len(committed_orders)
    committed_volume_kg = round(
        sum(float(o.quantity_kg) for o in committed_orders), 1
    )
    committed_value_inr = round(
        sum(float(o.quantity_kg) * float(o.agreed_price_per_kg) for o in committed_orders),
        2,
    )

    # 2. Requirement Fill Rate
    reqs = (
        db.query(Requirement)
        .filter(Requirement.status != "CANCELLED")
        .all()
    )
    req_fulfilled = sum(float(r.quantity_fulfilled_kg) for r in reqs)
    req_requested = sum(float(r.quantity_kg) for r in reqs)
    fill_rate_pct = (
        round((req_fulfilled / req_requested) * 100.0, 2)
        if req_requested > 0
        else None
    )

    # 3. Logistics Cost per kg
    logistics_rates = []
    for o in committed_orders:
        qty = float(o.quantity_kg)
        if qty > 0:
            if o.allocated_transport_cost_total is not None:
                rate = float(o.allocated_transport_cost_total) / qty
            else:
                rate = float(o.transport_cost_estimate_per_kg)
            logistics_rates.append(rate)

    avg_logistics_cost = (
        round(sum(logistics_rates) / len(logistics_rates), 2)
        if logistics_rates
        else None
    )

    # 4. Route Metrics (APPROVED plans only per API.md §13 / Rules D-025)
    approved_plans = (
        db.query(RoutePlan)
        .filter(RoutePlan.status == "APPROVED")
        .all()
    )
    route_savings_km = round(
        sum(float(p.baseline_km - p.optimized_km) for p in approved_plans), 1
    ) if approved_plans else 0.0

    route_savings_inr = round(
        sum(float(p.baseline_cost - p.optimized_cost) for p in approved_plans), 2
    ) if approved_plans else 0.0

    approved_plan_ids = [p.id for p in approved_plans]
    approved_shipments = (
        db.query(Shipment)
        .filter(Shipment.plan_id.in_(approved_plan_ids))
        .all()
        if approved_plan_ids
        else []
    )
    avg_utilization_pct = (
        round(
            sum(float(s.utilization_pct) for s in approved_shipments)
            / len(approved_shipments),
            2,
        )
        if approved_shipments
        else None
    )

    kpis = AnalyticsKPIs(
        committed_orders=committed_count,
        committed_volume_kg=committed_volume_kg,
        committed_value_inr=committed_value_inr,
        requirement_fill_rate_pct=fill_rate_pct,
        avg_logistics_cost_per_kg=avg_logistics_cost,
        route_savings_km=route_savings_km,
        route_savings_inr=route_savings_inr,
        avg_utilization_pct=avg_utilization_pct,
    )

    # 5. Modelled Price Gap vs Traditional Chain
    farmer_deltas = []
    buyer_deltas = []
    orders_considered = 0

    all_hubs = db.query(DemandHub).all()

    for o in committed_orders:
        qty = float(o.quantity_kg)
        farmgate_per_kg = float(o.agreed_price_per_kg)

        if o.allocated_transport_cost_total is not None and qty > 0:
            transport_per_kg = round(float(o.allocated_transport_cost_total) / qty, 2)
        else:
            transport_per_kg = round(float(o.transport_cost_estimate_per_kg), 2)

        fee_pct = float(pricing_cfg.get("platform_fee_pct", 2.0))
        fee_per_kg = round(farmgate_per_kg * (fee_pct / 100.0), 2)
        landed_per_kg = round(farmgate_per_kg + transport_per_kg + fee_per_kg, 2)

        # Reference hub lookup
        hub = None
        if o.buyer and o.buyer.hub:
            hub = o.buyer.hub
        elif o.buyer and o.buyer.hub_id:
            hub = db.query(DemandHub).filter(DemandHub.id == o.buyer.hub_id).first()

        if not hub and o.producer and all_hubs:
            p_lat, p_lng = o.producer.lat, o.producer.lng
            hub = min(all_hubs, key=lambda h: haversine_km(p_lat, p_lng, h.lat, h.lng))

        if not hub:
            continue

        benchmark = get_latest_market_price(db, hub_id=hub.id, crop_id=o.crop_id)
        if not benchmark:
            continue

        producer_lat = o.producer.lat if o.producer else hub.lat
        producer_lng = o.producer.lng if o.producer else hub.lng
        producer_hub_dist_km = haversine_km(producer_lat, producer_lng, hub.lat, hub.lng)
        producer_to_hub_transport = round(producer_hub_dist_km * 0.05, 2)

        scenario = compute_traditional_scenario(
            benchmark_modal=float(benchmark.modal_price_per_kg),
            farmgate_per_kg=farmgate_per_kg,
            landed_per_kg=landed_per_kg,
            producer_to_hub_transport_per_kg=producer_to_hub_transport,
            cfg=pricing_cfg,
        )

        farmer_deltas.append(scenario.delta_farmer_pct)
        buyer_deltas.append(scenario.delta_buyer_pct)
        orders_considered += 1

    price_gap = AnalyticsPriceGap(
        avg_farmer_delta_pct=(
            round(sum(farmer_deltas) / orders_considered, 2)
            if orders_considered > 0
            else None
        ),
        avg_buyer_delta_pct=(
            round(sum(buyer_deltas) / orders_considered, 2)
            if orders_considered > 0
            else None
        ),
        orders_considered=orders_considered,
        basis="MODELLED_SCENARIO",
    )

    # 6. Daily Orders & Volume Series (14 days: today - 13 days .. today)
    daily_map = {
        (today - timedelta(days=i)): {"orders": 0, "volume_kg": 0.0}
        for i in range(13, -1, -1)
    }

    for o in committed_orders:
        target_d = o.delivery_date
        if not target_d and o.created_at:
            target_d = o.created_at.date()
        if target_d in daily_map:
            daily_map[target_d]["orders"] += 1
            daily_map[target_d]["volume_kg"] += float(o.quantity_kg)

    daily_points = [
        DailyOrdersPoint(
            date=d.isoformat(),
            orders=daily_map[d]["orders"],
            volume_kg=round(daily_map[d]["volume_kg"], 1),
        )
        for d in sorted(daily_map.keys())
    ]

    # 7. Model Context Linkage
    deployed_method = model_info.get("deployed_method", "LIGHTGBM")
    model_version = model_info.get("model_version")

    model_context = AnalyticsModelContext(
        deployed_method=deployed_method,
        data_source="SYNTHETIC",
        model_version=model_version,
    )

    return AnalyticsOverviewResponse(
        as_of=datetime.utcnow().isoformat(),
        data_note="All figures computed from synthetic demo records",
        kpis=kpis,
        price_gap=price_gap,
        daily=daily_points,
        model=model_context,
    )


def get_analytics_supply_demand(
    db: Session,
    crop_id: int | None = None,
) -> AnalyticsSupplyDemandResponse:
    """Compute Hub x Crop supply-vs-demand matrix per ML.md §13 & FR-101.

    Rules:
    - Rule D-026: Attribute each ACTIVE listing to its nearest hub to avoid double counting.
    - forecast_7d(h,c): 7-day predicted demand sum from forecasting service.
    - ratio: supply / forecast_7d.
    - status: SHORTAGE (<0.7), SURPLUS (>1.3), else BALANCED.
    """
    today = today_ist()
    model_info = get_forecast_model_info()
    method = model_info.get("deployed_method", "LIGHTGBM")

    hubs = db.query(DemandHub).order_by(DemandHub.id.asc()).all()
    if crop_id is not None:
        target_crop = db.query(Crop).filter(Crop.id == crop_id).first()
        if not target_crop:
            from fastapi import status as http_status

            from app.core.errors import AppException
            raise AppException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                code="CROP_NOT_FOUND",
                message=f"Crop with ID {crop_id} not found.",
            )
        crops = [target_crop]
    else:
        crops = db.query(Crop).order_by(Crop.id.asc()).all()

    # Pre-fetch all active listings with producers
    active_listings = (
        db.query(Listing)
        .join(ProducerProfile, Listing.producer_id == ProducerProfile.id)
        .filter(
            Listing.status == "ACTIVE",
            Listing.available_until >= today,
            Listing.quantity_available_kg > 0,
        )
        .all()
    )

    # Attribution map: (hub_id, crop_id) -> total available kg
    supply_map: dict[tuple[int, int], float] = {
        (h.id, c.id): 0.0 for h in hubs for c in crops
    }

    if hubs:
        for listing in active_listings:
            if crop_id is not None and listing.crop_id != crop_id:
                continue
            producer = listing.producer
            if not producer:
                continue
            p_lat, p_lng = producer.lat, producer.lng
            nearest_hub = min(
                hubs,
                key=lambda h: haversine_km(p_lat, p_lng, h.lat, h.lng),
            )
            key = (nearest_hub.id, listing.crop_id)
            if key in supply_map:
                supply_map[key] += float(listing.quantity_available_kg)

    rows: list[SupplyDemandRow] = []

    for hub in hubs:
        for crop in crops:
            supp_kg = supply_map.get((hub.id, crop.id), 0.0)

            # Get 7-day forecast
            fc = get_demand_forecast(
                db=db,
                hub_id=hub.id,
                crop_id=crop.id,
                horizon_days=7,
            )
            demand_7d = sum(item["point_forecast_kg"] for item in fc.get("forecast", []))

            if demand_7d > 0:
                ratio = round(supp_kg / demand_7d, 2)
            else:
                ratio = 0.0

            if ratio < 0.7:
                status = "SHORTAGE"
            elif ratio > 1.3:
                status = "SURPLUS"
            else:
                status = "BALANCED"

            rows.append(
                SupplyDemandRow(
                    hub=hub.name,
                    hub_id=hub.id,
                    crop=crop.name,
                    crop_id=crop.id,
                    forecast_7d_kg=round(demand_7d, 1),
                    supply_kg=round(supp_kg, 1),
                    ratio=ratio,
                    status=status,
                )
            )

    return AnalyticsSupplyDemandResponse(
        rows=rows,
        method=method,
        data_source="SYNTHETIC",
        as_of=datetime.utcnow().isoformat(),
    )
