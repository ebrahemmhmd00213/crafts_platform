import math
import heapq
import logging
from accounts.models import TechnicianProfile

logger = logging.getLogger(__name__)

WEIGHT_DISTANCE = 0.5
WEIGHT_RATING = 2.0
WEIGHT_RESPONSE = 0.05
NEUTRAL_RATING = 3.0      
MAX_RESPONSE_MINUTES = 120  


def haversine_km(lat1, lon1, lat2, lon2):
    """حساب المسافة بالكيلومتر بين نقطتين على سطح الأرض"""
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def find_nearby_technicians(order, max_km=15, limit=20):
    
    if order.latitude is None or order.longitude is None:
        logger.warning(f"Order {order.id} has no coordinates")
        return []

    techs = TechnicianProfile.objects.filter(
        status=TechnicianProfile.Status.APPROVED,
        service_type=order.service_type,
        user__latitude__isnull=False,
        user__longitude__isnull=False,   
    ).select_related('user')

    scored = []
    for t in techs:
        dist = haversine_km(order.latitude, order.longitude,
                            t.user.latitude, t.user.longitude)
        if dist > max_km:
            continue

        
        rating = t.avg_rating if t.avg_rating > 0 else NEUTRAL_RATING

        
        response = min(t.avg_response_minutes, MAX_RESPONSE_MINUTES)

        
        score = (
            dist * WEIGHT_DISTANCE
            - rating * WEIGHT_RATING
            + response * WEIGHT_RESPONSE
        )
        scored.append((score, t))

    
    best = heapq.nsmallest(limit, scored, key=lambda x: x[0])

    
    logger.info(f"Found {len(best)} technicians for order {order.id}")

    return [t for _, t in best]