from copy import deepcopy
import threading
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from apps.hackathons.models import HackathonAchievement, HackathonEvent, HackathonParticipation, HackathonProject, HackathonSubmission
from apps.hackathons.test_devpost import ACCOUNTS, ROOT, sample_document


class VisibilityAPITests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="publisher", email="publisher@example.com", password="pass12345")
        self.other = user_model.objects.create_user(username="other-publisher", email="other-publisher@example.com", password="pass12345")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.project = HackathonProject.objects.create(owner=self.user, title="Manual project")
        self.event = HackathonEvent.objects.create(owner=self.user, name="Manual event")
        self.participation = HackathonParticipation.objects.create(user=self.user, event=self.event)

    def project_url(self, project=None):
        return f"/api/v1/hackathons/projects/{(project or self.project).pk}/visibility/"

    def participation_url(self):
        return f"/api/v1/hackathons/participations/{self.participation.pk}/visibility/"

    def test_manual_project_and_participation_publish_and_unpublish(self):
        for url, model in ((self.project_url(), self.project), (self.participation_url(), self.participation)):
            with self.subTest(url=url):
                self.assertFalse(model.is_public)
                for value in (True, True, False):
                    response = self.client.patch(url, {"is_public": value}, format="json")
                    self.assertEqual(response.status_code, 200, response.data)
                    self.assertEqual(response.data, {"id": model.pk, "is_public": value})
                    model.refresh_from_db()
                    self.assertEqual(model.is_public, value)

    def test_strict_validation_authentication_and_owner_scope(self):
        for url in (self.project_url(), self.participation_url()):
            for payload in ({}, {"is_public": "true"}, {"is_public": 1}, {"is_public": None},
                            {"is_public": True, "source": "manual"}):
                with self.subTest(url=url, payload=payload):
                    self.assertEqual(self.client.patch(url, payload, format="json").status_code, 400)
            self.assertEqual(self.client.patch(url, {"is_public": True}, format="json").status_code, 200)
        other_client = APIClient()
        other_client.force_authenticate(self.other)
        self.assertEqual(other_client.patch(self.project_url(), {"is_public": False}, format="json").status_code, 404)
        self.assertEqual(other_client.patch(self.participation_url(), {"is_public": False}, format="json").status_code, 404)
        self.assertEqual(self.client.patch("/api/v1/hackathons/projects/999999/visibility/", {"is_public": True}, format="json").status_code, 404)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.patch(self.project_url(), {"is_public": False}, format="json").status_code, 401)

    def test_verified_context_can_change_visibility_without_editing_claim(self):
        submission = HackathonSubmission.objects.create(owner=self.user, project=self.project, event=self.event, status="submitted")
        achievement = HackathonAchievement.objects.create(
            participation=self.participation, submission=submission,
            achievement_type="award", title="Verified award", verification_status="verified")
        self.assertEqual(self.client.patch(self.project_url(), {"is_public": True}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(self.participation_url(), {"is_public": True}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(f"/api/v1/hackathons/events/{self.event.pk}/", {"name": "Changed"}, format="json").status_code, 403)
        achievement.refresh_from_db()
        self.assertEqual(achievement.verification_status, "verified")
        self.assertEqual(achievement.title, "Verified award")

    def test_imported_project_visibility_survives_reimport(self):
        self.assertEqual(self.client.post(ACCOUNTS, {"platform": "devpost", "handle": "example_user"}, format="json").status_code, 201)
        document = sample_document()
        token = self.client.post(ROOT + "preview/", document, format="json").data["preview_token"]
        self.assertEqual(self.client.post(ROOT, {"document": document, "preview_token": token}, format="json").status_code, 200)
        imported = HackathonProject.objects.get(owner=self.user, source="devpost")
        self.assertFalse(imported.is_public)
        imported_id = imported.external_id
        self.assertEqual(self.client.patch(self.project_url(imported), {"is_public": True}, format="json").status_code, 200)
        changed = deepcopy(document)
        changed["projects"][0]["title"] = "Updated from import"
        plan = self.client.post(ROOT + "preview/", changed, format="json").data
        self.assertEqual(self.client.post(ROOT, {"document": changed, "preview_token": plan["preview_token"]}, format="json").status_code, 200)
        imported.refresh_from_db()
        self.assertEqual((imported.title, imported.is_public, imported.external_id), ("Updated from import", True, imported_id))
        self.assertEqual(self.client.patch(self.project_url(imported), {"title": "Manual override"}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(self.project_url(imported), {"is_public": False}, format="json").status_code, 200)
        changed["projects"][0]["title"] = "Updated again"
        plan = self.client.post(ROOT + "preview/", changed, format="json").data
        self.assertEqual(self.client.post(ROOT, {"document": changed, "preview_token": plan["preview_token"]}, format="json").status_code, 200)
        imported.refresh_from_db()
        self.assertEqual((imported.title, imported.is_public, imported.external_id), ("Updated again", False, imported_id))


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locks are required")
class ConcurrentVisibilityImportTests(TransactionTestCase):
    def test_visibility_and_import_serialize_without_losing_publication(self):
        user = get_user_model().objects.create_user(username="race-publisher", email="race-publisher@example.com", password="pass12345")
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.post(ACCOUNTS, {"platform": "devpost", "handle": "example_user"}, format="json").status_code, 201)
        document = sample_document()
        token = client.post(ROOT + "preview/", document, format="json").data["preview_token"]
        self.assertEqual(client.post(ROOT, {"document": document, "preview_token": token}, format="json").status_code, 200)
        project = HackathonProject.objects.get(owner=user, source="devpost")
        changed = deepcopy(document)
        changed["projects"][0]["title"] = "Updated during race"
        token = client.post(ROOT + "preview/", changed, format="json").data["preview_token"]
        start = threading.Barrier(3)
        results = []
        failures = []

        def request_in_thread(kind):
            close_old_connections()
            try:
                thread_client = APIClient()
                thread_client.force_authenticate(user)
                start.wait(timeout=10)
                if kind == "visibility":
                    response = thread_client.patch(f"/api/v1/hackathons/projects/{project.pk}/visibility/", {"is_public": True}, format="json")
                else:
                    response = thread_client.post(ROOT, {"document": changed, "preview_token": token}, format="json")
                results.append((kind, response.status_code))
            except Exception as exc:
                failures.append(exc)
            finally:
                connections.close_all()

        threads = [threading.Thread(target=request_in_thread, args=(kind,)) for kind in ("visibility", "import")]
        for thread in threads:
            thread.start()
        start.wait(timeout=10)
        for thread in threads:
            thread.join(timeout=20)
        self.assertFalse(failures, failures)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(dict(results)["visibility"], 200)
        self.assertIn(dict(results)["import"], (200, 409))
        project.refresh_from_db()
        self.assertTrue(project.is_public)
        if dict(results)["import"] == 200:
            self.assertEqual(project.title, "Updated during race")
        else:
            retry_token = client.post(ROOT + "preview/", changed, format="json").data["preview_token"]
            self.assertEqual(client.post(ROOT, {"document": changed, "preview_token": retry_token}, format="json").status_code, 200)
            project.refresh_from_db()
            self.assertEqual(project.title, "Updated during race")
            self.assertTrue(project.is_public)
