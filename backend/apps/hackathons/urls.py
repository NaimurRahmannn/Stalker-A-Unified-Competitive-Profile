from django.urls import path

from apps.hackathons.views import HackathonOverviewView

urlpatterns = [
    path(
        "overview/",
        HackathonOverviewView.as_view(),
        name="hackathon-overview",
    ),
]
