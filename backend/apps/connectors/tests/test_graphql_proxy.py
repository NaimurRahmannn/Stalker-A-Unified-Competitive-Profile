from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class LeetCodeGraphQLProxyViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("leetcode-graphql-proxy")
        self.sample_query = "query getUserProfile($username: String!) { matchedUser(username: $username) { username } }"
        self.sample_variables = {"username": "Niamur_Rahmann"}

    def test_requires_query_field(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Field 'query' is required", response.data["detail"])

    def test_variables_must_be_dict(self):
        response = self.client.post(
            self.url,
            {"query": self.sample_query, "variables": "invalid"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Field 'variables' must be an object", response.data["detail"])

    @patch("apps.connectors.leetcode_proxy.LeetCodeGraphQLProxy._fetch_upstream")
    def test_executes_query_and_caches_result(self, mock_fetch):
        mock_fetch.return_value = {
            "data": {
                "matchedUser": {
                    "username": "Niamur_Rahmann",
                    "profile": {"realName": "Naimur Rahman Lam"},
                }
            }
        }

        # 1st Request: Cache MISS
        resp1 = self.client.post(
            self.url,
            {"query": self.sample_query, "variables": self.sample_variables},
            format="json",
        )
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        self.assertEqual(resp1.headers.get("X-Cache"), "MISS")
        self.assertEqual(resp1.data["data"]["matchedUser"]["username"], "Niamur_Rahmann")
        self.assertEqual(mock_fetch.call_count, 1)

        # 2nd Request: Cache HIT
        resp2 = self.client.post(
            self.url,
            {"query": self.sample_query, "variables": self.sample_variables},
            format="json",
        )
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertEqual(resp2.headers.get("X-Cache"), "HIT")
        self.assertEqual(resp2.data["data"]["matchedUser"]["username"], "Niamur_Rahmann")
        # Upstream should NOT be called again
        self.assertEqual(mock_fetch.call_count, 1)
