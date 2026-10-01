from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.dates import today_ist
from app.core.geo import road_distance_km
from app.core.security import hash_password
from app.db.models import (
    BuyerProfile,
    Crop,
    DemandHub,
    Listing,
    Order,
    OrderEvent,
    ProducerProfile,
    Requirement,
    User,
    Vehicle,
)
from app.modules.logistics.cost import estimate_dedicated_trip
from app.modules.logistics.fleet import get_vehicle_types

CANONICAL_PERSONAS = {
    "fpo_sonipat": "fpo_sonipat@demo.fasalsetu.local",
    "fpo_meerut": "fpo_meerut@demo.fasalsetu.local",
    "farmer_karnal": "farmer_karnal@demo.fasalsetu.local",
    "buyer_gurugram": "buyer_gurugram@demo.fasalsetu.local",
    "buyer_noida": "buyer_noida@demo.fasalsetu.local",
    "operator": "operator@demo.fasalsetu.local",
}


def seed_reference_and_users(db: Session) -> dict:
    """Deterministically seed crops, hubs, users/profiles, and vehicles per Data.md §12."""
    default_pw_hash = hash_password("demo1234")

    # 1. Crops
    crops_data = [
        {
            "id": 1,
            "name": "Tomato",
            "category": "VEGETABLE",
            "agmarknet_commodity_name": "Tomato",
            "shelf_life_days": 7,
            "max_transit_hours": 12,
            "perishability": "HIGH",
            "notes": "ASSUMPTION",
        },
        {
            "id": 2,
            "name": "Onion",
            "category": "VEGETABLE",
            "agmarknet_commodity_name": "Onion",
            "shelf_life_days": 60,
            "max_transit_hours": 48,
            "perishability": "LOW",
            "notes": "ASSUMPTION",
        },
        {
            "id": 3,
            "name": "Potato",
            "category": "VEGETABLE",
            "agmarknet_commodity_name": "Potato",
            "shelf_life_days": 60,
            "max_transit_hours": 48,
            "perishability": "LOW",
            "notes": "ASSUMPTION",
        },
        {
            "id": 4,
            "name": "Cauliflower",
            "category": "VEGETABLE",
            "agmarknet_commodity_name": "Cauliflower",
            "shelf_life_days": 5,
            "max_transit_hours": 10,
            "perishability": "HIGH",
            "notes": "ASSUMPTION",
        },
        {
            "id": 5,
            "name": "Green Chilli",
            "category": "VEGETABLE",
            "agmarknet_commodity_name": "Green Chilli",
            "shelf_life_days": 7,
            "max_transit_hours": 12,
            "perishability": "HIGH",
            "notes": "ASSUMPTION",
        },
    ]
    for c in crops_data:
        existing = db.query(Crop).filter(Crop.id == c["id"]).first()
        if not existing:
            db.add(Crop(**c))

    # 2. Demand Hubs
    hubs_data = [
        {
            "id": 1,
            "name": "Delhi North",
            "city": "Delhi",
            "state": "Delhi",
            "lat": 28.70,
            "lng": 77.17,
            "reference_market_name": "Delhi North Reference Market (SYNTHETIC)",
        },
        {
            "id": 2,
            "name": "Gurugram",
            "city": "Gurugram",
            "state": "Haryana",
            "lat": 28.46,
            "lng": 77.03,
            "reference_market_name": "Gurugram Reference Market (SYNTHETIC)",
        },
        {
            "id": 3,
            "name": "Noida",
            "city": "Noida",
            "state": "Uttar Pradesh",
            "lat": 28.54,
            "lng": 77.39,
            "reference_market_name": "Noida Reference Market (SYNTHETIC)",
        },
        {
            "id": 4,
            "name": "Ghaziabad",
            "city": "Ghaziabad",
            "state": "Uttar Pradesh",
            "lat": 28.67,
            "lng": 77.45,
            "reference_market_name": "Ghaziabad Reference Market (SYNTHETIC)",
        },
        {
            "id": 5,
            "name": "Faridabad",
            "city": "Faridabad",
            "state": "Haryana",
            "lat": 28.41,
            "lng": 77.31,
            "reference_market_name": "Faridabad Reference Market (SYNTHETIC)",
        },
    ]
    for h in hubs_data:
        existing = db.query(DemandHub).filter(DemandHub.id == h["id"]).first()
        if not existing:
            db.add(DemandHub(**h))

    db.flush()

    # 3. Producers
    producers_data = [
        {
            "id": 1,
            "email": "fpo_sonipat@demo.fasalsetu.local",
            "display_name": "Sonipat Kisan Collective [DEMO]",
            "producer_type": "FPO",
            "org_name": "Sonipat Kisan Collective [DEMO]",
            "state": "Haryana",
            "district": "Sonipat",
            "lat": 28.99,
            "lng": 77.02,
            "member_farmers": 120,
        },
        {
            "id": 2,
            "email": "fpo_bulandshahr@demo.fasalsetu.local",
            "display_name": "Bulandshahr Growers Union [DEMO]",
            "producer_type": "FPO",
            "org_name": "Bulandshahr Growers Union [DEMO]",
            "state": "Uttar Pradesh",
            "district": "Bulandshahr",
            "lat": 28.41,
            "lng": 77.85,
            "member_farmers": 85,
        },
        {
            "id": 3,
            "email": "farmer_alwar@demo.fasalsetu.local",
            "display_name": "Alwar Farmer #1 [DEMO]",
            "producer_type": "FARMER",
            "org_name": "Alwar Farmer #1 [DEMO]",
            "state": "Rajasthan",
            "district": "Alwar",
            "lat": 27.56,
            "lng": 76.61,
            "member_farmers": None,
        },
        {
            "id": 4,
            "email": "fpo_meerut@demo.fasalsetu.local",
            "display_name": "Meerut Agri Producers [DEMO]",
            "producer_type": "FPO",
            "org_name": "Meerut Agri Producers [DEMO]",
            "state": "Uttar Pradesh",
            "district": "Meerut",
            "lat": 28.98,
            "lng": 77.71,
            "member_farmers": 210,
        },
        {
            "id": 5,
            "email": "farmer_karnal@demo.fasalsetu.local",
            "display_name": "Karnal Farmer #1 [DEMO]",
            "producer_type": "FARMER",
            "org_name": "Karnal Farmer #1 [DEMO]",
            "state": "Haryana",
            "district": "Karnal",
            "lat": 29.69,
            "lng": 76.99,
            "member_farmers": None,
        },
        {
            "id": 6,
            "email": "fpo_panipat@demo.fasalsetu.local",
            "display_name": "Panipat Vegetable Growers [DEMO]",
            "producer_type": "FPO",
            "org_name": "Panipat Vegetable Growers [DEMO]",
            "state": "Haryana",
            "district": "Panipat",
            "lat": 29.39,
            "lng": 76.97,
            "member_farmers": 140,
        },
    ]

    for p in producers_data:
        user = db.query(User).filter(User.email == p["email"]).first()
        if not user:
            user = User(
                email=p["email"],
                password_hash=default_pw_hash,
                role="PRODUCER",
                display_name=p["display_name"],
                is_demo=True,
            )
            db.add(user)
            db.flush()

        profile = (
            db.query(ProducerProfile).filter(ProducerProfile.user_id == user.id).first()
        )
        if not profile:
            profile = ProducerProfile(
                id=p["id"],
                user_id=user.id,
                producer_type=p["producer_type"],
                org_name=p["org_name"],
                state=p["state"],
                district=p["district"],
                lat=p["lat"],
                lng=p["lng"],
                member_farmers=p["member_farmers"],
                is_demo=True,
            )
            db.add(profile)

    # 4. Buyers
    buyers_data = [
        {
            "id": 1,
            "email": "buyer_gurugram@demo.fasalsetu.local",
            "display_name": "Gurugram Restaurant Group [DEMO]",
            "buyer_type": "RESTAURANT",
            "org_name": "Gurugram Restaurant Group [DEMO]",
            "hub_id": 2,
            "city": "Gurugram",
            "state": "Haryana",
            "lat": 28.47,
            "lng": 77.05,
        },
        {
            "id": 2,
            "email": "buyer_noida@demo.fasalsetu.local",
            "display_name": "Noida RWA Group-Buying Collective [DEMO]",
            "buyer_type": "CONSUMER_GROUP",
            "org_name": "Noida RWA Group-Buying Collective [DEMO]",
            "hub_id": 3,
            "city": "Noida",
            "state": "Uttar Pradesh",
            "lat": 28.57,
            "lng": 77.35,
        },
        {
            "id": 3,
            "email": "buyer_delhi@demo.fasalsetu.local",
            "display_name": "Delhi Fresh Retail Chain [DEMO]",
            "buyer_type": "RETAILER",
            "org_name": "Delhi Fresh Retail Chain [DEMO]",
            "hub_id": 1,
            "city": "Delhi",
            "state": "Delhi",
            "lat": 28.72,
            "lng": 77.15,
        },
        {
            "id": 4,
            "email": "buyer_ghaziabad@demo.fasalsetu.local",
            "display_name": "Ghaziabad Sauce & Pickle Processor [DEMO]",
            "buyer_type": "PROCESSOR",
            "org_name": "Ghaziabad Sauce & Pickle Processor [DEMO]",
            "hub_id": 4,
            "city": "Ghaziabad",
            "state": "Uttar Pradesh",
            "lat": 28.68,
            "lng": 77.42,
        },
        {
            "id": 5,
            "email": "buyer_faridabad@demo.fasalsetu.local",
            "display_name": "Faridabad Institutional Kitchen [DEMO]",
            "buyer_type": "INSTITUTION",
            "org_name": "Faridabad Institutional Kitchen [DEMO]",
            "hub_id": 5,
            "city": "Faridabad",
            "state": "Haryana",
            "lat": 28.42,
            "lng": 77.32,
        },
    ]

    for b in buyers_data:
        user = db.query(User).filter(User.email == b["email"]).first()
        if not user:
            user = User(
                email=b["email"],
                password_hash=default_pw_hash,
                role="BUYER",
                display_name=b["display_name"],
                is_demo=True,
            )
            db.add(user)
            db.flush()

        profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user.id).first()
        if not profile:
            profile = BuyerProfile(
                id=b["id"],
                user_id=user.id,
                buyer_type=b["buyer_type"],
                org_name=b["org_name"],
                hub_id=b["hub_id"],
                city=b["city"],
                state=b["state"],
                lat=b["lat"],
                lng=b["lng"],
                is_demo=True,
            )
            db.add(profile)

    # 5. Operator
    op_email = "operator@demo.fasalsetu.local"
    op_user = db.query(User).filter(User.email == op_email).first()
    if not op_user:
        op_user = User(
            email=op_email,
            password_hash=default_pw_hash,
            role="ADMIN",
            display_name="Platform Operator [DEMO]",
            is_demo=True,
        )
        db.add(op_user)

    # 6. Vehicles
    vehicles_data = [
        {
            "id": 1,
            "name": "MT-01",
            "vehicle_type": "MINI_TRUCK",
            "capacity_kg": 750.0,
            "cost_per_km": 12.0,
            "fixed_cost_per_trip": 400.0,
            "avg_speed_kmph": 30.0,
            "depot_name": "Sonipat Transport Hub (SYNTHETIC)",
            "depot_lat": 28.98,
            "depot_lng": 77.03,
            "is_available": True,
            "is_demo": True,
        },
        {
            "id": 2,
            "name": "PK-01",
            "vehicle_type": "PICKUP",
            "capacity_kg": 1500.0,
            "cost_per_km": 16.0,
            "fixed_cost_per_trip": 600.0,
            "avg_speed_kmph": 30.0,
            "depot_name": "Sonipat Transport Hub (SYNTHETIC)",
            "depot_lat": 28.98,
            "depot_lng": 77.03,
            "is_available": True,
            "is_demo": True,
        },
        {
            "id": 3,
            "name": "MD-01",
            "vehicle_type": "MEDIUM_TRUCK",
            "capacity_kg": 4000.0,
            "cost_per_km": 26.0,
            "fixed_cost_per_trip": 1200.0,
            "avg_speed_kmph": 30.0,
            "depot_name": "Sonipat Transport Hub (SYNTHETIC)",
            "depot_lat": 28.98,
            "depot_lng": 77.03,
            "is_available": True,
            "is_demo": True,
        },
        {
            "id": 4,
            "name": "PK-02",
            "vehicle_type": "PICKUP",
            "capacity_kg": 1500.0,
            "cost_per_km": 16.0,
            "fixed_cost_per_trip": 600.0,
            "avg_speed_kmph": 30.0,
            "depot_name": "Ghaziabad Transport Hub (SYNTHETIC)",
            "depot_lat": 28.66,
            "depot_lng": 77.44,
            "is_available": True,
            "is_demo": True,
        },
        {
            "id": 5,
            "name": "MT-02",
            "vehicle_type": "MINI_TRUCK",
            "capacity_kg": 750.0,
            "cost_per_km": 12.0,
            "fixed_cost_per_trip": 400.0,
            "avg_speed_kmph": 30.0,
            "depot_name": "Ghaziabad Transport Hub (SYNTHETIC)",
            "depot_lat": 28.66,
            "depot_lng": 77.44,
            "is_available": True,
            "is_demo": True,
        },
    ]

    for v in vehicles_data:
        existing = db.query(Vehicle).filter(Vehicle.id == v["id"]).first()
        if not existing:
            db.add(Vehicle(**v))

    db.commit()

    return {
        "crops": len(crops_data),
        "hubs": len(hubs_data),
        "producers": len(producers_data),
        "buyers": len(buyers_data),
        "users": len(producers_data) + len(buyers_data) + 1,
        "vehicles": len(vehicles_data),
    }


def seed_synthetic_demand_and_prices(db: Session, seed: int = 42) -> dict[str, int]:
    """Generate and persist synthetic demand panel and benchmark prices.

    PROTECTS REAL AGMARKNET DATA: Only records where is_synthetic=True and
    source='SYNTHETIC_DEMO' are cleared. Real snapshot rows remain untouched.
    """
    from ml.generate_data import generate_panels, save_datasets, seed_demand_and_prices

    complete_df, post_drop_df, prices_df = generate_panels(seed=seed)
    save_datasets(post_drop_df, complete_df, prices_df)
    counts = seed_demand_and_prices(db, post_drop_df, prices_df)
    return counts


def seed_demo_listings(db: Session) -> dict[str, int]:
    """Deterministically seed listings L1-L14 per Data.md §12."""
    today = today_ist()

    # Per Data.md §12:
    # Tomato(1), Cauliflower(4), Green Chilli(5): harvest=today-1, available=today -> today+3
    # Onion(2), Potato(3): harvest=today-3, available=today -> today+10
    listings_data = [
        {"id": 1, "producer_id": 2, "crop_id": 1, "grade": "B", "quantity_kg": 800.0, "ask_price_per_kg": 22.50, "min_order_kg": 100.0, "is_high_perish": True},
        {"id": 2, "producer_id": 6, "crop_id": 1, "grade": "A", "quantity_kg": 1200.0, "ask_price_per_kg": 24.00, "min_order_kg": 200.0, "is_high_perish": True},
        {"id": 3, "producer_id": 3, "crop_id": 1, "grade": "C", "quantity_kg": 600.0, "ask_price_per_kg": 19.50, "min_order_kg": 100.0, "is_high_perish": True},
        {"id": 4, "producer_id": 5, "crop_id": 1, "grade": "B", "quantity_kg": 500.0, "ask_price_per_kg": 23.00, "min_order_kg": 100.0, "is_high_perish": True},
        {"id": 5, "producer_id": 4, "crop_id": 2, "grade": "A", "quantity_kg": 6000.0, "ask_price_per_kg": 22.50, "min_order_kg": 500.0, "is_high_perish": False},
        {"id": 6, "producer_id": 2, "crop_id": 2, "grade": "B", "quantity_kg": 3000.0, "ask_price_per_kg": 21.50, "min_order_kg": 500.0, "is_high_perish": False},
        {"id": 7, "producer_id": 3, "crop_id": 2, "grade": "B", "quantity_kg": 2000.0, "ask_price_per_kg": 21.00, "min_order_kg": 300.0, "is_high_perish": False},
        {"id": 8, "producer_id": 4, "crop_id": 3, "grade": "A", "quantity_kg": 4000.0, "ask_price_per_kg": 18.00, "min_order_kg": 500.0, "is_high_perish": False},
        {"id": 9, "producer_id": 2, "crop_id": 3, "grade": "B", "quantity_kg": 2500.0, "ask_price_per_kg": 17.00, "min_order_kg": 300.0, "is_high_perish": False},
        {"id": 10, "producer_id": 1, "crop_id": 4, "grade": "A", "quantity_kg": 700.0, "ask_price_per_kg": 28.50, "min_order_kg": 100.0, "is_high_perish": True},
        {"id": 11, "producer_id": 6, "crop_id": 4, "grade": "B", "quantity_kg": 500.0, "ask_price_per_kg": 27.00, "min_order_kg": 100.0, "is_high_perish": True},
        {"id": 12, "producer_id": 5, "crop_id": 5, "grade": "A", "quantity_kg": 300.0, "ask_price_per_kg": 46.00, "min_order_kg": 50.0, "is_high_perish": True},
        {"id": 13, "producer_id": 1, "crop_id": 5, "grade": "B", "quantity_kg": 250.0, "ask_price_per_kg": 43.50, "min_order_kg": 50.0, "is_high_perish": True},
        {"id": 14, "producer_id": 6, "crop_id": 5, "grade": "A", "quantity_kg": 200.0, "ask_price_per_kg": 47.00, "min_order_kg": 50.0, "is_high_perish": True},
    ]

    count = 0
    for item in listings_data:
        is_high = item.pop("is_high_perish")
        harvest_date = today - timedelta(days=1 if is_high else 3)
        available_from = today
        available_until = today + timedelta(days=3 if is_high else 10)

        existing = db.query(Listing).filter(Listing.id == item["id"]).first()
        if existing:
            existing.producer_id = item["producer_id"]
            existing.crop_id = item["crop_id"]
            existing.grade = item["grade"]
            existing.quantity_kg = item["quantity_kg"]
            existing.quantity_available_kg = item["quantity_kg"]
            existing.ask_price_per_kg = item["ask_price_per_kg"]
            existing.min_order_kg = item["min_order_kg"]
            existing.harvest_date = harvest_date
            existing.available_from = available_from
            existing.available_until = available_until
            existing.status = "ACTIVE"
            existing.is_demo = True
        else:
            listing = Listing(
                id=item["id"],
                producer_id=item["producer_id"],
                crop_id=item["crop_id"],
                grade=item["grade"],
                quantity_kg=item["quantity_kg"],
                quantity_available_kg=item["quantity_kg"],
                ask_price_per_kg=item["ask_price_per_kg"],
                min_order_kg=item["min_order_kg"],
                harvest_date=harvest_date,
                available_from=available_from,
                available_until=available_until,
                status="ACTIVE",
                is_demo=True,
            )
            db.add(listing)
        count += 1

    db.commit()
    return {"listings": count}


def seed_demo_requirements(db: Session) -> dict[str, int]:
    """Deterministically seed open requirements R1-R8 per Data.md §12."""
    today = today_ist()

    # Per Data.md §12:
    # R1: B1, Tomato(1), Grade B, 1500 kg, Max landed 29.00, needed_by = today + 1
    # R2: B5, Onion(2), Grade B, 6500 kg, Max landed 28.00, needed_by = today + 3
    # R3: B2, Cauliflower(4), Grade A, 1000 kg, Max landed 36.00, needed_by = today + 2
    # R4: B3, Potato(3), Grade B, 3000 kg, Max landed 24.00, needed_by = today + 2
    # R5: B4, Tomato(1), Grade C, 1000 kg, Max landed 27.00, needed_by = today + 2
    # R6: B1, Green Chilli(5), Grade B, 300 kg, Max landed 55.00, needed_by = today + 2
    # R7: B3, Cauliflower(4), Grade B, 400 kg, Max landed 36.00, needed_by = today + 1
    # R8: B5, Tomato(1), Grade A, 2500 kg, Max landed 22.00, needed_by = today + 2
    requirements_data = [
        {"id": 1, "buyer_id": 1, "crop_id": 1, "grade_min": "B", "quantity_kg": 1500.0, "max_landed_price_per_kg": 29.00, "days_ahead": 1, "notes": "Live demo: match before/after new listing"},
        {"id": 2, "buyer_id": 5, "crop_id": 2, "grade_min": "B", "quantity_kg": 6500.0, "max_landed_price_per_kg": 28.00, "days_ahead": 3, "notes": "Multi-source allocation"},
        {"id": 3, "buyer_id": 2, "crop_id": 4, "grade_min": "A", "quantity_kg": 1000.0, "max_landed_price_per_kg": 36.00, "days_ahead": 2, "notes": "Partial fill"},
        {"id": 4, "buyer_id": 3, "crop_id": 3, "grade_min": "B", "quantity_kg": 3000.0, "max_landed_price_per_kg": 24.00, "days_ahead": 2, "notes": "Normal match"},
        {"id": 5, "buyer_id": 4, "crop_id": 1, "grade_min": "C", "quantity_kg": 1000.0, "max_landed_price_per_kg": 27.00, "days_ahead": 2, "notes": "Low-grade tolerant processor"},
        {"id": 6, "buyer_id": 1, "crop_id": 5, "grade_min": "B", "quantity_kg": 300.0, "max_landed_price_per_kg": 55.00, "days_ahead": 2, "notes": "Small lots"},
        {"id": 7, "buyer_id": 3, "crop_id": 4, "grade_min": "B", "quantity_kg": 400.0, "max_landed_price_per_kg": 36.00, "days_ahead": 1, "notes": "Freshness sensitivity"},
        {"id": 8, "buyer_id": 5, "crop_id": 1, "grade_min": "A", "quantity_kg": 2500.0, "max_landed_price_per_kg": 22.00, "days_ahead": 2, "notes": "No match budget below Grade-A ask"},
    ]

    count = 0
    for item in requirements_data:
        needed_by = today + timedelta(days=item["days_ahead"])
        existing = db.query(Requirement).filter(Requirement.id == item["id"]).first()
        if existing:
            existing.buyer_id = item["buyer_id"]
            existing.crop_id = item["crop_id"]
            existing.grade_min = item["grade_min"]
            existing.quantity_kg = item["quantity_kg"]
            existing.quantity_fulfilled_kg = 0.0
            existing.max_landed_price_per_kg = item["max_landed_price_per_kg"]
            existing.needed_by = needed_by
            existing.status = "OPEN"
            existing.notes = item["notes"]
            existing.is_demo = True
        else:
            req = Requirement(
                id=item["id"],
                buyer_id=item["buyer_id"],
                crop_id=item["crop_id"],
                grade_min=item["grade_min"],
                quantity_kg=item["quantity_kg"],
                quantity_fulfilled_kg=0.0,
                max_landed_price_per_kg=item["max_landed_price_per_kg"],
                needed_by=needed_by,
                status="OPEN",
                notes=item["notes"],
                is_demo=True,
            )
            db.add(req)
        count += 1

    db.commit()
    return {"requirements": count}


def seed_demo_orders(db: Session) -> dict[str, int]:
    """Deterministically seed routing pool orders O1-O6 and historical orders H1-H4 per Data.md §12."""
    today = today_ist()
    vehicle_types = get_vehicle_types(db)
    operator = db.query(User).filter(User.email == CANONICAL_PERSONAS["operator"]).first()
    operator_id = operator.id if operator else 1

    # Remove any test-created orders beyond canonical seed (id > 10)
    extra_orders = db.query(Order).filter(Order.id > 10).all()
    for extra_order in extra_orders:
        db.query(OrderEvent).filter(OrderEvent.order_id == extra_order.id).delete()
        db.delete(extra_order)
    db.flush()

    # Reset all listings to initial quantity before applying canonical seed reservations
    all_listings = db.query(Listing).all()
    for l_item in all_listings:
        l_item.quantity_available_kg = l_item.quantity_kg
        l_item.status = "ACTIVE"
    db.flush()

    # O1-O6: routing pool (status CONFIRMED, no shipment, origin MARKETPLACE)
    # H1-H4: historical orders (status DELIVERED, delivered 2-10 days ago, no shipment, origin MARKETPLACE)
    orders_data = [
        # O1: L1 Tomato, P2 -> B5, 600 kg @ 22.50
        {"id": 1, "listing_id": 1, "buyer_id": 5, "crop_id": 1, "producer_id": 2, "quantity_kg": 600.0, "price_per_kg": 22.50, "days_ahead": 2, "status": "CONFIRMED"},
        # O2: L5 Onion, P4 -> B4, 1200 kg @ 22.50
        {"id": 2, "listing_id": 5, "buyer_id": 4, "crop_id": 2, "producer_id": 4, "quantity_kg": 1200.0, "price_per_kg": 22.50, "days_ahead": 3, "status": "CONFIRMED"},
        # O3: L8 Potato, P4 -> B3, 900 kg @ 18.00
        {"id": 3, "listing_id": 8, "buyer_id": 3, "crop_id": 3, "producer_id": 4, "quantity_kg": 900.0, "price_per_kg": 18.00, "days_ahead": 2, "status": "CONFIRMED"},
        # O4: L2 Tomato, P6 -> B3, 500 kg @ 24.00
        {"id": 4, "listing_id": 2, "buyer_id": 3, "crop_id": 1, "producer_id": 6, "quantity_kg": 500.0, "price_per_kg": 24.00, "days_ahead": 2, "status": "CONFIRMED"},
        # O5: L10 Cauliflower, P1 -> B2, 400 kg @ 28.50
        {"id": 5, "listing_id": 10, "buyer_id": 2, "crop_id": 4, "producer_id": 1, "quantity_kg": 400.0, "price_per_kg": 28.50, "days_ahead": 2, "status": "CONFIRMED"},
        # O6: L12 Green Chilli, P5 -> B1, 150 kg @ 46.00
        {"id": 6, "listing_id": 12, "buyer_id": 1, "crop_id": 5, "producer_id": 5, "quantity_kg": 150.0, "price_per_kg": 46.00, "days_ahead": 2, "status": "CONFIRMED"},
        # H1: L6 Onion, 1000 kg @ 21.50 -> B4 (P2)
        {"id": 7, "listing_id": 6, "buyer_id": 4, "crop_id": 2, "producer_id": 2, "quantity_kg": 1000.0, "price_per_kg": 21.50, "days_ago": 8, "status": "DELIVERED"},
        # H2: L9 Potato, 800 kg @ 17.00 -> B5 (P2)
        {"id": 8, "listing_id": 9, "buyer_id": 5, "crop_id": 3, "producer_id": 2, "quantity_kg": 800.0, "price_per_kg": 17.00, "days_ago": 5, "status": "DELIVERED"},
        # H3: L7 Onion, 600 kg @ 21.00 -> B2 (P3)
        {"id": 9, "listing_id": 7, "buyer_id": 2, "crop_id": 2, "producer_id": 3, "quantity_kg": 600.0, "price_per_kg": 21.00, "days_ago": 3, "status": "DELIVERED"},
        # H4: L11 Cauliflower, 200 kg @ 27.00 -> B1 (P6)
        {"id": 10, "listing_id": 11, "buyer_id": 1, "crop_id": 4, "producer_id": 6, "quantity_kg": 200.0, "price_per_kg": 27.00, "days_ago": 2, "status": "DELIVERED"},
    ]

    count = 0
    for item in orders_data:
        listing = db.query(Listing).filter(Listing.id == item["listing_id"]).first()
        buyer = db.query(BuyerProfile).filter(BuyerProfile.id == item["buyer_id"]).first()
        if not listing or not buyer:
            continue

        # Adjust listing quantity_available_kg per real reservation invariant
        listing.quantity_available_kg = max(0.0, float(listing.quantity_available_kg) - item["quantity_kg"])
        if listing.quantity_available_kg <= 0:
            listing.status = "SOLD_OUT"

        dist_km = road_distance_km(
            (listing.producer.lat, listing.producer.lng),
            (buyer.lat, buyer.lng),
            circuity=1.35,
        )
        trip_est = estimate_dedicated_trip(dist_km, item["quantity_kg"], vehicle_types)
        transport_cost_estimate_per_kg = trip_est["cost_per_kg"]
        platform_fee_per_kg = round(item["price_per_kg"] * 0.02, 2)

        if "days_ahead" in item:
            delivery_date = today + timedelta(days=item["days_ahead"])
        else:
            delivery_date = today - timedelta(days=item["days_ago"])

        existing = db.query(Order).filter(Order.id == item["id"]).first()
        if existing:
            existing.listing_id = item["listing_id"]
            existing.buyer_id = item["buyer_id"]
            existing.producer_id = item["producer_id"]
            existing.crop_id = item["crop_id"]
            existing.quantity_kg = item["quantity_kg"]
            existing.agreed_price_per_kg = item["price_per_kg"]
            existing.transport_cost_estimate_per_kg = transport_cost_estimate_per_kg
            existing.platform_fee_per_kg = platform_fee_per_kg
            existing.delivery_date = delivery_date
            existing.status = item["status"]
            existing.origin = "MARKETPLACE"
            existing.is_demo = True
            order = existing
        else:
            order = Order(
                id=item["id"],
                listing_id=item["listing_id"],
                requirement_id=None,
                buyer_id=item["buyer_id"],
                producer_id=item["producer_id"],
                crop_id=item["crop_id"],
                quantity_kg=item["quantity_kg"],
                agreed_price_per_kg=item["price_per_kg"],
                transport_cost_estimate_per_kg=transport_cost_estimate_per_kg,
                platform_fee_per_kg=platform_fee_per_kg,
                delivery_date=delivery_date,
                status=item["status"],
                origin="MARKETPLACE",
                shipment_id=None,
                allocated_transport_cost_total=None,
                is_demo=True,
            )
            db.add(order)
            db.flush()

        # Seed events for audit timeline
        existing_events = db.query(OrderEvent).filter(OrderEvent.order_id == order.id).count()
        if existing_events == 0:
            e_placed = OrderEvent(
                order_id=order.id,
                from_status=None,
                to_status="PLACED",
                actor_user_id=operator_id,
                actor_role="BUYER",
                note="Marketplace direct purchase (Seeded)",
            )
            db.add(e_placed)

            if item["status"] in ["CONFIRMED", "DELIVERED"]:
                e_conf = OrderEvent(
                    order_id=order.id,
                    from_status="PLACED",
                    to_status="CONFIRMED",
                    actor_user_id=operator_id,
                    actor_role="PRODUCER",
                    note="Order confirmed by producer (Seeded)",
                )
                db.add(e_conf)

            if item["status"] == "DELIVERED":
                e_deliv = OrderEvent(
                    order_id=order.id,
                    from_status="CONFIRMED",
                    to_status="DELIVERED",
                    actor_user_id=operator_id,
                    actor_role="ADMIN",
                    note="Historical delivery completed (Seeded)",
                )
                db.add(e_deliv)

        count += 1

    db.commit()
    return {"orders": count}


def seed_all(db: Session) -> dict[str, Any]:
    """Execute complete deterministic seed pipeline in proper relational order."""
    r1 = seed_reference_and_users(db)
    r2 = seed_synthetic_demand_and_prices(db)
    r3 = seed_demo_listings(db)
    r4 = seed_demo_requirements(db)
    r5 = seed_demo_orders(db)
    return {**r1, **r2, **r3, **r4, **r5}


if __name__ == "__main__":
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        results = seed_all(session)
        print("Database seeded successfully:", results)
    finally:
        session.close()


