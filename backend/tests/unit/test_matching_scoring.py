from datetime import date, timedelta

from app.modules.matching.scoring import (
    compute_scores,
    evaluate_hard_filters,
    generate_reasons,
    load_matching_config,
)


class DummyCrop:
    def __init__(self, shelf_life_days=7, max_transit_hours=12.0):
        self.shelf_life_days = shelf_life_days
        self.max_transit_hours = max_transit_hours


class DummyListing:
    def __init__(
        self,
        id=1,
        status="ACTIVE",
        grade="A",
        available_until=None,
        available_from=None,
        harvest_date=None,
        quantity_available_kg=1000.0,
        ask_price_per_kg=20.0,
        min_order_kg=100.0,
    ):
        today = date(2026, 10, 2)
        self.id = id
        self.status = status
        self.grade = grade
        self.available_until = available_until or (today + timedelta(days=5))
        self.available_from = available_from or today
        self.harvest_date = harvest_date or (today - timedelta(days=1))
        self.quantity_available_kg = quantity_available_kg
        self.ask_price_per_kg = ask_price_per_kg
        self.min_order_kg = min_order_kg


class DummyRequirement:
    def __init__(
        self,
        grade_min="B",
        needed_by=None,
        max_landed_price_per_kg=35.0,
        quantity_kg=1000.0,
    ):
        today = date(2026, 10, 2)
        self.grade_min = grade_min
        self.needed_by = needed_by or (today + timedelta(days=3))
        self.max_landed_price_per_kg = max_landed_price_per_kg
        self.quantity_kg = quantity_kg


DEFAULT_VEHICLES = [
    {
        "vehicle_type": "MINI_TRUCK",
        "capacity_kg": 750.0,
        "cost_per_km": 12.0,
        "fixed_cost_per_trip": 400.0,
        "avg_speed_kmph": 30.0,
    },
    {
        "vehicle_type": "PICKUP",
        "capacity_kg": 1500.0,
        "cost_per_km": 16.0,
        "fixed_cost_per_trip": 600.0,
        "avg_speed_kmph": 30.0,
    },
    {
        "vehicle_type": "MEDIUM_TRUCK",
        "capacity_kg": 4000.0,
        "cost_per_km": 26.0,
        "fixed_cost_per_trip": 1200.0,
        "avg_speed_kmph": 30.0,
    },
]


def test_f1_availability_and_expiry_failures():
    today = date(2026, 10, 2)
    cfg = load_matching_config()
    crop = DummyCrop()
    req = DummyRequirement()
    p_coords = (28.7, 77.1)
    b_coords = (28.5, 77.3)

    # 1. Inactive status
    l_inactive = DummyListing(status="SOLD_OUT")
    passed, reason, detail, _ = evaluate_hard_filters(
        l_inactive, req, crop, p_coords, b_coords, 1000.0, DEFAULT_VEHICLES, cfg, today=today
    )
    assert not passed
    assert reason == "AVAILABILITY"

    # 2. Expired listing
    l_expired = DummyListing(available_until=today - timedelta(days=1))
    passed, reason, detail, _ = evaluate_hard_filters(
        l_expired, req, crop, p_coords, b_coords, 1000.0, DEFAULT_VEHICLES, cfg, today=today
    )
    assert not passed
    assert reason == "AVAILABILITY"

    # 3. Available qty < 1 kg
    l_zero_qty = DummyListing(quantity_available_kg=0.5)
    passed, reason, detail, _ = evaluate_hard_filters(
        l_zero_qty, req, crop, p_coords, b_coords, 1000.0, DEFAULT_VEHICLES, cfg, today=today
    )
    assert not passed
    assert reason == "AVAILABILITY"


def test_f2_grade_hierarchy_failure():
    today = date(2026, 10, 2)
    cfg = load_matching_config()
    crop = DummyCrop()
    req = DummyRequirement(grade_min="A")
    p_coords = (28.7, 77.1)
    b_coords = (28.5, 77.3)

    # Listing has grade B, requirement requires A
    l_b = DummyListing(grade="B")
    passed, reason, detail, _ = evaluate_hard_filters(
        l_b, req, crop, p_coords, b_coords, 1000.0, DEFAULT_VEHICLES, cfg, today=today
    )
    assert not passed
    assert reason == "GRADE"
    assert "below minimum requirement grade A" in detail


def test_f3_distance_boundary_failure():
    today = date(2026, 10, 2)
    cfg = load_matching_config()
    crop = DummyCrop()
    req = DummyRequirement()
    # Far coordinates > 300 km
    p_far = (26.0, 75.0)  # ~350 km away
    b_coords = (28.5, 77.3)

    listing = DummyListing()
    passed, reason, detail, metrics = evaluate_hard_filters(
        listing, req, crop, p_far, b_coords, 1000.0, DEFAULT_VEHICLES, cfg, today=today
    )
    assert not passed
    assert reason == "DISTANCE"
    assert metrics["distance_km"] > 300.0


def test_f4_earliest_delivery_failure():
    today = date(2026, 10, 2)
    cfg = load_matching_config()
    crop = DummyCrop()
    # Needed by is today, but available_from is in 2 days
    req = DummyRequirement(needed_by=today)
    l_future = DummyListing(available_from=today + timedelta(days=2))
    p_coords = (28.7, 77.1)
    b_coords = (28.5, 77.3)

    passed, reason, detail, _ = evaluate_hard_filters(
        l_future, req, crop, p_coords, b_coords, 1000.0, DEFAULT_VEHICLES, cfg, today=today
    )
    assert not passed
    assert reason == "AVAILABILITY"
    assert "is after buyer needed by date" in detail


def test_f5_freshness_and_shelf_life_failure():
    today = date(2026, 10, 2)
    cfg = load_matching_config()
    # Crop shelf life is 3 days
    crop = DummyCrop(shelf_life_days=3, max_transit_hours=10.0)
    req = DummyRequirement(needed_by=today + timedelta(days=5))
    # Harvest was 4 days ago
    l_old = DummyListing(harvest_date=today - timedelta(days=4))
    p_coords = (28.7, 77.1)
    b_coords = (28.5, 77.3)

    passed, reason, detail, _ = evaluate_hard_filters(
        l_old, req, crop, p_coords, b_coords, 1000.0, DEFAULT_VEHICLES, cfg, today=today
    )
    assert not passed
    assert reason == "FRESHNESS"
    assert "exceeds shelf life" in detail


def test_f6_budget_limit_failure():
    today = date(2026, 10, 2)
    cfg = load_matching_config()
    crop = DummyCrop()
    # Max landed budget is ₹20.00, but ask is ₹25.00
    req = DummyRequirement(max_landed_price_per_kg=20.0)
    listing = DummyListing(ask_price_per_kg=25.0)
    p_coords = (28.7, 77.1)
    b_coords = (28.5, 77.3)

    passed, reason, detail, metrics = evaluate_hard_filters(
        listing, req, crop, p_coords, b_coords, 1000.0, DEFAULT_VEHICLES, cfg, today=today
    )
    assert not passed
    assert reason == "BUDGET"
    assert metrics["landed_price_per_kg"] > 20.0
    assert "over budget" in detail


def test_score_computation_and_clamping():
    cfg = load_matching_config()
    # Verify bounds when inputs are extreme
    scores_high, weights = compute_scores(
        landed_price=10.0,
        max_landed_budget=30.0,
        distance_km=10.0,
        age_at_delivery_days=1,
        shelf_life_days=10,
        available_qty=2000.0,
        requirement_qty=1000.0,
        cfg=cfg,
    )
    assert 0.0 <= scores_high["price"] <= 1.0
    assert 0.0 <= scores_high["distance"] <= 1.0
    assert 0.0 <= scores_high["freshness"] <= 1.0
    assert 0.0 <= scores_high["fill"] <= 1.0
    assert 0.0 <= scores_high["total"] <= 1.0

    # Extremely poor scores
    scores_low, _ = compute_scores(
        landed_price=35.0,
        max_landed_budget=30.0,
        distance_km=400.0,
        age_at_delivery_days=12,
        shelf_life_days=10,
        available_qty=0.0,
        requirement_qty=1000.0,
        cfg=cfg,
    )
    assert scores_low["price"] == 0.0
    assert scores_low["distance"] == 0.0
    assert scores_low["freshness"] == 0.0
    assert scores_low["fill"] == 0.0
    assert scores_low["total"] == 0.0


def test_deterministic_reasons():
    reasons = generate_reasons(
        landed_price=25.60,
        max_landed_budget=29.00,
        distance_km=58.2,
        transit_hours=2.5,
        age_at_delivery_days=2,
        shelf_life_days=7,
        available_qty=2000.0,
        requirement_qty=1500.0,
    )
    assert len(reasons) >= 4
    # Numerical validation in strings
    assert any("11.7% below" in r for r in reasons)
    assert any("58.2 km" in r for r in reasons)
    assert any("2 days from harvest" in r for r in reasons)
    assert any("100% of requested" in r for r in reasons)


def test_deterministic_tie_breaking():
    # Sort key: (-total, landed, id)
    cands = [
        {"scores": {"total": 0.85}, "landed_price_per_kg": 25.0, "listing": DummyListing(id=3)},
        {"scores": {"total": 0.90}, "landed_price_per_kg": 26.0, "listing": DummyListing(id=2)},
        {"scores": {"total": 0.85}, "landed_price_per_kg": 24.0, "listing": DummyListing(id=1)},
        {"scores": {"total": 0.85}, "landed_price_per_kg": 24.0, "listing": DummyListing(id=4)},
    ]
    cands.sort(key=lambda c: (-c["scores"]["total"], c["landed_price_per_kg"], c["listing"].id))
    # Cand 2 (score 0.90) must be first
    assert cands[0]["listing"].id == 2
    # Cand 1 and 4 have score 0.85 and landed 24.0, so Cand 1 (lower id 1 < 4) comes before 4
    assert cands[1]["listing"].id == 1
    assert cands[2]["listing"].id == 4
    # Cand 3 has score 0.85 and landed 25.0
    assert cands[3]["listing"].id == 3
