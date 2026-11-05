import threading
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from apps.hackathons.models import HackathonAchievement, HackathonDuplicateReview, HackathonEvent, HackathonParticipation, HackathonProject, HackathonSubmission


ROOT = "/api/v1/hackathons/duplicate-reviews/"


class DuplicateReviewAPITests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="review-owner", email="review-owner@example.com", password="pass12345")
        self.other = user_model.objects.create_user(username="review-other", email="review-other@example.com", password="pass12345")
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        self.manual = HackathonProject.objects.create(owner=self.owner, title="Manual build", repository_url="https://github.com/example/shared")
        self.imported = HackathonProject.objects.create(owner=self.owner, title="Imported build", source="devpost",
            external_id="shared-build", project_url="https://devpost.com/software/shared-build",
            repository_url="https://github.com/example/shared")
        self.manual_event = HackathonEvent.objects.create(owner=self.owner, name="Manual event", event_url="https://shared-event.devpost.com/")
        self.imported_event = HackathonEvent.objects.create(owner=self.owner, name="Imported event", source="devpost",
            external_id="shared-event", event_url="https://shared-event.devpost.com/")
        self.participation = HackathonParticipation.objects.create(user=self.owner, event=self.manual_event)
        self.submission = HackathonSubmission.objects.create(owner=self.owner, project=self.manual, event=self.manual_event, status="submitted")
        self.achievement = HackathonAchievement.objects.create(participation=self.participation, submission=self.submission,
            achievement_type="award", title="Verified award", verification_status="verified")

    def payload(self, kind="project", decision="related"):
        manual, imported = ((self.manual, self.imported) if kind == "project" else (self.manual_event, self.imported_event))
        return {"record_type": kind, "manual_id": manual.pk, "imported_id": imported.pk, "decision": decision}

    def test_candidates_decisions_and_invariant_records(self):
        listing = self.client.get(ROOT)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual({row["record_type"] for row in listing.data["candidates"]}, {"project", "event"})
        self.assertEqual(listing.data["reviews"]["count"], 0)
        self.assertTrue(all(row["decision"] == "unresolved" for row in listing.data["candidates"]))
        response = self.client.post(ROOT, self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        review_id = response.data["id"]
        first_updated = HackathonDuplicateReview.objects.get(pk=review_id).updated_at
        self.assertEqual(self.client.post(ROOT, self.payload(), format="json").status_code, 200)
        self.assertEqual(HackathonDuplicateReview.objects.count(), 1)
        self.assertEqual(HackathonDuplicateReview.objects.get(pk=review_id).updated_at, first_updated)
        self.assertEqual(self.client.patch(ROOT + f"{review_id}/", {"decision": "distinct"}, format="json").data["decision"], "distinct")
        self.assertEqual(self.client.patch(ROOT + f"{review_id}/", {"decision": "unresolved"}, format="json").data["decision"], "unresolved")
        self.assertEqual(self.client.post(ROOT, self.payload("event"), format="json").status_code, 201)
        self.manual.refresh_from_db(); self.imported.refresh_from_db(); self.achievement.refresh_from_db(); self.submission.refresh_from_db()
        self.assertEqual((self.manual.title, self.imported.title, self.imported.external_id),
                         ("Manual build", "Imported build", "shared-build"))
        self.assertEqual(self.submission.project_id, self.manual.pk)
        self.assertEqual(self.achievement.verification_status, "verified")
        self.assertFalse(self.manual.is_public)
        self.assertFalse(self.imported.is_public)
        public = self.client.get("/api/v1/profile/review-owner/hackathons/").data
        self.assertNotIn("duplicate", str(public).lower())

    def test_owner_scope_source_checks_and_deletion(self):
        review = self.client.post(ROOT, self.payload(), format="json").data
        other_manual = HackathonProject.objects.create(owner=self.other, title="Other manual", repository_url=self.imported.repository_url)
        other_client = APIClient(); other_client.force_authenticate(self.other)
        self.assertEqual(other_client.patch(ROOT + f"{review['id']}/", {"decision": "distinct"}, format="json").status_code, 404)
        self.assertEqual(other_client.post(ROOT, self.payload(), format="json").status_code, 404)
        self.assertEqual(self.client.post(ROOT, {**self.payload(), "manual_id": other_manual.pk}, format="json").status_code, 404)
        self.assertEqual(self.client.post(ROOT, {**self.payload(), "manual_id": self.imported.pk}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT, {**self.payload(), "imported_id": self.manual.pk}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT, {**self.payload(), "manual_id": self.imported.pk, "imported_id": self.imported.pk}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT, {**self.payload(), "record_type": "submission"}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(ROOT + f"{review['id']}/", {"decision": "verified"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT, {**self.payload(), "owner": self.other.pk}, format="json").status_code, 400)
        unmatched = HackathonProject.objects.create(owner=self.owner, title="Different manual")
        self.assertEqual(self.client.post(ROOT, {**self.payload(), "imported_id": unmatched.pk}, format="json").status_code, 404)
        self.assertEqual(self.client.post(ROOT, {**self.payload(), "manual_id": unmatched.pk}, format="json").status_code, 400)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(ROOT).status_code, 401)
        self.client.force_authenticate(self.owner)
        self.imported.delete()
        self.assertEqual(HackathonDuplicateReview.objects.filter(pk=review["id"]).count(), 0)

    def test_url_candidates_normalize_safe_parts_without_conflating_query(self):
        self.manual.repository_url = "http://GITHUB.COM/example/shared/"
        self.manual.save(update_fields=("repository_url",))
        listing = self.client.get(ROOT)
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(any(row["record_type"] == "project" for row in listing.data["candidates"]))
        self.assertEqual(self.client.post(ROOT, self.payload(), format="json").status_code, 201)

        self.manual.repository_url = "https://github.com/example/shared?branch=other"
        self.manual.save(update_fields=("repository_url",))
        listing = self.client.get(ROOT)
        self.assertFalse(any(row["record_type"] == "project" for row in listing.data["candidates"]))


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locks are required")
class ConcurrentDuplicateReviewTests(TransactionTestCase):
    def test_concurrent_decisions_create_one_pair(self):
        user = get_user_model().objects.create_user(username="review-race", email="review-race@example.com", password="pass12345")
        manual = HackathonProject.objects.create(owner=user, title="Manual", repository_url="https://github.com/example/race")
        imported = HackathonProject.objects.create(owner=user, title="Imported", source="devpost", external_id="race",
            repository_url="https://github.com/example/race")
        payload = {"record_type": "project", "manual_id": manual.pk, "imported_id": imported.pk, "decision": "related"}
        barrier = threading.Barrier(3)
        results, errors = [], []

        def send():
            close_old_connections()
            try:
                client = APIClient(); client.force_authenticate(user)
                barrier.wait(timeout=10)
                response = client.post(ROOT, payload, format="json")
                results.append(response.status_code)
            except Exception as exc:
                errors.append(exc)
            finally:
                connections.close_all()

        threads = [threading.Thread(target=send) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait(timeout=10)
        for thread in threads:
            thread.join(timeout=20)
        self.assertFalse(errors, errors)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(sorted(results), [200, 201])
        self.assertEqual(HackathonDuplicateReview.objects.filter(owner=user).count(), 1)
