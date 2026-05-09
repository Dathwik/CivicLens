from django.contrib.gis.db import models
from django.utils import timezone


class Incident(models.Model):
    class Category(models.TextChoices):
        NOISE = "noise", "Noise Complaint"
        CRIME = "crime", "Crime"
        TRANSIT = "transit", "Transit"
        SANITATION = "sanitation", "Sanitation"
        INFRASTRUCTURE = "infrastructure", "Infrastructure"
        EMERGENCY = "emergency", "Emergency"
        OTHER = "other", "Other"

    class Source(models.TextChoices):
        NYC_311 = "nyc_311", "NYC 311"
        NYPD = "nypd", "NYPD Crime Stats"
        MTA = "mta", "MTA Alerts"
        FEMA = "fema", "FEMA"
        CHICAGO = "chicago", "Chicago Data Portal"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=Category.choices, default=Category.OTHER)
    source = models.CharField(max_length=50, choices=Source.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    borough = models.CharField(max_length=100, blank=True)
    neighborhood = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=500, blank=True)
    location = models.PointField(null=True, blank=True, srid=4326)
    timestamp = models.DateTimeField(default=timezone.now)
    external_id = models.CharField(max_length=200, unique=True)
    raw_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["category", "timestamp"]),
            models.Index(fields=["source", "timestamp"]),
            models.Index(fields=["borough", "timestamp"]),
            models.Index(fields=["external_id"]),
        ]

    def __str__(self):
        return f"[{self.category}] {self.title[:80]}"
