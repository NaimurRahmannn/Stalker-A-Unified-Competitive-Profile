from copy import deepcopy

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.hackathons.models import DevpostImportRun, HackathonAchievement, HackathonEvent, HackathonProject, HackathonSubmission
from apps.hackathons.test_devpost import ACCOUNTS, ROOT, sample_document


class ImportChangePreviewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="diff-owner", email="diff-owner@example.com", password="pass12345")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(ACCOUNTS, {"platform": "devpost", "handle": "example_user"}, format="json").status_code, 201)

    def preview(self, document):
        response = self.client.post(ROOT + "preview/", document, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def apply(self, document, plan):
        return self.client.post(ROOT, {"document": document, "preview_token": plan["preview_token"]}, format="json")

    def test_create_update_unchanged_and_bounded_changes(self):
        document = sample_document()
        before = (HackathonProject.objects.count(), HackathonEvent.objects.count(), DevpostImportRun.objects.count())
        first = self.preview(document)
        self.assertEqual(first["action_counts"]["create"], 4)
        self.assertEqual(first["projects"][0]["changes"], [])
        self.assertEqual(before, (HackathonProject.objects.count(), HackathonEvent.objects.count(), DevpostImportRun.objects.count()))
        self.assertEqual(self.apply(document, first).status_code, 200)
        project = HackathonProject.objects.get(owner=self.user, source="devpost")
        project.is_public = True
        project.save(update_fields=("is_public", "updated_at"))
        changed = deepcopy(document)
        changed["projects"][0]["title"] = "Updated title"
        changed["projects"][0]["description"] = "A" * 500
        changed["projects"][0]["technologies"] = ["Python", "Rust"]
        changed["projects"][0]["submissions"][0]["status"] = "withdrawn"
        plan = self.preview(changed)
        self.assertEqual(plan["projects"][0]["action"], "update")
        fields = {row["field"]: row for row in plan["projects"][0]["changes"]}
        self.assertEqual(fields["title"]["before"], "Smart City AI")
        self.assertEqual(fields["title"]["after"], "Updated title")
        self.assertEqual(fields["technologies"]["after"], ["Python", "Rust"])
        self.assertTrue(fields["description"]["truncated"])
        self.assertLessEqual(len(fields["description"]["after"]), 240)
        self.assertEqual(plan["projects"][0]["submissions"][0]["changes"][0]["field"], "status")
        self.assertNotIn("is_public", str(plan["projects"][0]["changes"]))
        self.assertEqual(self.apply(changed, plan).status_code, 200)
        project.refresh_from_db()
        self.assertTrue(project.is_public)
        self.assertEqual(self.preview(changed)["projects"][0]["action"], "unchanged")

    def test_protection_conflict_and_stale_preview(self):
        document = sample_document()
        first = self.preview(document)
        self.assertEqual(self.apply(document, first).status_code, 200)
        project = HackathonProject.objects.get(owner=self.user, source="devpost")
        submission = HackathonSubmission.objects.get(owner=self.user, source="devpost")
        achievement = HackathonAchievement.objects.create(participation=submission.event.participations.get(user=self.user),
            submission=submission, achievement_type="award", title="Verified award", verification_status="verified")
        changed = deepcopy(document)
        changed["projects"][0]["title"] = "Changed under verification"
        plan = self.preview(changed)
        self.assertEqual(plan["projects"][0]["action"], "protected")
        self.assertIn("verified achievement", plan["projects"][0]["reason"])
        self.assertEqual(plan["projects"][0]["changes"][0]["field"], "title")
        self.assertEqual(self.apply(changed, plan).status_code, 200)
        project.refresh_from_db(); achievement.refresh_from_db()
        self.assertEqual(project.title, "Smart City AI")
        self.assertEqual(achievement.verification_status, "verified")
        changed["projects"][0]["description"] = "A newer import description"
        stale = self.preview(changed)
        HackathonProject.objects.filter(pk=project.pk).update(description="admin correction")
        self.assertEqual(self.apply(changed, stale).status_code, 409)
        self.assertEqual(self.apply(changed, {"preview_token": stale["preview_token"] + "bad"}).status_code, 409)
