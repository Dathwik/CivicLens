"""
Tool execution layer — maps Claude tool_use blocks to real backend calls.
"""
import logging
from django.utils import timezone
from datetime import timedelta
from apps.incidents.models import Incident
from apps.search.documents import IncidentDocument
from apps.search.utils import build_incident_query
from .guardrails import sanitize_tool_input

logger = logging.getLogger(__name__)

BOROUGH_COORDS = {
    "Manhattan": (40.7831, -73.9712),
    "Brooklyn": (40.6782, -73.9442),
    "Queens": (40.7282, -73.7949),
    "The Bronx": (40.8448, -73.8648),
    "Staten Island": (40.5795, -74.1502),
}


def execute_tool(tool_name: str, tool_input: dict) -> dict:
    tool_input = sanitize_tool_input(tool_input)

    if tool_name == "search_incidents":
        return _search_incidents(tool_input)
    elif tool_name == "aggregate_stats":
        return _aggregate_stats(tool_input)
    elif tool_name == "filter_by_area":
        return _filter_by_area(tool_input)
    elif tool_name == "set_alert":
        return _set_alert(tool_input)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def _search_incidents(params: dict) -> dict:
    query_params = {
        "q": params.get("query"),
        "category": params.get("category"),
        "borough": params.get("borough"),
        "days": params.get("days", 30),
        "lat": params.get("lat"),
        "lng": params.get("lng"),
        "radius_km": params.get("radius_km", 5),
    }
    query_params = {k: v for k, v in query_params.items() if v is not None}

    es_query = build_incident_query(query_params)
    limit = min(params.get("limit", 50), 100)
    search = IncidentDocument.search().query(es_query)[:limit].sort("-timestamp")
    response = search.execute()

    results = []
    for hit in response:
        loc = hit.to_dict().get("location")
        results.append({
            "id": hit.meta.id,
            "title": hit.title,
            "category": hit.category,
            "borough": getattr(hit, "borough", ""),
            "timestamp": str(hit.timestamp),
            "lat": loc["lat"] if loc else None,
            "lng": loc["lon"] if loc else None,
        })

    return {"total": response.hits.total.value, "results": results}


def _aggregate_stats(params: dict) -> dict:
    group_by = params["group_by"]
    days = params.get("days", 7)
    since = timezone.now() - timedelta(days=days)

    qs = Incident.objects.filter(timestamp__gte=since)
    if params.get("category"):
        qs = qs.filter(category=params["category"])
    if params.get("borough"):
        qs = qs.filter(borough__iexact=params["borough"])

    from django.db.models import Count
    if group_by == "day":
        from django.db.models.functions import TruncDay
        rows = qs.annotate(day=TruncDay("timestamp")).values("day").annotate(count=Count("id")).order_by("day")
        return {"group_by": group_by, "data": [{"day": str(r["day"].date()), "count": r["count"]} for r in rows]}

    field_map = {"category": "category", "borough": "borough", "source": "source", "status": "status"}
    field = field_map.get(group_by, "category")
    rows = qs.values(field).annotate(count=Count("id")).order_by("-count")
    return {"group_by": group_by, "data": list(rows)}


def _filter_by_area(params: dict) -> dict:
    area = params["area_name"]
    days = params.get("days", 30)
    since = timezone.now() - timedelta(days=days)

    qs = Incident.objects.filter(timestamp__gte=since)
    if params.get("category"):
        qs = qs.filter(category=params["category"])

    # Borough match
    for borough, coords in BOROUGH_COORDS.items():
        if borough.lower() in area.lower():
            qs = qs.filter(borough__iexact=borough)
            results = list(qs[:50].values("id", "title", "category", "borough", "timestamp"))
            return {"area": area, "total": len(results), "results": results}

    # Fallback: address text match
    qs = qs.filter(address__icontains=area) | qs.filter(neighborhood__icontains=area)
    results = list(qs[:50].values("id", "title", "category", "borough", "timestamp"))
    return {"area": area, "total": len(results), "results": results}


def _set_alert(params: dict) -> dict:
    from apps.alerts.models import AlertSubscription
    sub = AlertSubscription.objects.create(
        user_query=params.get("query", ""),
        filters={
            "category": params.get("category"),
            "borough": params.get("borough"),
            "lat": params.get("lat"),
            "lng": params.get("lng"),
            "radius_km": params.get("radius_km", 2),
        },
    )
    return {"alert_id": sub.id, "message": f"Alert set for '{params.get('query')}'. You'll receive WebSocket notifications for new matching incidents."}
