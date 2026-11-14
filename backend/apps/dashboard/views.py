from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from apps.connectors.competitive import build_competitive_programming_overview
from apps.connectors.models import PlatformAccount
from apps.dashboard.clist_events import MAX_PAGE, get_clist_events
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


class DashboardEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = request.query_params.get("page", "1")
        if len(page) > len(str(MAX_PAGE)) or not page.isascii() or not page.isdecimal() or not 1 <= int(page) <= MAX_PAGE:
            return Response({"page": [f"Enter a page between 1 and {MAX_PAGE}."]}, status=status.HTTP_400_BAD_REQUEST)
        payload = get_clist_events(int(page))
        return Response(payload, status=200 if payload["status"] == "ready" else 503)
