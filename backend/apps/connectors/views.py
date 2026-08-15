from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connectors.base.exceptions import (
    ExternalServiceError,
    InvalidExternalAccountError,
    ProviderRateLimitError,
    UnsupportedSourceError,
)
from apps.connectors.models import CodeforcesStats, PlatformAccount, PlatformStatsSnapshot
from apps.connectors.serializers import (
    CodeforcesAnalyticsAccountSerializer,
    CodeforcesStatsSerializer,
    PlatformAccountSerializer,
    PlatformStatsSnapshotSerializer,
    serialize_codeforces_rating_history,
    serialize_codeforces_recent_activity,
    serialize_atcoder_submission_overview,
)
from apps.connectors.services import (
    get_connector,
    get_sync_cooldown_seconds,
)
from apps.connectors.providers.atcoder.submission_service import (
    AtCoderSubmissionIngestionService,
)


class PlatformAccountViewSet(viewsets.ModelViewSet):
    serializer_class = PlatformAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return (
            PlatformAccount.objects.filter(user=self.request.user)
            .select_related("codeforces_stats", "atcoder_stats")
            .prefetch_related("rating_events")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="sync")
    def sync(self, request, pk=None):
        platform_account = self.get_object()

        try:
            connector = get_connector(platform_account.platform)
        except UnsupportedSourceError:
            return Response(
                {"detail": "Sync is not supported for this platform yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not connector.is_enabled:
            return Response(
                {
                    "detail": (
                        f"{connector.display_name} synchronization is currently disabled."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        cooldown_seconds = get_sync_cooldown_seconds(platform_account)
        if cooldown_seconds > 0:
            return Response(
                {
                    "detail": "Please wait before syncing this account again.",
                    "retry_after_seconds": cooldown_seconds,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if connector.cooldown_uses_attempts:
            attempted_at = timezone.now()
            PlatformAccount.objects.filter(pk=platform_account.pk).update(
                last_sync_attempted_at=attempted_at
            )
            platform_account.last_sync_attempted_at = attempted_at

        try:
            platform_account = connector.sync(platform_account)
        except InvalidExternalAccountError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ProviderRateLimitError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except ExternalServiceError as exc:
            return Response(
                {
                    "detail": str(exc)
                    or "The provider is temporarily unavailable. Please try again later."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = self.get_serializer(platform_account)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="atcoder-submissions")
    def atcoder_submissions(self, request, pk=None):
        platform_account = self.get_object()
        if platform_account.platform != PlatformAccount.Platform.ATCODER:
            return Response(
                {"detail": "Submission data is only available for AtCoder accounts."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(serialize_atcoder_submission_overview(platform_account))

    @action(detail=True, methods=["post"], url_path="sync-submissions")
    def sync_submissions(self, request, pk=None):
        platform_account = self.get_object()
        if platform_account.platform != PlatformAccount.Platform.ATCODER:
            return Response(
                {"detail": "Submission synchronization is only supported for AtCoder."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = AtCoderSubmissionIngestionService().sync(platform_account)
        except ProviderRateLimitError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except ExternalServiceError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        payload = serialize_atcoder_submission_overview(platform_account)
        payload["sync"] = {
            "pages_fetched": result.pages_fetched,
            "indexed_submission_count": result.indexed_submission_count,
            "backfill_complete": result.backfill_complete,
        }
        return Response(payload, status=status.HTTP_200_OK)


class CodeforcesAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account = (
            PlatformAccount.objects.filter(
                user=request.user,
                platform=PlatformAccount.Platform.CODEFORCES,
            )
            .select_related("codeforces_stats")
            .first()
        )

        if account is None:
            return Response(
                {
                    "platform": PlatformAccount.Platform.CODEFORCES,
                    "account": None,
                    "stats": None,
                    "rating_history": [],
                    "recent_activity": [],
                    "snapshots": [],
                }
            )

        try:
            stats = account.codeforces_stats
        except CodeforcesStats.DoesNotExist:
            stats = None

        snapshots = list(
            PlatformStatsSnapshot.objects.filter(platform_account=account)[:180]
        )
        snapshots.reverse()

        return Response(
            {
                "platform": PlatformAccount.Platform.CODEFORCES,
                "account": CodeforcesAnalyticsAccountSerializer(account).data,
                "stats": CodeforcesStatsSerializer(stats).data if stats else None,
                "rating_history": (
                    serialize_codeforces_rating_history(stats) if stats else []
                ),
                "recent_activity": (
                    serialize_codeforces_recent_activity(stats) if stats else []
                ),
                "snapshots": PlatformStatsSnapshotSerializer(
                    snapshots,
                    many=True,
                ).data,
            }
        )
