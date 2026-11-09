from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.connectors.models import PlatformAccount
from apps.connectors.providers.kaggle.domain import NormalizedKaggleProfile, NormalizedKaggleTrack
from apps.connectors.providers.kaggle.exceptions import KaggleDocumentError
from apps.connectors.providers.kaggle.normalizer import normalize_profile
from apps.connectors.providers.kaggle.parser import parse_profile_document
from apps.datathons.linking import link_kaggle_account
from apps.datathons.models import KaggleProfile, KaggleProfileLink, KaggleRankingSnapshot, KaggleTrackStats
from apps.datathons.persistence import persist_kaggle_profile_statistics, record_kaggle_collection_failure


User = get_user_model()
FIXTURE = Path(__file__).resolve().parents[2] / "connectors/providers/kaggle/tests/fixtures/complete_profile.html"


def fixture_data():
    return normalize_profile(parse_profile_document(FIXTURE.read_text(encoding="utf-8"), "example_user"))


class KaggleLinkTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="password123")
        self.other = User.objects.create_user(username="bob", email="bob@example.com", password="password123")
        self.client.force_authenticate(self.user)

    def test_create_share_update_and_unlink(self):
        url = reverse("platform-account-list")
        created = self.client.post(url, {"platform": "kaggle", "handle": "Example_User"})
        self.assertEqual(created.status_code, 201, created.data)
        self.assertFalse(created.data["is_verified"])
        self.assertFalse(created.data["ownership_verified"])
        self.assertFalse(created.data["can_sync"])
        self.assertEqual(created.data["profile_url"], "https://www.kaggle.com/Example_User")
        first = PlatformAccount.objects.get(pk=created.data["id"])
        profile = first.kaggle_profile_link.kaggle_profile
        second = PlatformAccount.objects.create(user=self.other, platform="kaggle", handle="example_user")
        link_kaggle_account(second)
        self.assertEqual(second.kaggle_profile_link.kaggle_profile_id, profile.pk)
        self.assertEqual(KaggleProfile.objects.count(), 1)

        changed = self.client.patch(reverse("platform-account-detail", args=[first.pk]), {
            "handle": "https://www.kaggle.com/New_User"
        })
        self.assertEqual(changed.status_code, 200, changed.data)
        self.assertEqual(changed.data["handle"], "New_User")
        self.assertEqual(changed.data["profile_url"], "https://www.kaggle.com/New_User")
        first.refresh_from_db()
        self.assertNotEqual(first.kaggle_profile_link.kaggle_profile_id, profile.pk)
        self.assertTrue(KaggleProfile.objects.filter(pk=profile.pk).exists())

        deleted = self.client.delete(reverse("platform-account-detail", args=[first.pk]))
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(KaggleProfileLink.objects.filter(platform_account_id=first.pk).exists())
        self.assertTrue(KaggleProfile.objects.filter(pk=profile.pk).exists())

        recreated = self.client.post(url, {"platform": "kaggle", "handle": "Example_User"})
        self.assertEqual(recreated.status_code, 201, recreated.data)
        self.assertEqual(
            PlatformAccount.objects.get(pk=recreated.data["id"]).kaggle_profile_link.kaggle_profile_id,
            profile.pk,
        )

    def test_invalid_references_and_cross_platform_links(self):
        response = self.client.post(reverse("platform-account-list"), {
            "platform": "kaggle", "handle": "https://evil.com/user"
        })
        self.assertEqual(response.status_code, 400)
        response = self.client.post(reverse("platform-account-list"), {
            "platform": "kaggle", "handle": "example_user\n"
        })
        self.assertEqual(response.status_code, 400)
        account = PlatformAccount.objects.create(user=self.user, platform="codeforces", handle="example_user")
        profile = KaggleProfile.objects.create(
            username="example_user", normalized_username="example_user",
            profile_url="https://www.kaggle.com/example_user",
        )
        with self.assertRaises(ValidationError):
            KaggleProfileLink.objects.create(platform_account=account, kaggle_profile=profile)

    def test_non_owner_cannot_modify_kaggle_account(self):
        other_account = PlatformAccount.objects.create(user=self.other, platform="kaggle", handle="example_user")
        link_kaggle_account(other_account)
        response = self.client.patch(reverse("platform-account-detail", args=[other_account.pk]), {"handle": "newname"})
        self.assertEqual(response.status_code, 404)


class KagglePersistenceTests(TestCase):
    def setUp(self):
        self.profile = KaggleProfile.objects.create(
            username="example_user", normalized_username="example_user",
            profile_url="https://www.kaggle.com/example_user",
        )

    def test_import_creates_tracks_and_bounded_daily_snapshots(self):
        data = fixture_data()
        persist_kaggle_profile_statistics(self.profile, data)
        self.assertEqual(KaggleTrackStats.objects.filter(profile=self.profile).count(), 3)
        self.assertEqual(KaggleRankingSnapshot.objects.filter(profile=self.profile).count(), 3)
        persist_kaggle_profile_statistics(self.profile, data)
        self.assertEqual(KaggleRankingSnapshot.objects.filter(profile=self.profile).count(), 3)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.collection_status, "success")
        self.assertEqual(self.profile.last_successful_at, data.observed_at)

    def test_partial_data_preserves_previous_values_and_unranked_clears_current_rank(self):
        original = fixture_data()
        persist_kaggle_profile_statistics(self.profile, original)
        new_time = original.observed_at + timedelta(days=1)
        partial = NormalizedKaggleProfile("example_user", new_time, "offline_fixture_v1", (
            NormalizedKaggleTrack("competitions", "unknown", {"gold_medals": 3}, frozenset({"gold_medals"})),
        ))
        persist_kaggle_profile_statistics(self.profile, partial)
        row = KaggleTrackStats.objects.get(profile=self.profile, track="competitions")
        self.assertEqual(row.global_rank, 1234)
        self.assertEqual(row.gold_medals, 3)
        unranked = NormalizedKaggleProfile("example_user", new_time + timedelta(days=1), "offline_fixture_v1", (
            NormalizedKaggleTrack("competitions", "unranked", {}, frozenset()),
        ))
        persist_kaggle_profile_statistics(self.profile, unranked)
        row.refresh_from_db()
        self.assertEqual(row.rank_status, "unranked")
        self.assertIsNone(row.global_rank)
        self.assertEqual(row.highest_rank, 321)
        self.assertEqual(row.gold_medals, 3)

    def test_partial_tier_after_unranked_does_not_invent_a_rank(self):
        observed_at = timezone.now()
        persist_kaggle_profile_statistics(self.profile, NormalizedKaggleProfile(
            "example_user", observed_at, "offline_fixture_v1", (
                NormalizedKaggleTrack("competitions", "unranked", {
                    "highest_rank": 25, "gold_medals": 2,
                }, frozenset({"highest_rank", "gold_medals"})),
            ),
        ))
        persist_kaggle_profile_statistics(self.profile, NormalizedKaggleProfile(
            "example_user", observed_at + timedelta(seconds=1), "offline_fixture_v1", (
                NormalizedKaggleTrack("competitions", "unranked", {
                    "highest_rank": None, "gold_medals": None,
                }, frozenset({"highest_rank", "gold_medals"})),
            ),
        ))
        row = KaggleTrackStats.objects.get(profile=self.profile, track="competitions")
        self.assertEqual((row.highest_rank, row.gold_medals), (25, 2))
        persist_kaggle_profile_statistics(self.profile, NormalizedKaggleProfile(
            "example_user", observed_at + timedelta(seconds=2), "offline_fixture_v1", (
                NormalizedKaggleTrack("competitions", "unknown", {"tier": "Expert"}, frozenset({"tier"})),
            ),
        ))
        row.refresh_from_db()
        self.assertEqual(row.rank_status, "unknown")
        self.assertIsNone(row.global_rank)
        self.assertEqual(row.tier, "Expert")

    def test_stale_observation_and_failed_write_preserve_existing_data(self):
        original = fixture_data()
        persist_kaggle_profile_statistics(self.profile, original)
        with self.assertRaises(KaggleDocumentError):
            persist_kaggle_profile_statistics(self.profile, NormalizedKaggleProfile(
                "example_user", original.observed_at - timedelta(days=1), "offline_fixture_v1", ()
            ))
        self.assertEqual(KaggleTrackStats.objects.get(profile=self.profile, track="competitions").global_rank, 1234)
        changed = NormalizedKaggleProfile("example_user", original.observed_at + timedelta(days=1), "offline_fixture_v1", (
            NormalizedKaggleTrack("competitions", "ranked", {"global_rank": 100}, frozenset({"global_rank"})),
            NormalizedKaggleTrack("code", "ranked", {"global_rank": 200}, frozenset({"global_rank"})),
        ))
        with patch.object(KaggleTrackStats, "save", autospec=True, side_effect=RuntimeError("write failed")):
            with self.assertRaises(RuntimeError):
                persist_kaggle_profile_statistics(self.profile, changed)
        self.assertEqual(KaggleTrackStats.objects.get(profile=self.profile, track="competitions").global_rank, 1234)

    def test_constraints_reject_duplicate_profile_and_track(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            KaggleProfile.objects.create(username="Example_User", normalized_username="example_user", profile_url="https://www.kaggle.com/Example_User")
        data = fixture_data()
        persist_kaggle_profile_statistics(self.profile, data)
        with self.assertRaises(IntegrityError), transaction.atomic():
            KaggleTrackStats.objects.create(
                profile=self.profile, track="competitions", source="fixture", data_collected_at=timezone.now()
            )

    def test_profile_identity_validation_and_database_constraints(self):
        with self.assertRaises(ValidationError):
            KaggleProfile.objects.create(
                username="other_user", normalized_username="example_user",
                profile_url="https://www.kaggle.com/other_user",
            )
        for changes in ({"username": ""}, {"normalized_username": ""},
                        {"profile_url": ""}, {"collection_status": "stale"}):
            with self.subTest(changes=changes), self.assertRaises(IntegrityError), transaction.atomic():
                KaggleProfile.objects.filter(pk=self.profile.pk).update(**changes)

    def test_track_and_snapshot_database_constraints(self):
        now = timezone.now()
        stats = {"profile": self.profile, "track": "code", "source": "offline_fixture_v1", "data_collected_at": now}
        snapshot = {"profile": self.profile, "track": "code", "captured_on": timezone.localdate(now), "captured_at": now}
        for changes in ({"track": "private"}, {"rank_status": "stale"},
                        {"rank_status": "ranked"}, {"global_rank": 0},
                        {"highest_rank": 0}, {"gold_medals": -1}, {"points": Decimal("-1")},
                        {"rank_status": "unranked", "tier": "Expert"}):
            with self.subTest(model="stats", changes=changes), self.assertRaises(IntegrityError), transaction.atomic():
                KaggleTrackStats.objects.create(**(stats | changes))
        for changes in ({"track": "private"}, {"rank_status": "stale"},
                        {"rank_status": "ranked"}, {"global_rank": 0},
                        {"points": Decimal("-1")},
                        {"rank_status": "unranked", "tier": "Expert"}):
            with self.subTest(model="snapshot", changes=changes), self.assertRaises(IntegrityError), transaction.atomic():
                KaggleRankingSnapshot.objects.create(**(snapshot | changes))

    def test_failed_collection_preserves_success_and_cached_values(self):
        data = fixture_data()
        persist_kaggle_profile_statistics(self.profile, data)
        record_kaggle_collection_failure(self.profile, "invalid_document")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.collection_status, "failed")
        self.assertEqual(self.profile.last_error_code, "invalid_document")
        self.assertEqual(self.profile.last_successful_at, data.observed_at)
        self.assertIsNotNone(self.profile.last_attempted_at)
        self.assertEqual(KaggleTrackStats.objects.get(profile=self.profile, track="competitions").global_rank, 1234)
        self.assertEqual(KaggleRankingSnapshot.objects.filter(profile=self.profile).count(), 3)

    def test_history_retains_latest_365_daily_snapshots(self):
        now = timezone.now()
        old = [KaggleRankingSnapshot(
            profile=self.profile, track="competitions", rank_status="ranked", global_rank=rank,
            captured_at=now - timedelta(days=rank), captured_on=timezone.localdate(now - timedelta(days=rank)),
        ) for rank in range(1, 366)]
        KaggleRankingSnapshot.objects.bulk_create(old)
        persist_kaggle_profile_statistics(self.profile, NormalizedKaggleProfile(
            "example_user", now, "offline_fixture_v1", (
                NormalizedKaggleTrack("competitions", "ranked", {"global_rank": 1}, frozenset({"global_rank"})),
            ),
        ))
        history = KaggleRankingSnapshot.objects.filter(profile=self.profile, track="competitions")
        self.assertEqual(history.count(), 365)
        self.assertFalse(history.filter(captured_on=timezone.localdate(now - timedelta(days=365))).exists())
        self.assertTrue(history.filter(captured_on=timezone.localdate(now)).exists())


class KaggleOverviewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="password123")
        self.other = User.objects.create_user(username="bob", email="bob@example.com", password="password123")
        self.url = reverse("kaggle-overview")

    def test_auth_and_unlinked_response(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["linked"])
        self.assertIsNone(response.data["tracks"]["code"]["global_rank"])
        self.assertIsNone(response.data["last_attempted_at"])
        self.assertIsNone(response.data["tracks"]["code"]["source"])

    def test_cached_response_and_no_external_collection(self):
        account = PlatformAccount.objects.create(user=self.user, platform="kaggle", handle="example_user")
        profile = link_kaggle_account(account).kaggle_profile
        other_account = PlatformAccount.objects.create(user=self.other, platform="kaggle", handle="other_user")
        other_profile = link_kaggle_account(other_account).kaggle_profile
        persist_kaggle_profile_statistics(other_profile, NormalizedKaggleProfile(
            "other_user", timezone.now(), "offline_fixture_v1", (
                NormalizedKaggleTrack("code", "ranked", {"global_rank": 1}, frozenset({"global_rank"})),
            ),
        ))
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(self.url).data["collection_status"], "not_collected")
        persist_kaggle_profile_statistics(profile, fixture_data())
        with patch("requests.get", side_effect=AssertionError("network access")):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tracks"]["competitions"]["global_rank"], 1234)
        self.assertEqual(response.data["tracks"]["competitions"]["points"], Decimal("1250.5"))
        self.assertEqual(response.data["tracks"]["code"]["silver_medals"], 1)
        self.assertEqual(response.data["tracks"]["competitions"]["source"], "offline_fixture_v1")
        self.assertEqual(response.data["tracks"]["competitions"]["data_collected_at"], fixture_data().observed_at)
        self.assertIsNotNone(response.data["last_attempted_at"])
        self.assertNotEqual(response.data["tracks"]["code"]["global_rank"], 1)
        profile.collection_status = "failed"
        profile.save(update_fields=["collection_status"])
        self.assertEqual(self.client.get(self.url).data["tracks"]["competitions"]["global_rank"], 1234)

    def test_import_command_dry_run_and_persist(self):
        call_command("kaggle_import_fixture", username="example_user", fixture=str(FIXTURE), dry_run=True)
        self.assertEqual(KaggleProfile.objects.count(), 0)
        call_command("kaggle_import_fixture", username="example_user", fixture=str(FIXTURE))
        self.assertEqual(KaggleTrackStats.objects.count(), 3)

    def test_stale_direct_account_edit_cannot_reveal_old_stats(self):
        account = PlatformAccount.objects.create(user=self.user, platform="kaggle", handle="example_user")
        profile = link_kaggle_account(account).kaggle_profile
        persist_kaggle_profile_statistics(profile, fixture_data())
        PlatformAccount.objects.filter(pk=account.pk).update(handle="different_user")
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertTrue(response.data["linked"])
        self.assertEqual(response.data["collection_status"], "not_collected")
        self.assertIsNone(response.data["tracks"]["competitions"]["global_rank"])


class KagglePostgresConcurrencyTests(TransactionTestCase):
    def test_concurrent_links_share_one_profile(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL row locking and uniqueness behavior required")
        users = [
            User.objects.create_user(username=f"worker{index}", email=f"worker{index}@example.com", password="password123")
            for index in range(2)
        ]
        accounts = [
            PlatformAccount.objects.create(user=user, platform="kaggle", handle="Example_User")
            for user in users
        ]
        barrier = Barrier(2)

        def link(account_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                account = PlatformAccount.objects.get(pk=account_id)
                return link_kaggle_account(account).kaggle_profile_id
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(link, [account.pk for account in accounts]))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(KaggleProfile.objects.count(), 1)

    def test_concurrent_persistence_keeps_both_tracks(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL row locking required")
        profile = KaggleProfile.objects.create(
            username="example_user", normalized_username="example_user",
            profile_url="https://www.kaggle.com/example_user",
        )
        barrier = Barrier(2)
        observed_at = timezone.now()

        def persist(track):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                data = NormalizedKaggleProfile("example_user", observed_at, "offline_fixture_v1", (
                    NormalizedKaggleTrack(track, "ranked", {"global_rank": 42}, frozenset({"global_rank"})),
                ))
                persist_kaggle_profile_statistics(profile, data)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(persist, ("competitions", "code")))
        self.assertEqual(set(KaggleTrackStats.objects.filter(profile=profile).values_list("track", flat=True)), {"competitions", "code"})
