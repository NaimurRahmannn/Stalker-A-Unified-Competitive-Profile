from django.urls import path

from apps.dashboard.views import DashboardMeAPIView


urlpatterns = [
    path("me/", DashboardMeAPIView.as_view(), name="dashboard-me"),
]
