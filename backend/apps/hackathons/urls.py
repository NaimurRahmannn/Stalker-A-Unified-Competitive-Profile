from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.hackathons.views import (
    AchievementViewSet, EventViewSet, HackathonOverviewView, ManualEntryView,
    ParticipationViewSet, ProjectViewSet, SubmissionViewSet,
)

router = DefaultRouter()
router.register("events", EventViewSet, basename="hackathon-event")
router.register("projects", ProjectViewSet, basename="hackathon-project")
router.register("participations", ParticipationViewSet, basename="hackathon-participation")
router.register("submissions", SubmissionViewSet, basename="hackathon-submission")
router.register("achievements", AchievementViewSet, basename="hackathon-achievement")

urlpatterns = [
    path(
        "overview/",
        HackathonOverviewView.as_view(),
        name="hackathon-overview",
    ),
    path("entries/", ManualEntryView.as_view(), name="hackathon-entry"),
]
urlpatterns += router.urls
