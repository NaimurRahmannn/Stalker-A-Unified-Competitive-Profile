from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.connectors.base.exceptions import (
    ExternalServiceError,
    InvalidExternalAccountError,
)
from apps.connectors.models import CodeforcesStats, PlatformAccount
from apps.connectors.serializers import PlatformAccountSerializer
from apps.connectors.services import get_connector


class PlatformAccountViewSet(viewsets.ModelViewSet):
    serializer_class = PlatformAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return PlatformAccount.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="sync")
    def sync(self, request, pk=None):
        platform_account = self.get_object()
        if platform_account.platform != PlatformAccount.Platform.CODEFORCES:
            return Response(
                {"detail": "Sync is currently only available for Codeforces."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        connector = get_connector(platform_account.platform)
        try:
            profile = connector.fetch_normalized_profile(platform_account.handle)
        except InvalidExternalAccountError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ExternalServiceError as exc:
            return Response(
                {"detail": str(exc) or "Codeforces sync failed."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        with transaction.atomic():
            platform_account.handle = profile["handle"]
            platform_account.profile_url = profile.get("profile_url", platform_account.profile_url)
            platform_account.is_verified = True
            platform_account.last_synced_at = timezone.now()
            platform_account.save(
                update_fields=[
                    "handle",
                    "profile_url",
                    "is_verified",
                    "last_synced_at",
                    "updated_at",
                ]
            )

            CodeforcesStats.objects.update_or_create(
                platform_account=platform_account,
                defaults={
                    "handle": profile["handle"],
                    "rating": profile["rating"],
                    "max_rating": profile["max_rating"],
                    "rank": profile["rank"],
                    "max_rank": profile["max_rank"],
                    "solved_count": profile["solved_count"],
                    "attempted_count": profile["attempted_count"],
                    "accepted_submission_count": profile["accepted_submission_count"],
                    "contest_count": profile["contest_count"],
                    "last_online_at": profile["last_online_at"],
                    "registered_at": profile["registered_at"],
                    "raw_user_info": profile["raw_user_info"],
                    "raw_rating_history": profile["raw_rating_history"],
                },
            )

        serializer = self.get_serializer(platform_account)
        return Response(serializer.data, status=status.HTTP_200_OK)
