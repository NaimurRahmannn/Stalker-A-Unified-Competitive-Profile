from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ExternalAccount
from apps.dashboard.models import ProfileSnapshot


User = get_user_model()


class DashboardMeEndpointTests(APITestCase):
	def test_dashboard_me_endpoint_for_authenticated_user(self):
		user = User.objects.create_user(
			username="dash_user",
			email="dash@example.com",
			password="strong-pass-123",
		)
		account = ExternalAccount.objects.create(
			user=user,
			source=ExternalAccount.Source.CODEFORCES,
			handle_or_slug="tourist",
			profile_url="https://codeforces.com/profile/tourist",
			verification_status=ExternalAccount.VerificationStatus.VERIFIED,
			sync_status=ExternalAccount.SyncStatus.SUCCESS,
		)
		ProfileSnapshot.objects.create(
			external_account=account,
			display_name="Gennady Korotkevich",
			headline_rank_title="legendary grandmaster",
			rating=3900,
			highest_rating=3900,
			avatar_url="https://example.com/avatar.png",
			metadata_json={"raw_profile": {"handle": "tourist"}},
		)

		self.client.force_authenticate(user=user)
		response = self.client.get(reverse("dashboard-me"))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["user"]["username"], "dash_user")
		self.assertEqual(len(response.data["accounts"]), 1)
		self.assertEqual(response.data["accounts"][0]["source"], "codeforces")
		self.assertEqual(response.data["accounts"][0]["latest_snapshot"]["rating"], 3900)
