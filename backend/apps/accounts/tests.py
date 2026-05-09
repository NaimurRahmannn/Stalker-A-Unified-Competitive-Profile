from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ExternalAccount
from apps.connectors.base.exceptions import InvalidExternalAccountError
from apps.dashboard.models import ProfileSnapshot


User = get_user_model()


class AuthEndpointsTests(APITestCase):
    def test_user_registration_success(self):
        payload = {
            "username": "niamur",
            "email": "niamur@example.com",
            "full_name": "Niamur Rahman",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }

        response = self.client.post(reverse("accounts-register"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertTrue(User.objects.filter(username="niamur").exists())

        user = User.objects.get(username="niamur")
        self.assertEqual(user.email, "niamur@example.com")
        self.assertEqual(user.full_name, "Niamur Rahman")
        self.assertTrue(user.check_password("StrongPassword123!"))

    def test_password_mismatch_error(self):
        payload = {
            "username": "mismatch_user",
            "email": "mismatch@example.com",
            "full_name": "Mismatch User",
            "password": "StrongPassword123!",
            "password_confirm": "DifferentPassword123!",
        }

        response = self.client.post(reverse("accounts-register"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)
        self.assertFalse(User.objects.filter(username="mismatch_user").exists())

    def test_duplicate_email_error(self):
        User.objects.create_user(
            username="existing_user",
            email="niamur@example.com",
            password="StrongPassword123!",
        )
        payload = {
            "username": "new_user",
            "email": "NIAMUR@example.com",
            "full_name": "New User",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }

        response = self.client.post(reverse("accounts-register"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_login_success(self):
        User.objects.create_user(
            username="login_user",
            email="login@example.com",
            password="StrongPassword123!",
        )

        response = self.client.post(
            reverse("accounts-login"),
            {"username": "login_user", "password": "StrongPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_authenticated_me_endpoint_works(self):
        user = User.objects.create_user(
            username="me_user",
            email="me@example.com",
            password="StrongPassword123!",
            full_name="Me User",
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("accounts-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], user.username)
        self.assertEqual(response.data["email"], user.email)
        self.assertEqual(response.data["full_name"], user.full_name)

    def test_unauthenticated_me_endpoint_fails(self):
        response = self.client.get(reverse("accounts-me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_profile_update_works(self):
        user = User.objects.create_user(
            username="profile_user",
            email="profile@example.com",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            reverse("accounts-me-update"),
            {
                "bio": "Competitive programmer and Kaggle learner",
                "country": "Bangladesh",
                "institution": "My University",
                "github_url": "https://github.com/example",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bio"], "Competitive programmer and Kaggle learner")
        self.assertEqual(response.data["country"], "Bangladesh")
        self.assertEqual(response.data["institution"], "My University")
        self.assertEqual(response.data["github_url"], "https://github.com/example")


class ExternalAccountConnectTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username="connector_user",
			email="connector@example.com",
			password="strong-pass-123",
		)
		self.client.force_authenticate(user=self.user)

	@patch("apps.connectors.providers.codeforces.client.CodeforcesApiClient.get_user_info")
	def test_connect_codeforces_invalid_handle(self, mocked_get_user_info):
		mocked_get_user_info.side_effect = InvalidExternalAccountError("Codeforces handle was not found.")

		response = self.client.post(
			reverse("accounts-connect"),
			{"source": "codeforces", "handle_or_slug": "invalid-handle"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("handle_or_slug", response.data)
		self.assertEqual(ExternalAccount.objects.count(), 0)

	@patch("apps.connectors.providers.codeforces.client.CodeforcesApiClient.get_user_info")
	def test_connect_codeforces_success(self, mocked_get_user_info):
		mocked_get_user_info.return_value = {
			"handle": "tourist",
			"firstName": "Gennady",
			"lastName": "Korotkevich",
			"rank": "legendary grandmaster",
			"rating": 3900,
			"maxRating": 3900,
			"titlePhoto": "https://example.com/avatar.png",
		}

		response = self.client.post(
			reverse("accounts-connect"),
			{"source": "codeforces", "handle_or_slug": "tourist"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(ExternalAccount.objects.count(), 1)
		self.assertEqual(ProfileSnapshot.objects.count(), 1)

		account = ExternalAccount.objects.get()
		self.assertEqual(account.source, ExternalAccount.Source.CODEFORCES)
		self.assertEqual(account.verification_status, ExternalAccount.VerificationStatus.VERIFIED)
		self.assertEqual(account.sync_status, ExternalAccount.SyncStatus.SUCCESS)
