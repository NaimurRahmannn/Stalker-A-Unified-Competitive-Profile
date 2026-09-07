from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.connectors.views import (
    AtCoderAnalyticsView,
    CodeforcesAnalyticsView,
    CompetitiveProgrammingOverviewView,
    LeetCodeAnalyticsView,
    PlatformAccountViewSet,
)
from apps.connectors.views_graphql import LeetCodeGraphQLProxyView

router = DefaultRouter()
router.register(
    "platform-accounts",
    PlatformAccountViewSet,
    basename="platform-account",
)

urlpatterns = [
    path(
        "connectors/leetcode/graphql/",
        LeetCodeGraphQLProxyView.as_view(),
        name="leetcode-graphql-proxy",
    ),
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
    path(
        "competitive-programming/leetcode/",
        LeetCodeAnalyticsView.as_view(),
        name="leetcode-analytics",
    ),
    *router.urls,
]
