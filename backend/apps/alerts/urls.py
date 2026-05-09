from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import AlertSubscription
from rest_framework import serializers


class AlertSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertSubscription
        fields = ["id", "user_query", "filters", "is_active", "created_at"]


class AlertListView(APIView):
    def get(self, request):
        subs = AlertSubscription.objects.filter(is_active=True)
        return Response(AlertSubscriptionSerializer(subs, many=True).data)

    def delete(self, request):
        alert_id = request.query_params.get("id")
        if alert_id:
            AlertSubscription.objects.filter(id=alert_id).update(is_active=False)
        return Response({"status": "deactivated"})


urlpatterns = [
    path("", AlertListView.as_view(), name="alerts"),
]
