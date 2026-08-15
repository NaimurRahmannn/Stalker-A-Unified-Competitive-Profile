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
from apps.connectors.competitive import build_competitive_programming_overview
from apps.connectors.models import (
    AtCoderStats,
    AtCoderSubmission,
    AtCoderSubmissionSyncState,
    AtCoderSyncState,
    CodeforcesStats,
    PlatformAccount,
    PlatformRatingEvent,
    PlatformStatsSnapshot,
)
from apps.connectors.providers.atcoder.analytics import (
    RECENT_ACTIVITY_LIMIT,
    SNAPSHOT_LIMIT,
    build_atcoder_sync_summary,
)
from apps.connectors.providers.atcoder.orchestrator import (
    AtCoderSyncOrchestrator,
    OverallSyncStatus,
    SourceSyncStatus,
    SyncErrorCode,
)
from apps.connectors.serializers import (
    AtCoderAnalyticsAccountSerializer,
    AtCoderAnalyticsActivitySerializer,
    AtCoderAnalyticsRatingEventSerializer,
    AtCoderAnalyticsSnapshotSerializer,
    AtCoderAnalyticsStatsSerializer,
    AtCoderAnalyticsSyncSerializer,
    CodeforcesAnalyticsAccountSerializer,
    CodeforcesStatsSerializer,
    PlatformAccountSerializer,
    PlatformStatsSnapshotSerializer,
    serialize_atcoder_submission_overview,
    serialize_codeforces_rating_history,
    serialize_codeforces_recent_activity,
)
from apps.connectors.services import get_connector, get_sync_cooldown_seconds


class PlatformAccountViewSet(viewsets.ModelViewSet):
    serializer_class = PlatformAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return (
            PlatformAccount.objects.filter(user=self.request.user)
            .select_related(
                "codeforces_stats",
                "atcoder_stats",
                "atcoder_sync_state",
            )
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="sync")
    def sync(self, request, pk=None):
        platform_account = self.get_object()

        if platform_account.platform == PlatformAccount.Platform.ATCODER:
            result = AtCoderSyncOrchestrator().sync(platform_account)
            refreshed_account = self.get_queryset().get(pk=platform_account.pk)
            payload = self.get_serializer(refreshed_account).data
            payload.update(result.as_dict())
            payload["last_synced_at"] = refreshed_account.last_synced_at
            return Response(
                payload,
                status=self._atcoder_result_http_status(result),
            )

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
                        f"{connector.display_name} synchronization is currently "
                        "disabled."
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
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ProviderRateLimitError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except ExternalServiceError as exc:
            return Response(
                {
                    "detail": str(exc)
                    or (
                        "The provider is temporarily unavailable. Please try "
                        "again later."
                    )
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

        result = AtCoderSyncOrchestrator().sync_submissions_only(platform_account)
        if result.status in {SourceSyncStatus.FAILED, SourceSyncStatus.BLOCKED}:
            return Response(
                {"source": result.as_dict()},
                status=self._atcoder_source_http_status(result.error_code),
            )
        if result.status == SourceSyncStatus.DISABLED:
            return Response(
                {"source": result.as_dict()},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        payload = serialize_atcoder_submission_overview(platform_account)
        payload["source"] = result.as_dict()
        payload["sync"] = result.details
        return Response(payload, status=status.HTTP_200_OK)

    @staticmethod
    def _atcoder_source_http_status(error_code):
        if error_code == SyncErrorCode.RATE_LIMITED:
            return status.HTTP_429_TOO_MANY_REQUESTS
        if error_code == SyncErrorCode.INVALID_ACCOUNT:
            return status.HTTP_400_BAD_REQUEST
        return status.HTTP_503_SERVICE_UNAVAILABLE

    @classmethod
    def _atcoder_result_http_status(cls, result):
        if result.status != OverallSyncStatus.FAILED:
            return status.HTTP_200_OK
        active_errors = [
            source.error_code
            for source in (result.rating, result.submissions)
            if source.status != SourceSyncStatus.DISABLED
        ]
        if active_errors and all(
            error == SyncErrorCode.RATE_LIMITED for error in active_errors
        ):
            return status.HTTP_429_TOO_MANY_REQUESTS
        if active_errors and all(
            error == SyncErrorCode.INVALID_ACCOUNT for error in active_errors
        ):
            return status.HTTP_400_BAD_REQUEST
        return status.HTTP_503_SERVICE_UNAVAILABLE


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


class AtCoderAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account = (
            PlatformAccount.objects.filter(
                user=request.user,
                platform=PlatformAccount.Platform.ATCODER,
            )
            .select_related(
                "atcoder_stats",
                "atcoder_sync_state",
                "atcoder_submission_sync_state",
            )
            .first()
        )

        if account is None:
            return Response(
                {
                    "platform": PlatformAccount.Platform.ATCODER,
                    "account": None,
                    "sync": None,
                    "stats": None,
                    "rating_history": [],
                    "recent_activity": [],
                    "snapshots": [],
                }
            )

        stats = self._related_or_none(account, "atcoder_stats", AtCoderStats)
        sync_state = self._related_or_none(
            account,
            "atcoder_sync_state",
            AtCoderSyncState,
        )
        submission_state = self._related_or_none(
            account,
            "atcoder_submission_sync_state",
            AtCoderSubmissionSyncState,
        )
        rating_history = PlatformRatingEvent.objects.filter(
            platform_account=account,
            discipline=PlatformRatingEvent.Discipline.ALGORITHM,
        ).order_by("occurred_at", "id")
        recent_activity = AtCoderSubmission.objects.filter(
            platform_account=account
        ).order_by("-submitted_at", "-external_submission_id")[
            :RECENT_ACTIVITY_LIMIT
        ]
        snapshots = list(
            PlatformStatsSnapshot.objects.filter(platform_account=account)[
                :SNAPSHOT_LIMIT
            ]
        )
        snapshots.reverse()
        sync_summary = build_atcoder_sync_summary(
            stats,
            sync_state,
            submission_state,
        )

        return Response(
            {
                "platform": PlatformAccount.Platform.ATCODER,
                "account": AtCoderAnalyticsAccountSerializer(account).data,
                "sync": AtCoderAnalyticsSyncSerializer(sync_summary).data,
                "stats": (
                    AtCoderAnalyticsStatsSerializer(stats).data
                    if stats
                    else None
                ),
                "rating_history": AtCoderAnalyticsRatingEventSerializer(
                    rating_history,
                    many=True,
                ).data,
                "recent_activity": AtCoderAnalyticsActivitySerializer(
                    recent_activity,
                    many=True,
                ).data,
                "snapshots": AtCoderAnalyticsSnapshotSerializer(
                    snapshots,
                    many=True,
                ).data,
            }
        )

    @staticmethod
    def _related_or_none(account, relation_name, model_class):
        try:
            return getattr(account, relation_name)
        except model_class.DoesNotExist:
            return None


class CompetitiveProgrammingOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(build_competitive_programming_overview(request.user))
