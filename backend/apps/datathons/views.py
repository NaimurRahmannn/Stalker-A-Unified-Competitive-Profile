from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connectors.models import PlatformAccount
from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity
from apps.datathons.models import KaggleCollectionRun, KaggleProfileLink, KaggleTrackStats
from apps.datathons.services.providers import CollectionError, PROVIDERS
from apps.datathons.services.queue import CooldownActive, request_kaggle_collection


def _empty_track():
    return {
        "rank_status": "unknown", "global_rank": None, "highest_rank": None,
        "tier": None, "points": None, "gold_medals": None,
        "silver_medals": None, "bronze_medals": None,
        "source": None, "data_collected_at": None,
    }


def _owned_kaggle_account(user):
    account = PlatformAccount.objects.filter(
        user=user, platform=PlatformAccount.Platform.KAGGLE,
    ).select_related("kaggle_profile_link__kaggle_profile").first()
    if account is None:
        return None, None
    try:
        profile = account.kaggle_profile_link.kaggle_profile
        identity = normalize_kaggle_identity(account.handle)
    except (KaggleProfileLink.DoesNotExist, ValueError):
        return account, None
    if profile.normalized_username != identity.lookup_key or profile.profile_url != identity.profile_url:
        return account, None
    return account, profile


class KaggleOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tracks = {track: _empty_track() for track in KaggleTrackStats.Track.values}
        account = (PlatformAccount.objects.filter(
            user=request.user, platform=PlatformAccount.Platform.KAGGLE
        ).select_related("kaggle_profile_link__kaggle_profile").prefetch_related(
            "kaggle_profile_link__kaggle_profile__track_stats"
        ).first())
        if account is None:
            return Response({
                "linked": False, "username": None, "profile_url": None,
                "collection_status": "not_collected", "last_attempted_at": None,
                "last_successful_at": None,
                "tracks": tracks,
            })
        try:
            profile = account.kaggle_profile_link.kaggle_profile
        except KaggleProfileLink.DoesNotExist:
            profile = None
        try:
            identity = normalize_kaggle_identity(account.handle)
        except ValueError:
            identity = None
        if profile is not None and (identity is None or profile.normalized_username != identity.lookup_key):
            profile = None
        if profile is not None:
            for row in profile.track_stats.all():
                tracks[row.track] = {
                    "rank_status": row.rank_status, "global_rank": row.global_rank,
                    "highest_rank": row.highest_rank, "tier": row.tier,
                    "points": row.points, "gold_medals": row.gold_medals,
                    "silver_medals": row.silver_medals, "bronze_medals": row.bronze_medals,
                    "source": row.source, "data_collected_at": row.data_collected_at,
                }
        return Response({
            "linked": True, "username": account.handle,
            "profile_url": account.profile_url,
            "collection_status": profile.collection_status if profile else "not_collected",
            "last_attempted_at": profile.last_attempted_at if profile else None,
            "last_successful_at": profile.last_successful_at if profile else None,
            "tracks": tracks,
        })


class KaggleCapabilitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        enabled = settings.KAGGLE_COLLECTION_ENABLED
        registration = PROVIDERS.get(settings.KAGGLE_PROVIDER_NAME) if enabled else None
        available = registration is not None
        if available:
            try:
                registration.policy.validate()
            except CollectionError:
                available = False
        return Response({
            "collection_enabled": enabled,
            "provider_available": available,
            "can_request_sync": enabled and available,
            "reason": None if available else "provider_disabled",
        })


class KaggleSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.data:
            return Response({"code": "unexpected_fields", "detail": "This endpoint takes no profile fields."},
                            status=status.HTTP_400_BAD_REQUEST)
        account, profile = _owned_kaggle_account(request.user)
        if account is None:
            return Response({"code": "not_linked", "detail": "Link a Kaggle account first."},
                            status=status.HTTP_404_NOT_FOUND)
        if profile is None:
            return Response({"code": "invalid_link", "detail": "The Kaggle account link needs correction."},
                            status=status.HTTP_409_CONFLICT)
        try:
            result = request_kaggle_collection(profile, requested_by=request.user)
        except CooldownActive as exc:
            return Response({"code": "cooldown", "retry_after_seconds": exc.retry_after_seconds},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        except CollectionError as exc:
            return Response({"code": exc.code, "detail": "Kaggle collection is unavailable."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({
            "run_id": result.run.pk, "status": result.run.status, "username": profile.username,
            "deduplicated": result.deduplicated, "queued_at": result.run.queued_at,
        }, status=status.HTTP_202_ACCEPTED)


class KaggleSyncStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account, profile = _owned_kaggle_account(request.user)
        if account is None:
            return Response({"code": "not_linked", "detail": "Link a Kaggle account first."},
                            status=status.HTTP_404_NOT_FOUND)
        if profile is None:
            return Response({"code": "invalid_link", "detail": "The Kaggle account link needs correction."},
                            status=status.HTTP_409_CONFLICT)
        run = KaggleCollectionRun.objects.filter(profile=profile).order_by("-created_at", "-pk").first()
        if run is None:
            return Response({"status": "not_started", "username": profile.username, "run_id": None})
        dispatch_state = (
            "failed" if run.last_dispatch_error_code else
            "dispatched" if run.dispatched_at or run.attempt_count > 0 or run.status in (
                KaggleCollectionRun.Status.RUNNING, KaggleCollectionRun.Status.SUCCEEDED,
                KaggleCollectionRun.Status.RETRYING,
            ) else "pending"
        )
        return Response({
            "run_id": run.pk, "username": profile.username, "trigger": run.trigger,
            "status": run.status, "attempt_count": run.attempt_count,
            "queued_at": run.queued_at, "started_at": run.started_at,
            "finished_at": run.finished_at, "next_attempt_at": run.next_attempt_at,
            "error_code": run.error_code or None, "dispatch_state": dispatch_state,
        })
