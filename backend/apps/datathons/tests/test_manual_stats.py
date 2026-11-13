from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.connectors.models import PlatformAccount
from apps.connectors.serializers import PlatformAccountSerializer
from apps.datathons.linking import link_kaggle_account
from apps.datathons.models import KaggleManualTrackStats, KaggleTrackStats


def values(**changes):
    return {
        "rank_status": "ranked", "global_rank": 123, "highest_rank": 99,
        "tier": "Expert", "points": "15.2500", "gold_medals": 0,
        "silver_medals": 2, "bronze_medals": 3, **changes,
    }


class KaggleManualStatsTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user(username="manual_owner", email="manual_owner@example.com", password="unused")
        self.other = users.objects.create_user(username="manual_other", email="manual_other@example.com", password="unused")
        self.account = PlatformAccount.objects.create(
            user=self.owner, platform="kaggle", handle="example_user",
            profile_url="https://www.kaggle.com/example_user",
        )
        self.other_account = PlatformAccount.objects.create(
            user=self.other, platform="kaggle", handle="example_user",
            profile_url="https://www.kaggle.com/example_user",
        )
        link_kaggle_account(self.account)
        link_kaggle_account(self.other_account)
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.url = reverse("kaggle-manual-track", args=["competitions"])

    def test_manual_entry_is_self_reported_and_private_to_account(self):
        response = self.client.put(self.url, values(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["global_rank"], 123)
        self.assertEqual(KaggleTrackStats.objects.count(), 0)
        overview = self.client.get(reverse("kaggle-overview"))
        self.assertEqual(overview.data["manual_tracks"]["competitions"]["global_rank"], 123)
        self.assertIsNone(overview.data["tracks"]["competitions"]["global_rank"])
        self.assertIsNone(overview.data["last_successful_at"])

        other_client = APIClient()
        other_client.force_authenticate(user=self.other)
        other_overview = other_client.get(reverse("kaggle-overview"))
        self.assertIsNone(other_overview.data["manual_tracks"]["competitions"])
        other_client.put(self.url, values(global_rank=456), format="json")
        self.assertEqual(self.client.get(reverse("kaggle-overview")).data["manual_tracks"]["competitions"]["global_rank"], 123)

    def test_update_and_delete_only_selected_track(self):
        self.client.put(self.url, values(), format="json")
        code_url = reverse("kaggle-manual-track", args=["code"])
        self.client.put(code_url, values(global_rank=500), format="json")
        self.assertEqual(self.client.put(self.url, values(global_rank=77), format="json").status_code, 200)
        self.assertEqual(self.client.delete(self.url).status_code, 204)
        overview = self.client.get(reverse("kaggle-overview"))
        self.assertIsNone(overview.data["manual_tracks"]["competitions"])
        self.assertEqual(overview.data["manual_tracks"]["code"]["global_rank"], 500)

    def test_unranked_track_can_be_reported_without_rank(self):
        response = self.client.put(
            self.url, values(rank_status="unranked", global_rank=None, tier=None, points=None), format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["rank_status"], "unranked")
        self.assertIsNone(response.data["global_rank"])
        self.assertEqual(response.data["gold_medals"], 0)

    def test_invalid_claims_are_rejected(self):
        for payload in (
            values(global_rank=0), values(rank_status="ranked", global_rank=None),
            values(rank_status="unranked"), values(rank_status="unknown", global_rank=3),
            values(gold_medals=-1), values(points="10000000000"),
            values(tier="Legend"),
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.put(self.url, payload, format="json").status_code, 400)
        self.assertEqual(KaggleManualTrackStats.objects.count(), 0)
        self.assertEqual(self.client.put(reverse("kaggle-manual-track", args=["discussion"]), values(), format="json").status_code, 404)

    def test_unlinked_and_invalid_link_cannot_write(self):
        self.account.delete()
        self.assertEqual(self.client.put(self.url, values(), format="json").status_code, 404)
        self.assertEqual(self.client.delete(self.url).status_code, 404)

    def test_stale_profile_link_hides_manual_values(self):
        self.client.put(self.url, values(), format="json")
        PlatformAccount.objects.filter(pk=self.account.pk).update(
            handle="different_user", profile_url="https://www.kaggle.com/different_user",
        )
        self.assertIsNone(self.client.get(reverse("kaggle-overview")).data["manual_tracks"]["competitions"])
        self.assertEqual(self.client.put(self.url, values(), format="json").status_code, 409)

    def test_changing_or_deleting_link_removes_manual_values(self):
        self.client.put(self.url, values(), format="json")
        serializer = PlatformAccountSerializer(self.account, data={"handle": "new_user"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.assertFalse(KaggleManualTrackStats.objects.filter(platform_account=self.account).exists())
        self.client.put(self.url, values(), format="json")
        self.account.delete()
        self.assertEqual(KaggleManualTrackStats.objects.count(), 0)

    def test_authentication_is_required(self):
        anonymous = APIClient()
        self.assertEqual(anonymous.put(self.url, values(), format="json").status_code, 401)
