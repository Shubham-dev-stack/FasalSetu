from datetime import timedelta
from pathlib import Path
from typing import Any

import yaml
from fastapi import status
from sqlalchemy.orm import Session

from app.core.dates import today_ist
from app.core.errors import AppException
from app.core.geo import haversine_km, road_distance_km
from app.db.models import Crop, DemandHub, MarketPrice, Order, User
from app.modules.logistics.cost import estimate_dedicated_trip
from app.modules.logistics.fleet import get_vehicle_types
from app.schemas.pricing import (
    BenchmarkInfo,
    FairBand,
    OrderPriceBreakdownResponse,
    PricingBenchmarkResponse,
    PricingCropInfo,
    PricingHubInfo,
    ScenarioAssumptions,
    TraditionalScenario,
    TrendPoint,
    WaterfallPerKg,
    WaterfallTotals,
)

DEFAULT_PRICING_CONFIG: dict[str, Any] = {
    "platform_fee_pct": 2.0,
    "commission_agent_pct": 5.0,
    "trader_margin_pct": 8.0,
    "retail_margin_pct": 12.0,
    "last_mile_cost_per_kg": 1.0,
    "price_warning_multiple": 3.0,
}


def load_pricing_config() -> dict[str, Any]:
    config_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "config"
        / "pricing.yaml"
    )
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded and isinstance(loaded, dict):
                    cfg = dict(DEFAULT_PRICING_CONFIG)
                    cfg.update(loaded)
                    return cfg
        except Exception:
            pass
    return dict(DEFAULT_PRICING_CONFIG)


def get_latest_market_price(
    db: Session,
    hub_id: int,
    crop_id: int,
) -> MarketPrice | None:
    """Query latest market price for hub and crop, prioritizing AGMARKNET_SNAPSHOT (real snapshot)

    over SYNTHETIC_DEMO per Data.md / ML.md.
    """
    today = today_ist()

    # 1. Real Agmarknet snapshot check (within last 30 days)
    real_price = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.hub_id == hub_id,
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
        return real_price

    # 2. Synthetic demo benchmark
    synthetic_price = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.hub_id == hub_id,
            MarketPrice.crop_id == crop_id,
            MarketPrice.is_synthetic.is_(True),
            MarketPrice.source == "SYNTHETIC_DEMO",
            MarketPrice.price_date <= today,
        )
        .order_by(MarketPrice.price_date.desc())
        .first()
    )
    return synthetic_price


def compute_traditional_scenario(
    benchmark_modal: float,
    farmgate_per_kg: float,
    landed_per_kg: float,
    producer_to_hub_transport_per_kg: float,
    cfg: dict[str, Any],
) -> TraditionalScenario:
    """Compute traditional chain scenario per ML.md §12:

    farmer_mandi_net = benchmark_modal * (1 - commission_agent_pct/100) - producer_to_hub_transport_per_kg
    buyer_traditional = benchmark_modal * (1 + trader_margin_pct/100) * (1 + retail_margin_pct/100) + last_mile_cost_per_kg
    delta_farmer_pct = (farmgate - farmer_mandi_net) / farmer_mandi_net
    delta_buyer_pct = (landed - buyer_traditional) / buyer_traditional
    """
    comm_pct = float(cfg.get("commission_agent_pct", 5.0))
    trader_pct = float(cfg.get("trader_margin_pct", 8.0))
    retail_pct = float(cfg.get("retail_margin_pct", 12.0))
    last_mile = float(cfg.get("last_mile_cost_per_kg", 1.0))
    platform_fee_pct = float(cfg.get("platform_fee_pct", 2.0))

    farmer_mandi_net = (benchmark_modal * (1.0 - comm_pct / 100.0)) - producer_to_hub_transport_per_kg
    buyer_traditional = (benchmark_modal * (1.0 + trader_pct / 100.0) * (1.0 + retail_pct / 100.0)) + last_mile

    delta_farmer_pct = (
        ((farmgate_per_kg - farmer_mandi_net) / farmer_mandi_net) * 100.0
        if farmer_mandi_net > 0
        else 0.0
    )
    delta_buyer_pct = (
        ((landed_per_kg - buyer_traditional) / buyer_traditional) * 100.0
        if buyer_traditional > 0
        else 0.0
    )

    assumptions = ScenarioAssumptions(
        platform_fee_pct=platform_fee_pct,
        commission_agent_pct=comm_pct,
        trader_margin_pct=trader_pct,
        retail_margin_pct=retail_pct,
        last_mile_cost_per_kg=last_mile,
    )

    return TraditionalScenario(
        farmer_mandi_net_per_kg=round(farmer_mandi_net, 2),
        buyer_traditional_per_kg=round(buyer_traditional, 2),
        delta_farmer_pct=round(delta_farmer_pct, 2),
        delta_buyer_pct=round(delta_buyer_pct, 2),
        assumptions=assumptions,
    )


def compute_fair_band(
    farmer_mandi_net: float,
    buyer_traditional: float,
    transport_per_kg: float,
    platform_fee_pct: float,
) -> FairBand | None:
    """Compute fair price band per ML.md §12:

    L = farmer_mandi_net
    U = (buyer_traditional - transport_per_kg) / (1 + platform_fee_pct / 100)
    fair_band = [L, U] (null if U <= L)
    """
    low = farmer_mandi_net
    high = (buyer_traditional - transport_per_kg) / (1.0 + platform_fee_pct / 100.0)

    if high <= low:
        return None

    return FairBand(low=round(low, 2), high=round(high, 2))


def get_order_price_breakdown(
    db: Session,
    order_id: int,
    current_user: User,
) -> OrderPriceBreakdownResponse:
    """Retrieve full per-order price waterfall breakdown per API.md §12 / PRD FR-90."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Order {order_id} not found.",
        )

    # Authorization: party (buyer / producer) or ADMIN / OPERATOR
    is_admin = current_user.role.upper() in ["ADMIN", "OPERATOR"]
    if not is_admin:
        is_owner = False
        if current_user.producer_profile and order.producer_id == current_user.producer_profile.id:
            is_owner = True
        elif current_user.buyer_profile and order.buyer_id == current_user.buyer_profile.id:
            is_owner = True

        if not is_owner:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="You do not have permission to view price breakdown for this order.",
            )

    cfg = load_pricing_config()
    qty = float(order.quantity_kg)
    farmgate_per_kg = float(order.agreed_price_per_kg)

    # Transport basis and per-kg rate
    if order.allocated_transport_cost_total is not None and qty > 0:
        transport_per_kg = round(float(order.allocated_transport_cost_total) / qty, 2)
        transport_basis = "ALLOCATED_ROUTE"
    else:
        transport_per_kg = round(float(order.transport_cost_estimate_per_kg), 2)
        transport_basis = "ESTIMATE"

    # Platform fee per kg: farmgate * platform_fee_pct / 100 (AC-PRC-01)
    fee_pct = float(cfg.get("platform_fee_pct", 2.0))
    platform_fee_per_kg = round(farmgate_per_kg * (fee_pct / 100.0), 2)

    # Landed price per kg: farmgate + transport + platform_fee (AC-PRC-01)
    landed_per_kg = round(farmgate_per_kg + transport_per_kg + platform_fee_per_kg, 2)

    per_kg = WaterfallPerKg(
        farmgate=farmgate_per_kg,
        transport=transport_per_kg,
        platform_fee=platform_fee_per_kg,
        landed=landed_per_kg,
    )

    totals = WaterfallTotals(
        farmgate_total=round(farmgate_per_kg * qty, 2),
        transport_total=round(transport_per_kg * qty, 2),
        platform_fee_total=round(platform_fee_per_kg * qty, 2),
        landed_total=round(landed_per_kg * qty, 2),
    )

    crop = order.crop
    crop_info = PricingCropInfo(id=crop.id, name=crop.name)

    # Reference benchmark lookup (buyer hub or nearest hub of producer)
    hub: DemandHub | None = None
    if order.buyer and order.buyer.hub:
        hub = order.buyer.hub
    elif order.buyer and order.buyer.hub_id:
        hub = db.query(DemandHub).filter(DemandHub.id == order.buyer.hub_id).first()

    if not hub and order.producer:
        # Nearest hub to producer
        hubs = db.query(DemandHub).all()
        if hubs:
            hub = min(hubs, key=lambda h: haversine_km(order.producer.lat, order.producer.lng, h.lat, h.lng))

    benchmark_info: BenchmarkInfo | None = None
    scenario: TraditionalScenario | None = None
    fair_band: FairBand | None = None

    if hub:
        mkt_price = get_latest_market_price(db, hub.id, crop.id)
        if mkt_price:
            hub_info = PricingHubInfo(id=hub.id, name=hub.name, city=hub.city, state=hub.state)
            benchmark_info = BenchmarkInfo(
                hub=hub_info,
                market_name=mkt_price.market_name,
                price_date=str(mkt_price.price_date),
                modal_price_per_kg=float(mkt_price.modal_price_per_kg),
                min_price_per_kg=float(mkt_price.min_price_per_kg),
                max_price_per_kg=float(mkt_price.max_price_per_kg),
                source=mkt_price.source,
                is_synthetic=mkt_price.is_synthetic,
            )

            # Producer to hub transport per kg
            vehicle_types = get_vehicle_types(db)
            prod_coords = (order.producer.lat, order.producer.lng)
            hub_coords = (hub.lat, hub.lng)
            dist_to_hub = road_distance_km(prod_coords, hub_coords)
            trip_est = estimate_dedicated_trip(dist_to_hub, qty, vehicle_types)
            producer_to_hub_transport_per_kg = trip_est["cost_per_kg"]

            # Traditional scenario
            scenario = compute_traditional_scenario(
                benchmark_modal=float(mkt_price.modal_price_per_kg),
                farmgate_per_kg=farmgate_per_kg,
                landed_per_kg=landed_per_kg,
                producer_to_hub_transport_per_kg=producer_to_hub_transport_per_kg,
                cfg=cfg,
            )

            fair_band = compute_fair_band(
                farmer_mandi_net=scenario.farmer_mandi_net_per_kg,
                buyer_traditional=scenario.buyer_traditional_per_kg,
                transport_per_kg=transport_per_kg,
                platform_fee_pct=fee_pct,
            )

    return OrderPriceBreakdownResponse(
        order_id=order.id,
        crop=crop_info,
        quantity_kg=qty,
        per_kg=per_kg,
        totals=totals,
        transport_basis=transport_basis,
        benchmark=benchmark_info,
        scenario=scenario,
        fair_band=fair_band,
    )


def get_pricing_benchmark(
    db: Session,
    crop_id: int,
    hub_id: int | None = None,
    lat: float | None = None,
    lng: float | None = None,
    quantity_kg: float = 1000.0,
) -> PricingBenchmarkResponse:
    """Retrieve benchmark price, 30-day trend, and fair-price band per API.md §12 / PRD FR-91."""
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Crop with id {crop_id} not found.",
        )

    # Resolve demand hub
    hub: DemandHub | None = None
    if hub_id is not None:
        hub = db.query(DemandHub).filter(DemandHub.id == hub_id).first()
        if not hub:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="NOT_FOUND",
                message=f"Demand hub with id {hub_id} not found.",
            )
    elif lat is not None and lng is not None:
        hubs = db.query(DemandHub).all()
        if not hubs:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="NOT_FOUND",
                message="No demand hubs configured in database.",
            )
        hub = min(hubs, key=lambda h: haversine_km(lat, lng, h.lat, h.lng))
    else:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Must provide either hub_id or (lat, lng) to resolve benchmark hub.",
        )

    cfg = load_pricing_config()
    hub_info = PricingHubInfo(id=hub.id, name=hub.name, city=hub.city, state=hub.state)

    mkt_price = get_latest_market_price(db, hub.id, crop.id)
    benchmark_info: BenchmarkInfo | None = None
    fair_band: FairBand | None = None

    # Trend (30 days)
    today = today_ist()
    start_date = today - timedelta(days=30)
    prices_history = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.hub_id == hub.id,
            MarketPrice.crop_id == crop.id,
            MarketPrice.price_date <= today,
            MarketPrice.price_date >= start_date,
        )
        .order_by(MarketPrice.price_date.asc())
        .all()
    )

    # Deduplicate by price_date, preferring AGMARKNET_SNAPSHOT if both present on the same day
    daily_trend: dict[str, float] = {}
    for p in prices_history:
        d_str = str(p.price_date)
        if d_str not in daily_trend or p.source == "AGMARKNET_SNAPSHOT":
            daily_trend[d_str] = float(p.modal_price_per_kg)

    trend = [TrendPoint(date=d, modal_price_per_kg=val) for d, val in sorted(daily_trend.items())]

    fee_pct = float(cfg.get("platform_fee_pct", 2.0))
    assumptions = ScenarioAssumptions(
        platform_fee_pct=fee_pct,
        commission_agent_pct=float(cfg.get("commission_agent_pct", 5.0)),
        trader_margin_pct=float(cfg.get("trader_margin_pct", 8.0)),
        retail_margin_pct=float(cfg.get("retail_margin_pct", 12.0)),
        last_mile_cost_per_kg=float(cfg.get("last_mile_cost_per_kg", 1.0)),
    )

    if mkt_price:
        benchmark_info = BenchmarkInfo(
            hub=hub_info,
            market_name=mkt_price.market_name,
            price_date=str(mkt_price.price_date),
            modal_price_per_kg=float(mkt_price.modal_price_per_kg),
            min_price_per_kg=float(mkt_price.min_price_per_kg),
            max_price_per_kg=float(mkt_price.max_price_per_kg),
            source=mkt_price.source,
            is_synthetic=mkt_price.is_synthetic,
        )

        modal_val = float(mkt_price.modal_price_per_kg)
        # Indicative transport for fair band calculation using default 1000 kg and average regional distance 50 km
        vehicle_types = get_vehicle_types(db)
        indicative_dist = 50.0
        trip_est = estimate_dedicated_trip(indicative_dist, quantity_kg, vehicle_types)
        indicative_transport_per_kg = trip_est["cost_per_kg"]

        farmer_mandi_net = (modal_val * (1.0 - assumptions.commission_agent_pct / 100.0)) - indicative_transport_per_kg
        buyer_traditional = (
            modal_val * (1.0 + assumptions.trader_margin_pct / 100.0) * (1.0 + assumptions.retail_margin_pct / 100.0)
        ) + assumptions.last_mile_cost_per_kg

        fair_band = compute_fair_band(
            farmer_mandi_net=farmer_mandi_net,
            buyer_traditional=buyer_traditional,
            transport_per_kg=indicative_transport_per_kg,
            platform_fee_pct=fee_pct,
        )

    return PricingBenchmarkResponse(
        hub=hub_info,
        benchmark=benchmark_info,
        trend=trend,
        fair_band=fair_band,
        assumptions=assumptions,
    )
