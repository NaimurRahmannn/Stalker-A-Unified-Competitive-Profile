from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.connectors.competitive import build_competitive_programming_overview
from apps.connectors.models import PlatformAccount
from apps.profiles.serializers import (
    PublicProfilePlatformSerializer,
    PublicProfileUserSerializer,
)


class PublicProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username: str):
        user = get_object_or_404(User, username=username)
        platforms = (
            PlatformAccount.objects.filter(user=user)
            .select_related("codeforces_stats", "atcoder_stats", "leetcode_stats")
            .order_by("platform")
        )

        return Response(
            {
                "user": PublicProfileUserSerializer(user).data,
                "platforms": PublicProfilePlatformSerializer(
                    platforms,
                    many=True,
                ).data,
                "competitive_programming": build_competitive_programming_overview(
                    user,
                    include_activity=False,
                ),
            }
        )


PublicProfileAPIView = PublicProfileView
