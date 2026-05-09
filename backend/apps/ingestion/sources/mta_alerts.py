import logging
import hashlib
import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from apps.incidents.models import Incident
from apps.search.documents import IncidentDocument

logger = logging.getLogger(__name__)

MTA_RSS_URL = "https://api.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts"

# NYC subway center coordinates for MTA alerts (no per-alert location)
NYC_CENTER = (40.7128, -74.0060)


def ingest() -> int:
    try:
        resp = requests.get(MTA_RSS_URL, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("MTA fetch failed: %s", e)
        return 0

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        logger.error("MTA XML parse error: %s", e)
        return 0

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)

    incidents = []
    for entry in entries:
        title = entry.findtext("atom:title", default="MTA Alert", namespaces=ns)
        summary = entry.findtext("atom:summary", default="", namespaces=ns)
        updated = entry.findtext("atom:updated", namespaces=ns)
        link = entry.findtext("atom:id", default="", namespaces=ns)

        external_id = f"mta_{hashlib.md5(link.encode()).hexdigest()[:16]}"

        incidents.append(Incident(
            title=title[:500],
            description=summary[:2000],
            category=Incident.Category.TRANSIT,
            source=Incident.Source.MTA,
            status=Incident.Status.OPEN,
            borough="",
            timestamp=updated or timezone.now(),
            external_id=external_id,
            raw_data={"title": title, "summary": summary, "link": link},
        ))

    result = Incident.objects.bulk_create(incidents, ignore_conflicts=True, batch_size=100)
    created = len(result)
    qs = Incident.objects.filter(external_id__in=[i.external_id for i in incidents])
    IncidentDocument().update(qs)
    logger.info("MTA: ingested %d new alerts", created)
    return created
