import logging
from django.conf import settings
from django.contrib.gis.geos import Point
from sodapy import Socrata
from apps.incidents.models import Incident
from apps.search.documents import IncidentDocument

logger = logging.getLogger(__name__)

DOMAIN = "data.cityofnewyork.us"
DATASET_ID = "5uac-w243"  # NYPD Complaint Data (current year)


def ingest(limit: int = 300) -> int:
    token = settings.NYC_OPEN_DATA_APP_TOKEN or None
    client = Socrata(DOMAIN, token, timeout=30)

    records = client.get(
        DATASET_ID,
        limit=limit,
        order="cmplnt_fr_dt DESC",
        select="cmplnt_num,ofns_desc,boro_nm,latitude,longitude,cmplnt_fr_dt,crm_atpt_cptd_cd",
    )

    incidents = []
    for r in records:
        if not r.get("latitude") or not r.get("longitude"):
            continue

        external_id = f"nypd_{r['cmplnt_num']}"
        status = (
            Incident.Status.CLOSED
            if r.get("crm_atpt_cptd_cd") == "COMPLETED"
            else Incident.Status.OPEN
        )

        incidents.append(Incident(
            title=r.get("ofns_desc", "NYPD Complaint"),
            description="",
            category=Incident.Category.CRIME,
            source=Incident.Source.NYPD,
            status=status,
            borough=r.get("boro_nm", "").title(),
            location=Point(float(r["longitude"]), float(r["latitude"])),
            timestamp=r.get("cmplnt_fr_dt"),
            external_id=external_id,
            raw_data=r,
        ))

    result = Incident.objects.bulk_create(incidents, ignore_conflicts=True, batch_size=200)
    created = len(result)
    qs = Incident.objects.filter(external_id__in=[i.external_id for i in incidents])
    IncidentDocument().update(qs)
    logger.info("NYPD Crime: ingested %d new incidents", created)
    return created
