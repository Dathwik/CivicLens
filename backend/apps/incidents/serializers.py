from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Incident


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = [
            "id", "title", "description", "category", "source",
            "status", "borough", "neighborhood", "address",
            "timestamp", "external_id",
        ]


class IncidentGeoSerializer(GeoFeatureModelSerializer):
    """GeoJSON serializer for Mapbox consumption."""

    class Meta:
        model = Incident
        geo_field = "location"
        fields = [
            "id", "title", "category", "source", "status",
            "borough", "timestamp",
        ]
