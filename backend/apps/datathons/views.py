from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connectors.models import PlatformAccount
from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity
from apps.datathons.models import KaggleProfileLink, KaggleTrackStats


def _empty_track():
    return {
        "rank_status": "unknown", "global_rank": None, "highest_rank": None,
        "tier": None, "points": None, "gold_medals": None,
        "silver_medals": None, "bronze_medals": None,
    }


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
                "collection_status": "not_collected", "last_successful_at": None,
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
                }
        return Response({
            "linked": True, "username": account.handle,
            "profile_url": account.profile_url,
            "collection_status": profile.collection_status if profile else "not_collected",
            "last_successful_at": profile.last_successful_at if profile else None,
            "tracks": tracks,
        })
