from django.db import models
from django.utils import timezone


class AlertSubscription(models.Model):
    user_query = models.CharField(max_length=500)
    filters = models.JSONField(default=dict)
    last_checked = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert: {self.user_query[:60]}"
