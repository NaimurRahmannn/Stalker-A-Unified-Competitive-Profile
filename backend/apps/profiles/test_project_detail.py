from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.hackathons.models import HackathonAchievement, HackathonEvent, HackathonParticipation, HackathonProject, HackathonSubmission


class PublicProjectDetailTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="detail-owner", email="detail-owner@example.com", password="pass12345")
        self.other = user_model.objects.create_user(username="detail-other", email="detail-other@example.com", password="pass12345")
        self.client = APIClient()
        self.project = HackathonProject.objects.create(owner=self.owner, title="Published build", description="Full description",
            technologies=["Python"], is_public=True, project_url="https://devpost.com/software/published-build")
        self.private_project = HackathonProject.objects.create(owner=self.owner, title="Private build")
        self.public_event = HackathonEvent.objects.create(owner=self.owner, name="Published event")
        self.private_event = HackathonEvent.objects.create(owner=self.owner, name="Hidden event")
        self.public_participation = HackathonParticipation.objects.create(user=self.owner, event=self.public_event, is_public=True)
        self.private_participation = HackathonParticipation.objects.create(user=self.owner, event=self.private_event, is_public=False)
        self.visible_submission = HackathonSubmission.objects.create(owner=self.owner, project=self.project, event=self.public_event,
            status="submitted", submission_url="https://example.com/submission")
        HackathonSubmission.objects.create(owner=self.owner, project=self.project, event=self.private_event, status="submitted",
            submission_url="https://example.com/private-submission")
        draft_event = HackathonEvent.objects.create(owner=self.owner, name="Draft event")
        HackathonParticipation.objects.create(user=self.owner, event=draft_event, is_public=True)
        HackathonSubmission.objects.create(owner=self.owner, project=self.project, event=draft_event, status="draft")
        HackathonAchievement.objects.create(participation=self.public_participation, submission=self.visible_submission,
            achievement_type="award", title="Visible award", verification_status="verified")
        HackathonAchievement.objects.create(participation=self.private_participation, achievement_type="award", title="Hidden award")

    def url(self, project=None, username="detail-owner"):
        return f"/api/v1/profile/{username}/hackathons/projects/{(project or self.project).pk}/"

    def test_anonymous_detail_only_contains_eligible_relationships(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 12)
        self.assertEqual(response.data["project"]["title"], "Published build")
        self.assertEqual(response.data["submission_count"], 1)
        self.assertEqual(response.data["achievement_count"], 1)
        self.assertEqual(response.data["submissions"][0]["event_name"], "Published event")
        self.assertEqual(response.data["achievements"][0]["verification_status"], "verified")
        payload = str(response.data)
        for hidden in ("Hidden event", "Hidden award", "Draft event", "private-submission", "external_id", "evidence_url", "preview_token"):
            self.assertNotIn(hidden, payload)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url()).data, response.data)

    def test_private_wrong_owner_and_missing_projects_return_404(self):
        self.assertEqual(self.client.get(self.url(self.private_project)).status_code, 404)
        self.assertEqual(self.client.get(self.url(username="detail-other")).status_code, 404)
        self.assertEqual(self.client.get(self.url(username="missing-user")).status_code, 404)
        self.assertEqual(self.client.get("/api/v1/profile/detail-owner/hackathons/projects/999999/").status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(f"/api/v1/hackathons/projects/{self.project.pk}/visibility/", {"is_public": False}, format="json").status_code, 200)
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_imported_project_and_participation_visibility_remain_independent(self):
        imported = HackathonProject.objects.create(owner=self.owner, title="Imported build", is_public=True,
            source="devpost", external_id="imported-build", project_url="https://devpost.com/software/imported-build")
        response = self.client.get(self.url(imported))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["project"]["source"], "devpost")
        self.assertEqual(response.data["submissions"], [])
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(f"/api/v1/hackathons/participations/{self.public_participation.pk}/visibility/",
            {"is_public": False}, format="json").status_code, 200)
        response = self.client.get(self.url())
        self.assertEqual(response.data["project"]["title"], "Published build")
        self.assertEqual(response.data["submissions"], [])
        self.assertEqual(response.data["achievements"], [])
