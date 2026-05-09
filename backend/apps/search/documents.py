from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from apps.incidents.models import Incident


@registry.register_document
class IncidentDocument(Document):
    location = fields.GeoPointField()
    category_display = fields.KeywordField(attr="get_category_display")
    source_display = fields.KeywordField(attr="get_source_display")

    # Filtered with term queries — must be exact-match (keyword), not analyzed text
    category = fields.KeywordField()
    source = fields.KeywordField()
    status = fields.KeywordField()
    borough = fields.KeywordField()

    class Index:
        name = "incidents"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    class Django:
        model = Incident
        fields = [
            "title",
            "description",
            "neighborhood",
            "address",
            "timestamp",
            "external_id",
        ]

    def prepare_location(self, instance):
        if instance.location:
            return {"lat": instance.location.y, "lon": instance.location.x}
        return None
