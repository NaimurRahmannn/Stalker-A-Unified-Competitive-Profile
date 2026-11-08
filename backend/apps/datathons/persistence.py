from django.db import transaction
from django.utils import timezone

from apps.connectors.providers.kaggle.domain import NormalizedKaggleProfile
from apps.connectors.providers.kaggle.exceptions import KaggleDocumentError
from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity
from apps.datathons.models import KaggleProfile, KaggleRankingSnapshot, KaggleTrackStats


HISTORY_DAYS = 365


@transaction.atomic
def persist_kaggle_profile_statistics(profile: KaggleProfile, data: NormalizedKaggleProfile) -> KaggleProfile:
    identity = normalize_kaggle_identity(data.username)
    if identity.lookup_key != profile.normalized_username:
        raise KaggleDocumentError("identity_mismatch", "Profile identity changed before persistence.")
    locked = KaggleProfile.objects.select_for_update().get(pk=profile.pk)
    if locked.last_successful_at and data.observed_at < locked.last_successful_at:
        raise KaggleDocumentError("stale_observation", "Older ranking observations cannot replace cached data.")
    current = {row.track: row for row in KaggleTrackStats.objects.filter(profile=locked)}
    for item in data.tracks:
        row = current.get(item.track)
        created = row is None
        if created:
            row = KaggleTrackStats(
                profile=locked, track=item.track, source=data.source, data_collected_at=data.observed_at
            )
        before = (row.rank_status, row.global_rank, row.tier, row.points)
        changed = created
        if item.rank_status != "unknown" and row.rank_status != item.rank_status:
            row.rank_status = item.rank_status
            changed = True
        if item.rank_status == "unranked":
            for field in ("global_rank", "tier", "points"):
                if getattr(row, field) is not None:
                    setattr(row, field, None)
                    changed = True
        for field in item.provided_fields:
            value = item.values[field]
            if value is None and item.rank_status != "unranked":
                continue
            if getattr(row, field) != value:
                setattr(row, field, value)
                changed = True
        if row.source != data.source:
            row.source = data.source
            changed = True
        if row.data_collected_at != data.observed_at:
            row.data_collected_at = data.observed_at
            changed = True
        if changed:
            row.save()
        after = (row.rank_status, row.global_rank, row.tier, row.points)
        day = timezone.localdate(data.observed_at)
        if after != before and row.rank_status != KaggleTrackStats.RankStatus.UNKNOWN:
            KaggleRankingSnapshot.objects.update_or_create(
                profile=locked, track=item.track, captured_on=day,
                defaults={
                    "rank_status": row.rank_status, "global_rank": row.global_rank,
                    "tier": row.tier, "points": row.points, "captured_at": data.observed_at,
                },
            )
            old_ids = list(KaggleRankingSnapshot.objects.filter(
                profile=locked, track=item.track
            ).order_by("-captured_at", "-pk").values_list("pk", flat=True)[HISTORY_DAYS:])
            if old_ids:
                KaggleRankingSnapshot.objects.filter(pk__in=old_ids).delete()
    locked.collection_status = KaggleProfile.CollectionStatus.SUCCESS
    locked.last_attempted_at = timezone.now()
    locked.last_successful_at = data.observed_at
    locked.last_error_code = ""
    locked.save(update_fields=["collection_status", "last_attempted_at", "last_successful_at", "last_error_code", "updated_at"])
    return locked


@transaction.atomic
def record_kaggle_collection_failure(profile: KaggleProfile, code: str) -> None:
    locked = KaggleProfile.objects.select_for_update().get(pk=profile.pk)
    locked.collection_status = KaggleProfile.CollectionStatus.FAILED
    locked.last_attempted_at = timezone.now()
    locked.last_error_code = code[:64]
    locked.save(update_fields=["collection_status", "last_attempted_at", "last_error_code", "updated_at"])
