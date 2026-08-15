from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.connectors.views import (
    AtCoderAnalyticsView,
    CodeforcesAnalyticsView,
    CompetitiveProgrammingOverviewView,
    PlatformAccountViewSet,
)

router = DefaultRouter()
router.register(
    "platform-accounts",
    PlatformAccountViewSet,
    basename="platform-account",
)

urlpatterns = [
    path(
        "competitive-programming/overview/",
        CompetitiveProgrammingOverviewView.as_view(),
        name="competitive-programming-overview",
    ),
    path(
        "competitive-programming/codeforces/",
        CodeforcesAnalyticsView.as_view(),
        name="codeforces-analytics",
    ),
    path(
        "competitive-programming/atcoder/",
        AtCoderAnalyticsView.as_view(),
        name="atcoder-analytics",
    ),
    *router.urls,
]
