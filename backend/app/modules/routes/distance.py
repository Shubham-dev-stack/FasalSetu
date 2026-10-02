from app.core.geo import road_distance_km


def calculate_distance_matrix(
    locations: list[tuple[float, float]],
    circuity: float = 1.35,
) -> list[list[float]]:
    """Compute distance matrix in kilometers for a list of (lat, lng) points."""
    n = len(locations)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0.0
            else:
                matrix[i][j] = road_distance_km(locations[i], locations[j], circuity=circuity)
    return matrix


def calculate_duration_minutes(
    distance_km: float,
    speed_kmph: float = 30.0,
    service_minutes: float = 20.0,
    is_service_stop: bool = True,
) -> int:
    """Compute travel duration plus service time in minutes."""
    travel_time = (distance_km / speed_kmph) * 60.0
    total = travel_time + (service_minutes if is_service_stop else 0.0)
    return int(round(total))
