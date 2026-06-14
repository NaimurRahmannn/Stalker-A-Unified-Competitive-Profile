from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


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
