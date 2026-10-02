from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_optional_current_user
from app.core.errors import AppException
from app.core.geo import road_distance_km
from app.db.models import BuyerProfile, Listing, User, Vehicle
from app.modules.logistics.cost import (
    NoVehicleAvailableException,
    estimate_dedicated_trip,
)
from app.modules.logistics.fleet import get_vehicle_types
from app.schemas.logistics import (
    LogisticsEstimateRequest,
    LogisticsEstimateResponse,
    VehicleListResponse,
    VehicleOut,
    VehiclePlanLegOut,
)

router = APIRouter(prefix="/logistics", tags=["logistics"])


@router.post("/estimate", response_model=LogisticsEstimateResponse)
def estimate_logistics_cost(
    data: LogisticsEstimateRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    """Calculate dedicated-trip transport estimate per ML.md §11 & API.md §10."""
    listing = db.query(Listing).filter(Listing.id == data.listing_id).first()
    if not listing:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Listing with ID {data.listing_id} not found.",
        )

    # Resolve destination coordinates
    dest_lat: float | None = None
    dest_lng: float | None = None

    if data.dest_lat is not None and data.dest_lng is not None:
        dest_lat = data.dest_lat
        dest_lng = data.dest_lng
    elif data.buyer_id is not None:
        buyer = db.query(BuyerProfile).filter(BuyerProfile.id == data.buyer_id).first()
        if not buyer:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="NOT_FOUND",
                message=f"Buyer with ID {data.buyer_id} not found.",
            )
        dest_lat = buyer.lat
        dest_lng = buyer.lng
    elif current_user and current_user.buyer_profile:
        dest_lat = current_user.buyer_profile.lat
        dest_lng = current_user.buyer_profile.lng
    else:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Destination coordinates required: provide (dest_lat, dest_lng), buyer_id, or authenticate as a buyer.",
            details=[
                {
                    "field": "dest_lat",
                    "issue": "Missing destination coordinates or buyer profile.",
                }
            ],
        )

    producer_coords = (listing.producer.lat, listing.producer.lng)
    dest_coords = (dest_lat, dest_lng)
    dist_km = road_distance_km(producer_coords, dest_coords, circuity=1.35)

    vehicle_types = get_vehicle_types(db, require_active=True)
    try:
        trip_est = estimate_dedicated_trip(
            distance_km=dist_km,
            quantity_kg=data.quantity_kg,
            vehicle_types=vehicle_types,
            return_leg_factor=2.0,
            avg_speed_kmph=30.0,
            service_minutes_per_stop=20.0,
            distance_source="ESTIMATED_HAVERSINE",
        )
    except NoVehicleAvailableException:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="NO_VEHICLE_AVAILABLE",
            message="No active vehicles available in the logistics fleet.",
        ) from None
    except ValueError as e:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(e),
            details=[{"field": "quantity_kg", "issue": str(e)}],
        ) from e

    vehicle_plan_out = [
        VehiclePlanLegOut(
            vehicle_type=leg["vehicle_type"],
            capacity_kg=leg["capacity_kg"],
            load_kg=leg["load_kg"],
            trips=leg["trips"],
            trip_cost=leg["trip_cost"],
            total_cost=leg["total_cost"],
        )
        for leg in trip_est["vehicle_plan"]
    ]

    return LogisticsEstimateResponse(
        distance_km=trip_est["distance_km"],
        distance_source=trip_est["distance_source"],
        vehicle_plan=vehicle_plan_out,
        trips=trip_est["trips"],
        cost_total=trip_est["cost_total"],
        cost_per_kg=trip_est["cost_per_kg"],
        transit_hours=trip_est["transit_hours"],
        basis=trip_est["basis"],
    )


@router.get("/vehicles", response_model=VehicleListResponse)
def list_vehicles(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    """List fleet vehicles per API.md §10."""
    vehicles = db.query(Vehicle).order_by(Vehicle.id.asc()).all()
    items = [
        VehicleOut(
            id=v.id,
            name=v.name,
            vehicle_type=v.vehicle_type,
            capacity_kg=float(v.capacity_kg),
            cost_per_km=float(v.cost_per_km),
            fixed_cost_per_trip=float(v.fixed_cost_per_trip),
            avg_speed_kmph=float(v.avg_speed_kmph),
            depot_name=v.depot_name,
            depot_lat=float(v.depot_lat),
            depot_lng=float(v.depot_lng),
            is_available=v.is_available,
            is_demo=v.is_demo,
        )
        for v in vehicles
    ]
    return VehicleListResponse(items=items)
