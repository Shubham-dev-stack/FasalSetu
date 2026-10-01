import argparse

from app.core.database import Base, SessionLocal, engine
from app.db.seed import (
    seed_demo_listings,
    seed_reference_and_users,
    seed_synthetic_demand_and_prices,
)


def setup_demo(retrain: bool = False, generate_data: bool = True):
    print("Setting up FasalSetu demo database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully (15 tables).")

    db = SessionLocal()
    try:
        counts = seed_reference_and_users(db)
        print("Seeding reference and user entities completed:")
        for k, v in counts.items():
            print(f"  - {k}: {v}")

        if generate_data:
            print("Generating synthetic demand panel and benchmark prices...")
            gen_counts = seed_synthetic_demand_and_prices(db)
            print("Synthetic data seeded:")
            for k, v in gen_counts.items():
                print(f"  - {k}: {v}")

        listing_counts = seed_demo_listings(db)
        print("Seeding demo listings L1-L14 completed:")
        for k, v in listing_counts.items():
            print(f"  - {k}: {v}")
    finally:
        db.close()


    if retrain:
        print("Model retraining flag passed (will be implemented in Phase 5).")

    print("Setup demo finished successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FasalSetu Demo Setup")
    parser.add_argument("--retrain", action="store_true", help="Retrain ML models")
    parser.add_argument(
        "--no-retrain", action="store_true", help="Skip ML model retraining"
    )
    args = parser.parse_args()
    setup_demo(retrain=args.retrain)
