from datetime import timedelta
from django.utils import timezone
from elasticsearch_dsl import Q


def build_incident_query(params: dict) -> Q:
    """
    Compose an Elasticsearch bool query from search params.
    params keys: q, category, borough, days, lat, lng, radius_km
    """
    must = []
    filters = []

    if q := params.get("q"):
        must.append(Q("multi_match", query=q, fields=["title^2", "description", "borough", "address"]))

    if category := params.get("category"):
        filters.append(Q("term", category=category))

    if borough := params.get("borough"):
        filters.append(Q("term", borough=borough.title()))

    if days := params.get("days"):
        since = timezone.now() - timedelta(days=int(days))
        filters.append(Q("range", timestamp={"gte": since.isoformat()}))

    if status := params.get("status"):
        filters.append(Q("term", status=status))

    # Geo distance filter
    lat = params.get("lat")
    lng = params.get("lng")
    radius_km = params.get("radius_km", "5km")
    if lat and lng:
        filters.append(Q("geo_distance", distance=f"{radius_km}km", location={"lat": float(lat), "lon": float(lng)}))

    if must or filters:
        return Q("bool", must=must or [Q("match_all")], filter=filters)
    return Q("match_all")
