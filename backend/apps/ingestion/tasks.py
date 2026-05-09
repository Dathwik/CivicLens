from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_nyc_311(self, limit: int = 500):
    try:
        from .sources.nyc_311 import ingest
        created = ingest(limit=limit)
        logger.info("NYC 311 task done: %d created", created)
        return created
    except Exception as exc:
        logger.error("NYC 311 ingestion failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_nyc_crime(self, limit: int = 300):
    try:
        from .sources.nyc_crime import ingest
        created = ingest(limit=limit)
        logger.info("NYPD Crime task done: %d created", created)
        return created
    except Exception as exc:
        logger.error("NYPD Crime ingestion failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_mta_alerts(self):
    try:
        from .sources.mta_alerts import ingest
        created = ingest()
        logger.info("MTA Alerts task done: %d created", created)
        return created
    except Exception as exc:
        logger.error("MTA ingestion failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task
def run_all_ingestion():
    """Master task that kicks off all source ingestions."""
    ingest_nyc_311.delay()
    ingest_nyc_crime.delay()
    ingest_mta_alerts.delay()
