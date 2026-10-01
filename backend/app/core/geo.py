import math

EARTH_RADIUS_KM = 6371.0
DEFAULT_ROAD_CIRCUITY_FACTOR = 1.35


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth (in km)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def road_distance_km(
    origin: tuple[float, float],
    destination: tuple[float, float],
    circuity: float = DEFAULT_ROAD_CIRCUITY_FACTOR,
) -> float:
    """Calculate estimated road distance by scaling haversine distance with circuity factor."""
    lat1, lon1 = origin
    lat2, lon2 = destination
    h_dist = haversine_km(lat1, lon1, lat2, lon2)
    return round(h_dist * circuity, 2)
