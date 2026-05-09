from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/incidents/", include("apps.incidents.urls")),
    path("api/search/", include("apps.search.urls")),
    path("api/ai/", include("apps.ai.urls")),
    path("api/alerts/", include("apps.alerts.urls")),
]
