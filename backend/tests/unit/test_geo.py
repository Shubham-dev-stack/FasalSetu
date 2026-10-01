import math

from app.core.geo import haversine_km, road_distance_km


def test_haversine_known_pair_sonipat_gurugram():
    # AC-LOG-01: Sonipat (28.99, 77.02) to Gurugram (28.47, 77.05)
    # Reference distance is ~58 km straight-line
    dist = haversine_km(28.99, 77.02, 28.47, 77.05)
    assert math.isclose(dist, 58.0, abs_tol=1.5)


def test_road_distance_scaling():
    # Road distance with 1.35 circuity
    straight_dist = haversine_km(28.99, 77.02, 28.47, 77.05)
    road_dist = road_distance_km((28.99, 77.02), (28.47, 77.05), circuity=1.35)
    assert math.isclose(road_dist, straight_dist * 1.35, abs_tol=0.05)
