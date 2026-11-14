from django.urls import path

from apps.dashboard.views import DashboardEventsView, DashboardMeView


urlpatterns = [
    path("me/", DashboardMeView.as_view(), name="dashboard-me"),
    path("events/", DashboardEventsView.as_view(), name="dashboard-events"),
]
