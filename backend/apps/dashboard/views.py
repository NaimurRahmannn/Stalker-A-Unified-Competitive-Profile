from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
            .select_related("codeforces_stats")
            .order_by("platform")
        )

        return Response(
            {
                "user": DashboardUserSerializer(request.user).data,
                "platforms": DashboardPlatformSerializer(platforms, many=True).data,
            }
        )


DashboardMeAPIView = DashboardMeView
