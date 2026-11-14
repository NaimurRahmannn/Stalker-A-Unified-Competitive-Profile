from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.dashboard.clist_events import CACHE_KEY, normalize_clist_events


class DashboardClistEventsTests(APITestCase):
    url = "/api/v1/dashboard/events/"

    def setUp(self):
        cache.delete(CACHE_KEY)
        cache.delete(f"{CACHE_KEY}:2")
        self.user = get_user_model().objects.create_user(
            username="contest_viewer", email="contests@example.com", password="StrongPassword123!"
        )

    def tearDown(self):
        cache.delete(CACHE_KEY)
        cache.delete(f"{CACHE_KEY}:2")

    def test_events_require_authentication(self):
        with patch("apps.dashboard.clist_events.requests.get") as provider:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        provider.assert_not_called()

    @override_settings(CLIST_API="", CLIST_USERNAME="")
    def test_missing_credentials_return_safe_unavailable_state(self):
        self.client.force_authenticate(self.user)
        with patch("apps.dashboard.clist_events.requests.get") as provider:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["events"], [])
        self.assertEqual(response.data["reason"], "not_configured")
        provider.assert_not_called()

    @override_settings(CLIST_API="test-key", CLIST_USERNAME="test-user")
    def test_events_are_normalized_and_cached_without_exposing_credentials(self):
        self.client.force_authenticate(self.user)
        now = timezone.now()
        future = (now + timedelta(hours=2)).replace(tzinfo=None).isoformat()
        later = (now + timedelta(hours=4)).replace(tzinfo=None).isoformat()
        past = (now - timedelta(hours=1)).replace(tzinfo=None).isoformat()
        payload = {"objects": [
            {"id": 1, "event": "Upcoming contest", "resource": "example.org", "start": future, "end": later, "href": "https://example.org/contest"},
            {"id": 2, "event": "Live contest", "resource": "another.org", "start": past, "end": later, "href": "https://another.org/live"},
            {"id": 3, "event": "Unsafe link", "resource": "bad.org", "start": future, "end": later, "href": "javascript:alert(1)"},
        ]}
        upstream = Mock(status_code=200)
        upstream.json.return_value = payload

        with patch("apps.dashboard.clist_events.requests.get", return_value=upstream) as provider:
            first = self.client.get(self.url)
            second = self.client.get(self.url)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data, second.data)
        self.assertEqual([event["id"] for event in first.data["events"]], [2, 1])
        self.assertTrue(first.data["events"][0]["ongoing"])
        self.assertNotIn("test-key", str(first.data))
        self.assertNotIn("test-user", str(first.data))
        provider.assert_called_once()
        self.assertEqual(provider.call_args.kwargs["headers"]["Authorization"], "ApiKey test-user:test-key")
        self.assertEqual(provider.call_args.kwargs["params"]["upcoming"], "true")

    @override_settings(CLIST_API="test-key", CLIST_USERNAME="test-user")
    def test_upstream_failure_returns_safe_error(self):
        self.client.force_authenticate(self.user)
        with patch("apps.dashboard.clist_events.requests.get", return_value=Mock(status_code=401)):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, {
            "status": "unavailable", "events": [], "reason": "provider_unavailable",
        })

    @override_settings(CLIST_API="test-key", CLIST_USERNAME="test-user")
    def test_contest_pages_use_distinct_offsets_and_cache_entries(self):
        self.client.force_authenticate(self.user)
        start = (timezone.now() + timedelta(hours=1)).isoformat()
        end = (timezone.now() + timedelta(hours=2)).isoformat()
        rows = [
            {"id": index, "event": f"Contest {index}", "resource": "example.org", "start": start, "end": end, "href": f"https://example.org/{index}"}
            for index in range(1, 52)
        ]
        first_page = Mock(status_code=200)
        first_page.json.return_value = {"objects": rows}
        second_page = Mock(status_code=200)
        second_page.json.return_value = {"objects": rows[50:]}

        with patch("apps.dashboard.clist_events.requests.get", side_effect=[first_page, second_page]) as provider:
            first = self.client.get(self.url)
            second = self.client.get(f"{self.url}?page=2")
            repeated = self.client.get(f"{self.url}?page=2")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first.data["events"]), 50)
        self.assertEqual(first.data["next_page"], 2)
        self.assertEqual(second.status_code, 200)
        self.assertEqual([row["id"] for row in second.data["events"]], [51])
        self.assertIsNone(second.data["next_page"])
        self.assertEqual(second.data, repeated.data)
        self.assertEqual(provider.call_count, 2)
        self.assertEqual(provider.call_args_list[0].kwargs["params"]["limit"], 51)
        self.assertEqual(provider.call_args_list[0].kwargs["params"]["offset"], 0)
        self.assertEqual(provider.call_args_list[1].kwargs["params"]["offset"], 50)

    @override_settings(CLIST_API="test-key", CLIST_USERNAME="test-user")
    def test_invalid_page_is_rejected_without_fetching_clist(self):
        self.client.force_authenticate(self.user)
        with patch("apps.dashboard.clist_events.requests.get") as provider:
            for page in ("0", "201", "abc", "9" * 5000):
                response = self.client.get(f"{self.url}?page={page}")
                self.assertEqual(response.status_code, 400)
        provider.assert_not_called()

    def test_normalizer_discards_ended_and_duplicate_contests(self):
        now = timezone.now()
        start = (now + timedelta(hours=1)).isoformat()
        end = (now + timedelta(hours=2)).isoformat()
        ended = (now - timedelta(hours=1)).isoformat()
        valid = {"id": 8, "event": "Future", "resource": "site.org", "start": start, "end": end, "href": "https://site.org/8"}
        result = normalize_clist_events({"objects": [
            valid, valid, {**valid, "id": 9, "end": ended},
        ]}, now=now)
        self.assertEqual([event["id"] for event in result], [8])
