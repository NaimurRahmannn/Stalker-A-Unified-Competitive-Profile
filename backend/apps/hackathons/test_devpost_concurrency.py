"""PostgreSQL-only proof that simultaneous apply requests share one result."""

import threading
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from apps.connectors.models import PlatformAccount
from apps.hackathons.models import DevpostImportRun, HackathonEvent, HackathonParticipation, HackathonProject, HackathonSubmission
from apps.hackathons.services.devpost.import_service import preview
from apps.hackathons.services.devpost.schema import normalize
from apps.hackathons.test_devpost import sample_document


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locks are required")
class ConcurrentDevpostApplyTests(TransactionTestCase):
    def test_concurrent_apply_reuses_one_completed_run(self):
        user = get_user_model().objects.create_user(username="concurrent-devpost", email="concurrent-devpost@example.com", password="pass12345")
        account = PlatformAccount.objects.create(user=user, platform="devpost", handle="example_user", profile_url="https://devpost.com/example_user")
        document = sample_document()
        token = preview(user, account, normalize(document, account.handle))["preview_token"]
        start = threading.Barrier(3)
        statuses = []
        failures = []

        def apply_in_thread():
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(user)
                start.wait(timeout=10)
                response = client.post("/api/v1/hackathons/devpost/imports/", {"document": document, "preview_token": token}, format="json")
                statuses.append((response.status_code, response.data.get("id")))
            except Exception as exc:
                failures.append(exc)
            finally:
                connections.close_all()

        threads = [threading.Thread(target=apply_in_thread) for _ in range(2)]
        for thread in threads:
            thread.start()
        try:
            start.wait(timeout=10)
        finally:
            for thread in threads:
                thread.join(timeout=15)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertFalse(failures, failures)
        self.assertEqual(len(statuses), 2)
        self.assertEqual(statuses[0], statuses[1])
        self.assertEqual(statuses[0][0], 200)
        self.assertEqual((DevpostImportRun.objects.count(), HackathonEvent.objects.count(), HackathonParticipation.objects.count(), HackathonProject.objects.count(), HackathonSubmission.objects.count()), (1, 1, 1, 1, 1))
