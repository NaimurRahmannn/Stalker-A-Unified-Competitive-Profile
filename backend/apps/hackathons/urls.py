from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.hackathons.views import (
    AchievementViewSet, EventViewSet, HackathonOverviewView, ManualEntryView,
    ParticipationViewSet, ProjectViewSet, SubmissionViewSet,
)
from apps.hackathons.devpost_views import DevpostImportDetailView, DevpostImportListView, DevpostImportPreviewView
from apps.hackathons.duplicate_reviews import DuplicateReviewDetailView, DuplicateReviewListView

router = DefaultRouter()
router.register("events", EventViewSet, basename="hackathon-event")
router.register("projects", ProjectViewSet, basename="hackathon-project")
router.register("participations", ParticipationViewSet, basename="hackathon-participation")
router.register("submissions", SubmissionViewSet, basename="hackathon-submission")
router.register("achievements", AchievementViewSet, basename="hackathon-achievement")

urlpatterns = [
    path("duplicate-reviews/", DuplicateReviewListView.as_view(), name="hackathon-duplicate-reviews"),
    path("duplicate-reviews/<int:pk>/", DuplicateReviewDetailView.as_view(), name="hackathon-duplicate-review-detail"),
    path("devpost/imports/preview/", DevpostImportPreviewView.as_view(), name="devpost-import-preview"),
    path("devpost/imports/", DevpostImportListView.as_view(), name="devpost-import-list"),
    path("devpost/imports/<int:pk>/", DevpostImportDetailView.as_view(), name="devpost-import-detail"),
    path(
        "overview/",
        HackathonOverviewView.as_view(),
        name="hackathon-overview",
    ),
    path("entries/", ManualEntryView.as_view(), name="hackathon-entry"),
]
urlpatterns += router.urls
