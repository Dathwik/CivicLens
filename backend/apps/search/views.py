from rest_framework.views import APIView
from rest_framework.response import Response
from .documents import IncidentDocument
from .utils import build_incident_query


class IncidentSearchView(APIView):
    def get(self, request):
        params = {
            "q": request.query_params.get("q"),
            "category": request.query_params.get("category"),
            "borough": request.query_params.get("borough"),
            "days": request.query_params.get("days"),
            "lat": request.query_params.get("lat"),
            "lng": request.query_params.get("lng"),
            "radius_km": request.query_params.get("radius_km", "5"),
            "status": request.query_params.get("status"),
        }

        query = build_incident_query({k: v for k, v in params.items() if v})
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        offset = (page - 1) * page_size

        search = IncidentDocument.search().query(query)[offset: offset + page_size]
        search = search.sort("-timestamp")
        response = search.execute()

        hits = []
        for hit in response:
            loc = hit.to_dict().get("location")
            hits.append({
                "id": hit.meta.id,
                "title": hit.title,
                "category": hit.category,
                "source": hit.source,
                "borough": getattr(hit, "borough", ""),
                "timestamp": str(hit.timestamp),
                "lat": loc["lat"] if loc else None,
                "lng": loc["lon"] if loc else None,
                "score": hit.meta.score,
            })

        return Response({
            "total": response.hits.total.value,
            "page": page,
            "results": hits,
            # GeoJSON FeatureCollection for Mapbox direct consumption
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [h["lng"], h["lat"]]} if h["lng"] else None,
                        "properties": {k: v for k, v in h.items() if k not in ("lat", "lng")},
                    }
                    for h in hits
                    if h["lat"]
                ],
            },
        })
