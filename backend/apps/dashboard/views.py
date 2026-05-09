from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.serializers import DashboardMeSerializer
from apps.dashboard.services import build_dashboard_payload


class DashboardMeAPIView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		payload = build_dashboard_payload(request.user)
		serializer = DashboardMeSerializer(payload)
		return Response(serializer.data)
