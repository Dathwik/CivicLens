from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Incident
from .serializers import IncidentSerializer, IncidentGeoSerializer


class IncidentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Incident.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["category", "source", "status", "borough"]
    ordering_fields = ["timestamp", "created_at"]

    def get_serializer_class(self):
        if self.request.query_params.get("format") == "geojson":
            return IncidentGeoSerializer
        return IncidentSerializer
