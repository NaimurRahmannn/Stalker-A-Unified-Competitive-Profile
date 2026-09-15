from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.connectors.models import CTFTeamProfile, CTFYearlyRanking, PlatformAccount
from apps.connectors.providers.ctftime.domain import (
    CTFProfileData,
    CTFSyncData,
    CTFYearlyRankingData,
)
from apps.connectors.providers.ctftime.persistence import CTFtimePersistenceMapper

User = get_user_model()


class CTFtimePersistenceMapperTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
        )
        self.account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CTFTIME,
            handle="1005",
        )

    def _create_mock_sync_data(self, name="More Smoked Leet Chicken") -> CTFSyncData:
        return CTFSyncData(
            profile=CTFProfileData(
                team_id="1005",
                name=name,
                country="RU",
                logo_url="https://ctftime.org/logo.png",
            ),
            yearly_rankings=(
                CTFYearlyRankingData(
                    year=2025,
                    global_rank=41,
                    country_rank=3,
                    rating_points=530.24,
                    organizer_points=0.0,
                ),
                CTFYearlyRankingData(
                    year=2024,
                    global_rank=39,
                    country_rank=4,
                    rating_points=470.92,
                    organizer_points=0.0,
                ),
            ),
        )

    def test_persist_creates_new_profile_and_rankings(self):
        data = self._create_mock_sync_data()
        CTFtimePersistenceMapper.persist_sync_data(self.account, data)

        profile = CTFTeamProfile.objects.get(platform_account=self.account)
        self.assertEqual(profile.external_team_id, "1005")
        self.assertEqual(profile.name, "More Smoked Leet Chicken")
        self.assertEqual(profile.country, "RU")

        rankings = CTFYearlyRanking.objects.filter(team_profile=profile).order_by("-year")
        self.assertEqual(rankings.count(), 2)
        
        self.assertEqual(rankings[0].year, 2025)
        self.assertEqual(rankings[0].global_rank, 41)
        
        self.assertEqual(rankings[1].year, 2024)
        self.assertEqual(rankings[1].global_rank, 39)

    def test_persist_updates_existing_profile_metadata(self):
        # Initial sync
        CTFtimePersistenceMapper.persist_sync_data(
            self.account, self._create_mock_sync_data(name="Old Name")
        )

        profile = CTFTeamProfile.objects.get(platform_account=self.account)
        self.assertEqual(profile.name, "Old Name")

        # Second sync with new name
        CTFtimePersistenceMapper.persist_sync_data(
            self.account, self._create_mock_sync_data(name="New Name")
        )

        # Should update existing, not create new
        self.assertEqual(CTFTeamProfile.objects.count(), 1)
        
        profile.refresh_from_db()
        self.assertEqual(profile.name, "New Name")

    def test_persist_updates_existing_yearly_ranking(self):
        # Initial sync
        data = self._create_mock_sync_data()
        CTFtimePersistenceMapper.persist_sync_data(self.account, data)

        # Create updated sync data for the same year (2025)
        updated_data = CTFSyncData(
            profile=data.profile,
            yearly_rankings=(
                CTFYearlyRankingData(
                    year=2025,
                    global_rank=1,  # Rank improved
                    country_rank=1,
                    rating_points=999.99,
                    organizer_points=0.0,
                ),
            ),
        )

        CTFtimePersistenceMapper.persist_sync_data(self.account, updated_data)

        # Should still be 2 rankings total (2024 wasn't touched in this sync, though in reality API returns all years)
        # Wait, our update_or_create loops over the provided data. 
        # If the API only returned 2025 this time, 2024 remains in DB untouched.
        # But we must ensure 2025 was UPDATED, not duplicated.
        
        profile = CTFTeamProfile.objects.get(platform_account=self.account)
        rankings = CTFYearlyRanking.objects.filter(team_profile=profile, year=2025)
        
        self.assertEqual(rankings.count(), 1)
        self.assertEqual(rankings.first().global_rank, 1)
        self.assertEqual(rankings.first().rating_points, 999.99)

    def test_persist_handles_missing_optional_fields(self):
        data = CTFSyncData(
            profile=CTFProfileData(
                team_id="1005",
                name="Team",
                country=None,
                logo_url=None,
            ),
            yearly_rankings=(
                CTFYearlyRankingData(
                    year=2026,
                    global_rank=None,
                    country_rank=None,
                    rating_points=10.0,
                    organizer_points=0.0,
                ),
            ),
        )
        
        CTFtimePersistenceMapper.persist_sync_data(self.account, data)

        profile = CTFTeamProfile.objects.get(platform_account=self.account)
        self.assertIsNone(profile.country)
        self.assertIsNone(profile.logo_url)

        ranking = CTFYearlyRanking.objects.get(team_profile=profile, year=2026)
        self.assertIsNone(ranking.global_rank)
        self.assertIsNone(ranking.country_rank)
