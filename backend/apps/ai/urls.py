from django.urls import path
from .views import ChatView, AgentView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="ai-chat"),
    path("agent/", AgentView.as_view(), name="ai-agent"),
]
