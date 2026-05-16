from django.urls import path

from apps.dashboard.views import DashboardMeView


urlpatterns = [
    path("me/", DashboardMeView.as_view(), name="dashboard-me"),
]
