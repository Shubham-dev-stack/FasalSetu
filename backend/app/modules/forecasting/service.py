import json
import logging
import math
import time
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dates import today_ist
from app.core.errors import AppException
from app.db.models import Crop, DemandHistory, DemandHub, Listing, ProducerProfile
from ml.predict import get_model_artifacts, predict_demand

logger = logging.getLogger("fasalsetu.forecasting.service")

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ARTIFACTS_DIR = BASE_DIR / "ml" / "artifacts"


class TimedCache:
    """Timestamp-aware memory cache with configurable TTL (default 1 hour = 3600 seconds)."""

    def __init__(self, ttl_seconds: float = 3600.0):
        self.ttl_seconds = ttl_seconds
        self._cache: dict[tuple[Any, ...], tuple[float, Any]] = {}

    def get(self, key: tuple[Any, ...]) -> Any | None:
        now = time.time()
        if key in self._cache:
            created_at, val = self._cache[key]
            if now - created_at < self.ttl_seconds:
                return val
            del self._cache[key]
        return None

    def set(self, key: tuple[Any, ...], val: Any) -> None:
        self._cache[key] = (time.time(), val)

    def clear(self) -> None:
        self._cache.clear()


# Singleton forecast cache with 1-hour TTL
forecast_cache = TimedCache(ttl_seconds=3600.0)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * r * math.asin(math.sqrt(a))


def get_demand_forecast(
    db: Session,
    hub_id: int,
    crop_id: int,
    horizon_days: int = 7,
    cutoff_date: date | None = None,
) -> dict[str, Any]:
    """Retrieve demand forecast with timestamp-aware 1-hour TTL cache."""
    # Determine effective cutoff date for cache key
    if cutoff_date is None:
        max_record_date = (
            db.query(func.max(DemandHistory.date))
            .filter(DemandHistory.hub_id == hub_id, DemandHistory.crop_id == crop_id)
            .scalar()
        )
        effective_cutoff = max_record_date or today_ist()
    else:
        effective_cutoff = cutoff_date

    cache_key = (hub_id, crop_id, effective_cutoff.isoformat(), horizon_days)
    cached = forecast_cache.get(cache_key)
    if cached is not None:
        return cached

    forecast = predict_demand(
        db=db,
        hub_id=hub_id,
        crop_id=crop_id,
        horizon_days=horizon_days,
        cutoff_date=cutoff_date,
    )
    forecast_cache.set(cache_key, forecast)
    return forecast


def get_hubs_forecast_and_opportunity(
    db: Session,
    crop_id: int,
    horizon_days: int = 7,
    cutoff_date: date | None = None,
) -> dict[str, Any]:
    """Compare all 5 demand hubs for a crop and compute supply-demand ratios with Rule D-026 supply attribution."""
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise AppException(
            status_code=404,
            code="CROP_NOT_FOUND",
            message=f"Crop with ID {crop_id} not found.",
        )

    hubs = db.query(DemandHub).order_by(DemandHub.id.asc()).all()
    if not hubs:
        raise AppException(
            status_code=404,
            code="NO_HUBS_FOUND",
            message="No demand hubs found in database.",
        )

    # 1. Attribute Active Produce Supply to Nearest Hub (Rule D-026: No multi-hub double counting)
    today = today_ist()
    active_listings = (
        db.query(Listing)
        .join(ProducerProfile, Listing.producer_id == ProducerProfile.id)
        .filter(
            Listing.crop_id == crop_id,
            Listing.status == "ACTIVE",
            Listing.available_until >= today,
            Listing.quantity_available_kg > 0,
        )
        .all()
    )

    supply_by_hub: dict[int, float] = {h.id: 0.0 for h in hubs}
    for listing in active_listings:
        producer = listing.producer
        if not producer:
            continue
        p_lat, p_lng = producer.lat, producer.lng

        # Find nearest hub center
        nearest_hub = min(
            hubs,
            key=lambda h: haversine_km(p_lat, p_lng, h.lat, h.lng),
        )
        supply_by_hub[nearest_hub.id] += float(listing.quantity_available_kg)

    # 2. Compute forecast and supply-demand ratio for each hub
    hub_items = []
    effective_cutoff_str = ""

    for hub in hubs:
        fc = get_demand_forecast(
            db=db,
            hub_id=hub.id,
            crop_id=crop_id,
            horizon_days=horizon_days,
            cutoff_date=cutoff_date,
        )
        effective_cutoff_str = fc["cutoff_date"]

        total_demand = sum(item["point_forecast_kg"] for item in fc["forecast"])
        avg_daily = total_demand / horizon_days if horizon_days > 0 else 0.0
        active_supply = supply_by_hub.get(hub.id, 0.0)

        if total_demand > 0:
            ratio = round(active_supply / total_demand, 2)
        else:
            ratio = 0.0

        if ratio < 0.5:
            opportunity_label = "HIGH_DEFICIT"
        elif ratio <= 1.2:
            opportunity_label = "BALANCED"
        else:
            opportunity_label = "OVERSUPPLIED"

        hub_items.append(
            {
                "hub_id": hub.id,
                "hub_name": hub.name,
                "state": hub.state,
                "lat": hub.lat,
                "lng": hub.lng,
                "total_forecast_kg": round(total_demand, 1),
                "avg_daily_forecast_kg": round(avg_daily, 1),
                "active_supply_kg": round(active_supply, 1),
                "supply_demand_ratio": ratio,
                "opportunity_label": opportunity_label,
                "method": fc["method"],
            }
        )

    # Sort hubs by opportunity (lowest supply-demand ratio first -> highest deficit opportunity)
    hub_items.sort(key=lambda h: (h["supply_demand_ratio"], -h["total_forecast_kg"]))

    return {
        "crop_id": crop.id,
        "crop_name": crop.name,
        "cutoff_date": effective_cutoff_str,
        "horizon_days": horizon_days,
        "demand_data_source": "SYNTHETIC",
        "disclaimer": (
            "Demand history is synthetic, generated from a documented process. "
            "Forecast metrics validate the pipeline, not real-world accuracy."
        ),
        "hubs": hub_items,
    }


def get_forecast_model_info() -> dict[str, Any]:
    """Retrieve model card and validation/test metrics for transparency."""
    artifacts = get_model_artifacts()
    if artifacts and "model_card" in artifacts:
        return artifacts["model_card"]

    card_path = ARTIFACTS_DIR / "model_card.json"
    if card_path.exists():
        with open(card_path) as f:
            return json.load(f)

    return {
        "model_id": "MOD-01",
        "model_version": "1.0.0",
        "trained_at": "N/A",
        "git_commit": "N/A",
        "dataset_hash_sha256": "N/A",
        "generator_version": "1.0",
        "demand_data_source": "SYNTHETIC",
        "price_feature_sources": ["SYNTHETIC_DEMO", "AGMARKNET_SNAPSHOT"],
        "reproducibility": "Reproducible within the pinned project environment, dependency versions, dataset, generator version, and fixed seed.",
        "deployed_method": "SEASONAL_NAIVE",
        "deployment_gate": {
            "passed": False,
            "deployed_method": "SEASONAL_NAIVE",
            "reason": "Model artifacts not loaded",
        },
        "metrics": {"validation": {}, "test": {}},
        "split_spec": {},
        "disclaimer": "Demand history is synthetic, generated from a documented process. Forecast metrics validate the pipeline, not real-world accuracy.",
    }
