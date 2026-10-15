from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connectors.competitive import build_competitive_programming_overview
from apps.connectors.models import PlatformAccount
from apps.dashboard.serializers import (
    DashboardPlatformSerializer,
    DashboardUserSerializer,
)


class DashboardMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        platforms = (
            PlatformAccount.objects.filter(user=request.user)
            .select_related("codeforces_stats", "atcoder_stats", "leetcode_stats", "ctf_team_profile", "ctftime_sync_state")
            .prefetch_related("ctf_team_profile__yearly_rankings")
            .order_by("platform")
        )

        return Response(
            {
                "user": DashboardUserSerializer(request.user).data,
                "platforms": DashboardPlatformSerializer(platforms, many=True).data,
                "competitive_programming": build_competitive_programming_overview(
                    request.user,
                    include_activity=False,
                ),
            }
        )


DashboardMeAPIView = DashboardMeView
