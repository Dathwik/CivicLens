import logging
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

logger = get_task_logger = logging.getLogger(__name__)


@shared_task
def check_alerts():
    """
    Celery beat task: every 2 minutes, re-run active alert subscriptions.
    Push new matching incidents to all WebSocket clients via channel layer.
    """
    from apps.alerts.models import AlertSubscription
    from apps.search.utils import build_incident_query
    from apps.search.documents import IncidentDocument

    channel_layer = get_channel_layer()
    subs = AlertSubscription.objects.filter(is_active=True)

    for sub in subs:
        params = {
            "q": sub.user_query,
            **{k: v for k, v in sub.filters.items() if v},
        }
        params["since_timestamp"] = sub.last_checked.isoformat()

        query = build_incident_query(params)
        search = IncidentDocument.search().query(query).sort("-timestamp")[:10]
        response = search.execute()

        for hit in response:
            if str(hit.timestamp) > sub.last_checked.isoformat():
                payload = {
                    "type": "alert_message",
                    "data": {
                        "type": "new_incident",
                        "alert_query": sub.user_query,
                        "incident": {
                            "id": hit.meta.id,
                            "title": hit.title,
                            "category": hit.category,
                            "borough": getattr(hit, "borough", ""),
                            "timestamp": str(hit.timestamp),
                        },
                    },
                }
                async_to_sync(channel_layer.group_send)("alerts_global", payload)

        sub.last_checked = timezone.now()
        sub.save(update_fields=["last_checked"])


@shared_task
def push_test_alert():
    """Dev helper: push a test alert to all WebSocket clients."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "alerts_global",
        {
            "type": "alert_message",
            "data": {
                "type": "test",
                "message": "CivicLens alert system connected and working.",
            },
        },
    )
