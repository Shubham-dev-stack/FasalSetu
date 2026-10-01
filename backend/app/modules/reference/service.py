from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Crop, DemandHub
from app.schemas.reference import CropOut, HubOut, ReferenceResponse

settings = get_settings()


def get_reference_data(db: Session) -> ReferenceResponse:
    crops = db.query(Crop).order_by(Crop.id).all()
    hubs = db.query(DemandHub).order_by(DemandHub.id).all()

    enums = {
        "grades": ["A", "B", "C"],
        "listing_status": ["ACTIVE", "SOLD_OUT", "EXPIRED", "WITHDRAWN"],
        "requirement_status": [
            "OPEN",
            "PARTIALLY_FULFILLED",
            "FULFILLED",
            "CANCELLED",
            "EXPIRED",
        ],
        "order_status": [
            "PLACED",
            "CONFIRMED",
            "REJECTED",
            "CANCELLED",
            "IN_TRANSIT",
            "DELIVERED",
        ],
        "producer_type": ["FARMER", "FPO"],
        "buyer_type": [
            "RETAILER",
            "RESTAURANT",
            "PROCESSOR",
            "INSTITUTION",
            "CONSUMER_GROUP",
        ],
        "vehicle_type": ["MINI_TRUCK", "PICKUP", "MEDIUM_TRUCK"],
    }

    public_config = {
        "platform_fee_pct": 2.0,
        "max_match_distance_km": 300.0,
        "forecast_horizon_days": 7,
        "demo_mode": settings.DEMO_MODE,
    }

    return ReferenceResponse(
        crops=[CropOut.model_validate(c) for c in crops],
        hubs=[HubOut.model_validate(h) for h in hubs],
        enums=enums,
        public_config=public_config,
    )
