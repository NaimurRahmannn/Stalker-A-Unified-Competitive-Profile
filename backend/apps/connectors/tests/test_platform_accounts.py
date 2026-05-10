from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.connectors.models import PlatformAccount


User = get_user_model()


class PlatformAccountAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="niamur",
            email="niamur@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPassword123!",
        )
        self.list_url = reverse("platform-account-list")

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_can_create_platform_account(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {"platform": "codeforces", "handle": "niamur"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["platform"], "codeforces")
        self.assertEqual(response.data["handle"], "niamur")
        self.assertEqual(response.data["profile_url"], "")
        self.assertFalse(response.data["is_verified"])
        self.assertIsNone(response.data["last_synced_at"])
        self.assertEqual(PlatformAccount.objects.get().user, self.user)

    def test_unauthenticated_user_cannot_create_platform_account(self):
        response = self.client.post(
            self.list_url,
            {"platform": "codeforces", "handle": "niamur"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(PlatformAccount.objects.count(), 0)

    def test_authenticated_user_can_list_only_their_own_platform_accounts(self):
        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="niamur",
        )
        PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.ATCODER,
            handle="tourist",
        )
        self.authenticate()

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["handle"], "niamur")

    def test_user_cannot_access_another_users_platform_account(self):
        account = PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )
        self.authenticate()

        response = self.client.get(reverse("platform-account-detail", args=[account.pk]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_add_same_platform_twice(self):
        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="niamur",
        )
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {"platform": "codeforces", "handle": "another_handle"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("platform", response.data)
        self.assertEqual(PlatformAccount.objects.filter(user=self.user).count(), 1)

    def test_user_can_update_their_handle(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="niamur",
        )
        self.authenticate()

        response = self.client.patch(
            reverse("platform-account-detail", args=[account.pk]),
            {"handle": "new_handle"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["handle"], "new_handle")
        account.refresh_from_db()
        self.assertEqual(account.handle, "new_handle")

    def test_user_can_delete_their_platform_account(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="niamur",
        )
        self.authenticate()

        response = self.client.delete(reverse("platform-account-detail", args=[account.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PlatformAccount.objects.filter(pk=account.pk).exists())

    def test_invalid_platform_returns_400(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {"platform": "invalid", "handle": "niamur"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("platform", response.data)

    def test_empty_handle_returns_400(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {"platform": "codeforces", "handle": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("handle", response.data)
