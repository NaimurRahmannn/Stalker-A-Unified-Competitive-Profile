from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connectors.competitive import build_competitive_programming_overview
from apps.connectors.models import PlatformAccount
from apps.dashboard.serializers import (
    DashboardPlatformSerializer,
    DashboardUserSerializer,
)
from apps.datathons.overview import build_kaggle_overview
from apps.hackathons.overview import build_hackathon_overview


class DashboardMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        platforms = (
            PlatformAccount.objects.filter(user=request.user)
            .select_related("codeforces_stats", "atcoder_stats", "leetcode_stats", "ctf_team_profile", "ctftime_sync_state", "kaggle_profile_link__kaggle_profile")
            .prefetch_related("ctf_team_profile__yearly_rankings", "kaggle_manual_stats", "kaggle_profile_link__kaggle_profile__track_stats")
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
                "hackathons": build_hackathon_overview(request.user),
                "datathons": build_kaggle_overview(request.user),
            }
        )


DashboardMeAPIView = DashboardMeView
