from django.urls import path
from .views import IncidentSearchView

urlpatterns = [
    path("", IncidentSearchView.as_view(), name="incident-search"),
]
