from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.dates import today_ist
from app.core.security import hash_password
from app.db.models import (
    BuyerProfile,
    Crop,
    DemandHub,
    Listing,
    ProducerProfile,
    User,
    Vehicle,
)

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

