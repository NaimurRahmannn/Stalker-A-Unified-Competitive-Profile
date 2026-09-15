from django.db import transaction
from django.utils import timezone

from apps.connectors.models import CTFTeamProfile, CTFYearlyRanking, PlatformAccount
from apps.connectors.providers.ctftime.domain import CTFSyncData


class CTFtimePersistenceMapper:
    """
    Handles mapping CTF domain DTOs to the Django database persistence layer.
    """

    @staticmethod
    def persist_sync_data(account: PlatformAccount, data: CTFSyncData) -> None:
        """
        Atomically persists the complete CTF provider data onto the platform account.
        Overwrites existing ranking records for the same year, avoiding duplicates.
        """
        now = timezone.now()

        with transaction.atomic():
            profile, _ = CTFTeamProfile.objects.update_or_create(
                platform_account=account,
                defaults={
                    "external_team_id": data.profile.team_id,
                    "name": data.profile.name,
                    "country": data.profile.country,
                    "logo_url": data.profile.logo_url,
                    "data_updated_at": now,
                },
            )

            # Update or create yearly rankings
            for ranking_data in data.yearly_rankings:
                CTFYearlyRanking.objects.update_or_create(
                    team_profile=profile,
                    year=ranking_data.year,
                    defaults={
                        "global_rank": ranking_data.global_rank,
                        "country_rank": ranking_data.country_rank,
                        "rating_points": ranking_data.rating_points,
                    },
                )
