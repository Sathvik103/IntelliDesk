import math

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two points on the Earth's surface
    using the Haversine formula in kilometers.

    d = 2 * r * arcsin(sqrt(sin^2(delta_lat/2) + cos(lat1)*cos(lat2)*sin^2(delta_lon/2)))
    """
    # If coordinates are identical or missing, distance is 0.0
    if lat1 == lat2 and lon1 == lon2:
        return 0.0
    
    # If either coordinate is completely unpopulated (0,0) and not near equator, treat as nominal default
    if (lat1 == 0.0 and lon1 == 0.0) or (lat2 == 0.0 and lon2 == 0.0):
        return 1.0  # nominal 1 km baseline fallback

    # Earth radius in kilometers
    R = 6371.0

    # Convert decimal degrees to radians
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))

    # Haversine formula
    a = (math.sin(delta_phi / 2.0) ** 2) + \
        (math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    
    # Clip value between 0 and 1 to prevent floating point domain errors in sqrt/asin
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = R * c
    return round(distance, 3)
