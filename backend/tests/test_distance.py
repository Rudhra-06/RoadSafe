import pytest
from app.utils.distance import haversine_distance

def test_haversine_distance_calculation():
    # Coordinates: NYC to Philadelphia (approx 130 km)
    nyc_lat, nyc_lon = 40.7128, -74.0060
    philly_lat, philly_lon = 39.9526, -75.1652

    dist = haversine_distance(nyc_lat, nyc_lon, philly_lat, philly_lon)
    assert 125.0 <= dist <= 135.0

    # Same coordinates should return 0.0
    zero_dist = haversine_distance(nyc_lat, nyc_lon, nyc_lat, nyc_lon)
    assert zero_dist == 0.0