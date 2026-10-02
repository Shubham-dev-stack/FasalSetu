import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from app.core.dates import today_ist
from app.core.geo import road_distance_km
from app.modules.logistics.cost import estimate_dedicated_trip

GRADE_RANKS = {"A": 3, "B": 2, "C": 1}

DEFAULT_MATCHING_CONFIG: dict[str, Any] = {
    "weights": {
        "price": 0.40,
        "distance": 0.20,
        "freshness": 0.20,
        "fill": 0.20,
    },
    "price_headroom_fraction": 0.30,
    "max_match_distance_km": 300.0,
    "supply_radius_km": 150.0,
    "shortage_ratio": 0.7,
    "surplus_ratio": 1.3,
}


def load_matching_config() -> dict[str, Any]:
    config_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "config"
        / "matching.yaml"
    )
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded and isinstance(loaded, dict):
                    # Merge with default config
                    cfg = dict(DEFAULT_MATCHING_CONFIG)
                    cfg.update(loaded)
                    return cfg
        except Exception:
            pass
    return DEFAULT_MATCHING_CONFIG


def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    return max(min_val, min(max_val, val))


def evaluate_hard_filters(
    listing: Any,
    requirement: Any,
    crop: Any,
    producer_coords: tuple[float, float],
    buyer_coords: tuple[float, float],
    remaining_qty: float,
    vehicle_types: list[dict],
    cfg: dict[str, Any],
    today: date | None = None,
) -> tuple[bool, str | None, str | None, dict[str, Any]]:
    """Evaluates hard filters F1 to F6 for a listing against a requirement.

    Returns:
        (passed, failure_reason, detail, metrics_dict)
        where failure_reason is one of:
        "AVAILABILITY", "GRADE", "DISTANCE", "FRESHNESS", "BUDGET"
    """
    if today is None:
        today = today_ist()

    max_dist_km = float(cfg.get("max_match_distance_km", 300.0))

    # F1: Availability & Expiry
    if listing.status != "ACTIVE":
        return False, "AVAILABILITY", f"Listing status is {listing.status}, must be ACTIVE", {}
    if listing.available_until < today:
        return False, "AVAILABILITY", f"Listing expired on {listing.available_until}", {}
    if float(listing.quantity_available_kg) < 1.0:
        return False, "AVAILABILITY", "Listing available quantity is less than 1 kg", {}

    # F2: Grade Hierarchy
    l_rank = GRADE_RANKS.get(listing.grade, 0)
    r_rank = GRADE_RANKS.get(requirement.grade_min, 0)
    if l_rank < r_rank:
        return (
            False,
            "GRADE",
            f"Listing grade {listing.grade} is below minimum requirement grade {requirement.grade_min}",
            {},
        )

    # F3: Distance limit
    dist_km = road_distance_km(producer_coords, buyer_coords, circuity=1.35)
    if dist_km > max_dist_km:
        return (
            False,
            "DISTANCE",
            f"Distance {dist_km:.1f} km exceeds maximum match radius of {max_dist_km:.0f} km",
            {"distance_km": dist_km},
        )

    # Calculate logistics & transit metrics for F4, F5, F6
    # Quantity basis for transport estimate is min(available, remaining_qty)
    alloc_basis_qty = min(float(listing.quantity_available_kg), remaining_qty)
    if alloc_basis_qty <= 0:
        alloc_basis_qty = float(listing.quantity_available_kg)

    trip_est = estimate_dedicated_trip(dist_km, alloc_basis_qty, vehicle_types)
    transit_hours = trip_est["transit_hours"]
    transport_cost_per_kg = trip_est["cost_per_kg"]

    # F4: Earliest Delivery
    transit_days = math.floor(transit_hours / 24.0)
    earliest_available = max(today, listing.available_from)
    earliest_delivery = earliest_available + timedelta(days=transit_days)

    if earliest_delivery > requirement.needed_by:
        return (
            False,
            "AVAILABILITY",
            f"Earliest delivery {earliest_delivery} is after buyer needed by date {requirement.needed_by}",
            {"earliest_delivery": earliest_delivery, "distance_km": dist_km},
        )

    # F5: Freshness & Transit Shelf Life
    age_at_delivery = (earliest_delivery - listing.harvest_date).days
    shelf_life = crop.shelf_life_days
    max_transit_hours = crop.max_transit_hours

    if age_at_delivery > shelf_life:
        return (
            False,
            "FRESHNESS",
            f"Age at delivery {age_at_delivery} days exceeds shelf life {shelf_life} days",
            {
                "age_at_delivery": age_at_delivery,
                "transit_hours": transit_hours,
                "distance_km": dist_km,
            },
        )
    if transit_hours > max_transit_hours:
        return (
            False,
            "FRESHNESS",
            f"Transit duration {transit_hours:.1f}h exceeds max transit limit {max_transit_hours:.1f}h",
            {
                "age_at_delivery": age_at_delivery,
                "transit_hours": transit_hours,
                "distance_km": dist_km,
            },
        )

    # F6: Max Landed Budget
    ask_price = float(listing.ask_price_per_kg)
    platform_fee = round(ask_price * 0.02, 2)
    landed_price = round(ask_price + transport_cost_per_kg + platform_fee, 2)
    max_landed = float(requirement.max_landed_price_per_kg)

    metrics = {
        "distance_km": dist_km,
        "transit_hours": transit_hours,
        "earliest_delivery": earliest_delivery,
        "age_at_delivery": age_at_delivery,
        "ask_price_per_kg": ask_price,
        "transport_cost_per_kg": transport_cost_per_kg,
        "platform_fee_per_kg": platform_fee,
        "landed_price_per_kg": landed_price,
    }

    if landed_price > max_landed:
        gap = landed_price - max_landed
        return (
            False,
            "BUDGET",
            f"Landed ₹{landed_price:.2f}/kg is ₹{gap:.2f}/kg over budget ₹{max_landed:.2f}/kg",
            metrics,
        )

    return True, None, None, metrics


def compute_scores(
    landed_price: float,
    max_landed_budget: float,
    distance_km: float,
    age_at_delivery_days: int,
    shelf_life_days: int,
    available_qty: float,
    requirement_qty: float,
    cfg: dict[str, Any],
) -> tuple[dict[str, float], dict[str, float]]:
    """Calculates deterministic matching score and component factor scores (0.0 to 1.0)."""
    weights = cfg.get("weights", DEFAULT_MATCHING_CONFIG["weights"])
    w_price = float(weights.get("price", 0.40))
    w_dist = float(weights.get("distance", 0.20))
    w_fresh = float(weights.get("freshness", 0.20))
    w_fill = float(weights.get("fill", 0.20))

    headroom = float(cfg.get("price_headroom_fraction", 0.30))
    max_dist = float(cfg.get("max_match_distance_km", 300.0))

    # Price score: clamp((1 - landed / P_max) / headroom, 0, 1)
    if max_landed_budget > 0:
        price_headroom_val = (1.0 - (landed_price / max_landed_budget)) / headroom
        price_score = clamp(price_headroom_val, 0.0, 1.0)
    else:
        price_score = 0.0

    # Distance score: clamp(1 - dist / max_dist, 0, 1)
    dist_score = clamp(1.0 - (distance_km / max_dist), 0.0, 1.0)

    # Freshness score: clamp(1 - age / shelf_life, 0, 1)
    if shelf_life_days > 0:
        fresh_score = clamp(1.0 - (age_at_delivery_days / shelf_life_days), 0.0, 1.0)
    else:
        fresh_score = 0.0

    # Fill score: min(available, Q) / Q
    if requirement_qty > 0:
        fill_score = clamp(min(available_qty, requirement_qty) / requirement_qty, 0.0, 1.0)
    else:
        fill_score = 0.0

    total_score = (
        (w_price * price_score)
        + (w_dist * dist_score)
        + (w_fresh * fresh_score)
        + (w_fill * fill_score)
    )
    total_score = clamp(total_score, 0.0, 1.0)

    scores = {
        "price": round(price_score, 4),
        "distance": round(dist_score, 4),
        "freshness": round(fresh_score, 4),
        "fill": round(fill_score, 4),
        "total": round(total_score, 4),
    }

    used_weights = {
        "price": w_price,
        "distance": w_dist,
        "freshness": w_fresh,
        "fill": w_fill,
    }

    return scores, used_weights


def generate_reasons(
    landed_price: float,
    max_landed_budget: float,
    distance_km: float,
    transit_hours: float,
    age_at_delivery_days: int,
    shelf_life_days: int,
    available_qty: float,
    requirement_qty: float,
) -> list[str]:
    """Generates deterministic, numerical explanation reasons strictly from calculated values."""
    reasons: list[str] = []

    # 1. Price explanation
    if max_landed_budget > 0:
        if landed_price < max_landed_budget:
            pct_below = round(((max_landed_budget - landed_price) / max_landed_budget) * 100, 1)
            reasons.append(
                f"Landed ₹{landed_price:.2f}/kg is {pct_below}% below your ₹{max_landed_budget:.2f} budget"
            )
        else:
            reasons.append(
                f"Landed ₹{landed_price:.2f}/kg meets your max budget of ₹{max_landed_budget:.2f}/kg"
            )

    # 2. Distance explanation
    if distance_km <= 75.0:
        reasons.append(f"Nearby source ({distance_km:.1f} km est., ~{transit_hours:.1f}h transit)")
    else:
        reasons.append(
            f"Transport distance {distance_km:.1f} km est. ({transit_hours:.1f}h transit)"
        )

    # 3. Freshness explanation
    reasons.append(
        f"Fresh produce ({age_at_delivery_days} days from harvest at delivery vs {shelf_life_days}d shelf life)"
    )

    # 4. Fill explanation
    if available_qty >= requirement_qty:
        reasons.append(f"Single lot can fulfill 100% of requested {requirement_qty:,.0f} kg")
    else:
        fill_pct = round((available_qty / requirement_qty) * 100, 1)
        reasons.append(
            f"Supplies {fill_pct}% ({available_qty:,.0f} kg) of requested {requirement_qty:,.0f} kg"
        )

    return reasons
