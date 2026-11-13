from apps.connectors.models import PlatformAccount
from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity
from apps.datathons.linking import KaggleProfileLink
from apps.datathons.manual_serializers import KaggleManualTrackSerializer
from apps.datathons.models import KaggleTrackStats


def _empty_track():
    return {
        "rank_status": "unknown",
        "global_rank": None,
        "highest_rank": None,
        "tier": None,
        "points": None,
        "gold_medals": None,
        "silver_medals": None,
        "bronze_medals": None,
        "source": None,
        "data_collected_at": None,
    }


def build_kaggle_overview(user):
    tracks = {track: _empty_track() for track in KaggleTrackStats.Track.values}
    manual_tracks = {track: None for track in KaggleTrackStats.Track.values}
    account = (
        PlatformAccount.objects.filter(
            user=user, platform=PlatformAccount.Platform.KAGGLE
        )
        .select_related("kaggle_profile_link__kaggle_profile")
        .prefetch_related(
            "kaggle_profile_link__kaggle_profile__track_stats",
            "kaggle_manual_stats",
        )
        .first()
    )
    if account is None:
        return {
            "linked": False,
            "username": None,
            "profile_url": None,
            "collection_status": "not_collected",
            "last_attempted_at": None,
            "last_successful_at": None,
            "tracks": tracks,
            "manual_tracks": manual_tracks,
            "summary": {
                "competitions_rank": None,
                "competitions_tier": None,
                "code_rank": None,
                "code_tier": None,
                "datasets_rank": None,
                "datasets_tier": None,
                "total_medals": 0,
                "gold_medals": 0,
                "silver_medals": 0,
                "bronze_medals": 0,
                "has_data": False,
            },
        }

    profile = None
    try:
        profile = account.kaggle_profile_link.kaggle_profile
    except (KaggleProfileLink.DoesNotExist, AttributeError):
        profile = None

    try:
        identity = normalize_kaggle_identity(account.handle)
    except ValueError:
        identity = None

    if profile is not None and (
        identity is None
        or profile.normalized_username != identity.lookup_key
        or profile.profile_url != identity.profile_url
    ):
        profile = None

    if profile is not None:
        for row in profile.track_stats.all():
            tracks[row.track] = {
                "rank_status": row.rank_status,
                "global_rank": row.global_rank,
                "highest_rank": row.highest_rank,
                "tier": row.tier,
                "points": row.points,
                "gold_medals": row.gold_medals,
                "silver_medals": row.silver_medals,
                "bronze_medals": row.bronze_medals,
                "source": row.source,
                "data_collected_at": row.data_collected_at,
            }
        for row in account.kaggle_manual_stats.all():
            manual_tracks[row.track] = KaggleManualTrackSerializer(row).data

    def _active_track(name):
        return manual_tracks.get(name) or tracks.get(name) or {}

    comp = _active_track("competitions")
    code = _active_track("code")
    data = _active_track("datasets")

    total_gold = sum(filter(None, [comp.get("gold_medals"), code.get("gold_medals"), data.get("gold_medals")]))
    total_silver = sum(filter(None, [comp.get("silver_medals"), code.get("silver_medals"), data.get("silver_medals")]))
    total_bronze = sum(filter(None, [comp.get("bronze_medals"), code.get("bronze_medals"), data.get("bronze_medals")]))
    total_medals = total_gold + total_silver + total_bronze

    has_data = any(
        t.get("global_rank") is not None
        or t.get("tier") is not None
        or (t.get("gold_medals") or 0) > 0
        or (t.get("silver_medals") or 0) > 0
        or (t.get("bronze_medals") or 0) > 0
        for t in [comp, code, data]
    )

    return {
        "linked": True,
        "username": account.handle,
        "profile_url": account.profile_url,
        "collection_status": profile.collection_status if profile else "not_collected",
        "last_attempted_at": profile.last_attempted_at if profile else None,
        "last_successful_at": profile.last_successful_at if profile else None,
        "tracks": tracks,
        "manual_tracks": manual_tracks,
        "summary": {
            "competitions_rank": comp.get("global_rank"),
            "competitions_tier": comp.get("tier"),
            "code_rank": code.get("global_rank"),
            "code_tier": code.get("tier"),
            "datasets_rank": data.get("global_rank"),
            "datasets_tier": data.get("tier"),
            "total_medals": total_medals,
            "gold_medals": total_gold,
            "silver_medals": total_silver,
            "bronze_medals": total_bronze,
            "has_data": has_data,
        },
    }


def build_kaggle_platform_stats(account: PlatformAccount):
    profile = None
    try:
        profile = account.kaggle_profile_link.kaggle_profile
    except (KaggleProfileLink.DoesNotExist, AttributeError):
        profile = None

    try:
        identity = normalize_kaggle_identity(account.handle)
    except ValueError:
        identity = None

    if profile is not None and (
        identity is None
        or profile.normalized_username != identity.lookup_key
        or profile.profile_url != identity.profile_url
    ):
        profile = None

    if profile is None:
        return {
            "competitions_rank": None,
            "competitions_tier": None,
            "code_rank": None,
            "code_tier": None,
            "datasets_rank": None,
            "datasets_tier": None,
            "total_medals": 0,
            "gold_medals": 0,
            "silver_medals": 0,
            "bronze_medals": 0,
            "has_data": False,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None,
        }

    manual_rows = {row.track: row for row in account.kaggle_manual_stats.all()}
    profile_rows = {row.track: row for row in profile.track_stats.all()}

    def _track(name):
        return manual_rows.get(name) or profile_rows.get(name)

    comp = _track("competitions")
    code = _track("code")
    data = _track("datasets")

    total_gold = sum(filter(None, [getattr(t, "gold_medals", None) for t in [comp, code, data] if t]))
    total_silver = sum(filter(None, [getattr(t, "silver_medals", None) for t in [comp, code, data] if t]))
    total_bronze = sum(filter(None, [getattr(t, "bronze_medals", None) for t in [comp, code, data] if t]))
    total_medals = total_gold + total_silver + total_bronze

    has_data = any(
        getattr(t, "global_rank", None) is not None
        or getattr(t, "tier", None) is not None
        or (getattr(t, "gold_medals", None) or 0) > 0
        or (getattr(t, "silver_medals", None) or 0) > 0
        or (getattr(t, "bronze_medals", None) or 0) > 0
        for t in [comp, code, data] if t
    )

    return {
        "competitions_rank": getattr(comp, "global_rank", None),
        "competitions_tier": getattr(comp, "tier", None),
        "code_rank": getattr(code, "global_rank", None),
        "code_tier": getattr(code, "tier", None),
        "datasets_rank": getattr(data, "global_rank", None),
        "datasets_tier": getattr(data, "tier", None),
        "total_medals": total_medals,
        "gold_medals": total_gold,
        "silver_medals": total_silver,
        "bronze_medals": total_bronze,
        "has_data": has_data,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
    }
