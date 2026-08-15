from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.connectors.views import CodeforcesAnalyticsView, PlatformAccountViewSet


router = DefaultRouter()
router.register("platform-accounts", PlatformAccountViewSet, basename="platform-account")

urlpatterns = [
    path(
        "competitive-programming/codeforces/",
        CodeforcesAnalyticsView.as_view(),
        name="codeforces-analytics",
    ),
    *router.urls,
]
