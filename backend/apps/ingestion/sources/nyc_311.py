import logging
from django.conf import settings
from django.contrib.gis.geos import Point
from sodapy import Socrata
from apps.incidents.models import Incident
from apps.search.documents import IncidentDocument

logger = logging.getLogger(__name__)

DOMAIN = "data.cityofnewyork.us"
DATASET_ID = "erm2-nwe9"  # 311 Service Requests

CATEGORY_MAP = {
    "Noise": Incident.Category.NOISE,
    "Noise - Residential": Incident.Category.NOISE,
    "Noise - Commercial": Incident.Category.NOISE,
    "Noise - Street/Sidewalk": Incident.Category.NOISE,
    "Noise - Vehicle": Incident.Category.NOISE,
    "Illegal Parking": Incident.Category.INFRASTRUCTURE,
    "HEAT/HOT WATER": Incident.Category.INFRASTRUCTURE,
    "Blocked Driveway": Incident.Category.INFRASTRUCTURE,
    "Street Light Condition": Incident.Category.INFRASTRUCTURE,
    "UNSANITARY CONDITION": Incident.Category.SANITATION,
    "Sanitation Condition": Incident.Category.SANITATION,
}


def ingest(limit: int = 500) -> int:
    token = settings.NYC_OPEN_DATA_APP_TOKEN or None
    client = Socrata(DOMAIN, token, timeout=30)

    records = client.get(
        DATASET_ID,
        limit=limit,
        order="created_date DESC",
        select="unique_key,complaint_type,descriptor,borough,incident_address,latitude,longitude,created_date,status",
    )

    created = 0
    incidents = []
    for r in records:
        if not r.get("latitude") or not r.get("longitude"):
            continue

        cat_raw = r.get("complaint_type", "")
        category = CATEGORY_MAP.get(cat_raw, Incident.Category.OTHER)
        external_id = f"nyc_311_{r['unique_key']}"

        incident = Incident(
            title=r.get("complaint_type", "311 Complaint"),
            description=r.get("descriptor", ""),
            category=category,
            source=Incident.Source.NYC_311,
            status=Incident.Status.OPEN if r.get("status") == "Open" else Incident.Status.CLOSED,
            borough=r.get("borough", "").title(),
            address=r.get("incident_address", ""),
            location=Point(float(r["longitude"]), float(r["latitude"])),
            timestamp=r.get("created_date"),
            external_id=external_id,
            raw_data=r,
        )
        incidents.append(incident)

    # Bulk upsert — skip duplicates via ignore_conflicts
    result = Incident.objects.bulk_create(incidents, ignore_conflicts=True, batch_size=200)
    created = len(result)
    # bulk_create skips signals; re-index touched rows into ES manually
    qs = Incident.objects.filter(external_id__in=[i.external_id for i in incidents])
    IncidentDocument().update(qs)
    logger.info("NYC 311: ingested %d new incidents (of %d fetched)", created, len(records))
    return created
