from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.hackathons.models import (
    HackathonAchievement, HackathonEvent, HackathonParticipation,
    HackathonProject, HackathonSubmission,
)


class PublicHackathonProfileTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="portfolio", email="portfolio@example.com", password="pass12345")
        self.other = user_model.objects.create_user(username="portfolio-other", email="portfolio-other@example.com", password="pass12345")
        self.client = APIClient()
        self.url = "/api/v1/profile/portfolio/hackathons/"
        self.public_project = HackathonProject.objects.create(owner=self.user, title="Visible project", description="Public description", is_public=True,
            repository_url="https://github.com/example/visible", technologies=["Python", "React"])
        self.private_project = HackathonProject.objects.create(owner=self.user, title="Secret project", description="Secret project details", is_public=False)
        self.visible_event = HackathonEvent.objects.create(owner=self.user, name="Visible event")
        self.hidden_event = HackathonEvent.objects.create(owner=self.user, name="Secret event")
        self.public_part = HackathonParticipation.objects.create(user=self.user, event=self.visible_event, is_public=True, team_name="Public team")
        self.private_part = HackathonParticipation.objects.create(user=self.user, event=self.hidden_event, is_public=False, team_name="Secret team")
        self.visible_submission = HackathonSubmission.objects.create(owner=self.user, project=self.public_project, event=self.visible_event, status="submitted")
        self.private_project_submission = HackathonSubmission.objects.create(owner=self.user, project=self.private_project, event=self.visible_event, status="submitted")
        self.hidden_event_submission = HackathonSubmission.objects.create(owner=self.user, project=self.public_project, event=self.hidden_event, status="submitted")
        self.public_award = HackathonAchievement.objects.create(participation=self.public_part, achievement_type="award", title="Self-reported award")
        self.verified_award = HackathonAchievement.objects.create(participation=self.public_part, submission=self.visible_submission,
            achievement_type="placement", title="Verified placement", rank=1, verification_status="verified")
        HackathonAchievement.objects.create(participation=self.public_part, submission=self.private_project_submission,
            achievement_type="award", title="Secret linked award")
        HackathonAchievement.objects.create(participation=self.private_part, achievement_type="award", title="Secret event award")
        HackathonProject.objects.create(owner=self.other, title="Other user's published project", is_public=True)

    def test_anonymous_and_authenticated_public_results_and_summary(self):
        with patch("apps.hackathons.services.devpost.providers.user_json.UserJsonProvider.acquire", side_effect=AssertionError("import called")):
            anonymous = self.client.get(self.url)
            profile = self.client.get("/api/v1/profile/portfolio/")
        self.assertEqual((anonymous.status_code, profile.status_code), (200, 200))
        expected = {"published_projects": 1, "public_participations": 1, "public_achievements": 2, "verified_achievements": 1}
        self.assertEqual(anonymous.data["summary"], expected)
        self.assertEqual(profile.data["hackathons"], expected)
        self.assertEqual([row["title"] for row in anonymous.data["projects"]["results"]], ["Visible project"])
        self.assertEqual([row["event_name"] for row in anonymous.data["projects"]["results"][0]["associations"]], ["Visible event"])
        self.assertEqual([row["event"]["name"] for row in anonymous.data["participations"]["results"]], ["Visible event"])
        self.assertEqual({row["title"] for row in anonymous.data["achievements"]["results"]}, {"Self-reported award", "Verified placement"})
        self.assertEqual({row["verification_status"] for row in anonymous.data["achievements"]["results"]}, {"self_reported", "verified"})
        self.assertEqual([row["project_title"] for row in anonymous.data["submissions"]["results"]], ["Visible project"])
        payload = str(anonymous.data) + str(profile.data["hackathons"])
        for secret in ("Secret project", "Secret event", "Secret team", "Secret linked award", "Secret event award", "Other user's published project"):
            self.assertNotIn(secret, payload)
        for internal in ("external_id", "preview_token", "request_fingerprint", "evidence_url", "email", "import_history"):
            self.assertNotIn(internal, str(anonymous.data))
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url).data, anonymous.data)

    def test_project_and_participation_visibility_are_independent(self):
        self.assertEqual(self.client.get(self.url).data["submissions"]["count"], 1)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.patch(f"/api/v1/hackathons/participations/{self.public_part.pk}/visibility/", {"is_public": False}, format="json").status_code, 200)
        hidden = self.client.get(self.url).data
        self.assertEqual((hidden["projects"]["count"], hidden["participations"]["count"], hidden["achievements"]["count"], hidden["submissions"]["count"]), (1, 0, 0, 0))
        self.assertNotIn("Visible event", str(hidden))
        self.assertEqual(self.client.patch(f"/api/v1/hackathons/participations/{self.public_part.pk}/visibility/", {"is_public": True}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(f"/api/v1/hackathons/projects/{self.public_project.pk}/visibility/", {"is_public": False}, format="json").status_code, 200)
        no_project = self.client.get(self.url).data
        self.assertEqual((no_project["projects"]["count"], no_project["participations"]["count"], no_project["achievements"]["count"], no_project["submissions"]["count"]), (0, 1, 1, 0))
        self.assertNotIn("Visible project", str(no_project))
        self.assertEqual(no_project["summary"]["verified_achievements"], 0)

    def test_empty_unknown_and_bounded_paginated_portfolio(self):
        self.assertEqual(self.client.get("/api/v1/profile/missing/hackathons/").status_code, 404)
        empty_user = get_user_model().objects.create_user(username="empty-portfolio", email="empty-portfolio@example.com", password="pass12345")
        empty = self.client.get(f"/api/v1/profile/{empty_user.username}/hackathons/").data
        self.assertEqual(empty["summary"], {"published_projects": 0, "public_participations": 0, "public_achievements": 0, "verified_achievements": 0})
        self.assertEqual(empty["projects"]["results"], [])
        self.assertEqual(empty["participations"]["results"], [])
        for index in range(25):
            HackathonProject.objects.create(owner=self.user, title=f"Extra {index:02}", is_public=True)
        first = self.client.get(self.url + "?projects_page=1&page_size=100").data
        second = self.client.get(self.url + "?projects_page=2&page_size=100").data
        self.assertEqual((first["projects"]["count"], len(first["projects"]["results"]), len(second["projects"]["results"])), (26, 20, 6))
        ids = [row["id"] for row in first["projects"]["results"] + second["projects"]["results"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(self.client.get(self.url + "?projects_page=999").status_code, 404)

    def test_public_query_count_stays_bounded(self):
        for index in range(12):
            event = HackathonEvent.objects.create(owner=self.user, name=f"Visible {index}")
            HackathonParticipation.objects.create(user=self.user, event=event, is_public=True)
            HackathonProject.objects.create(owner=self.user, title=f"Project {index}", is_public=True)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 20)

    def test_one_project_can_have_multiple_public_submissions_without_duplicate_cards(self):
        second_event = HackathonEvent.objects.create(owner=self.user, name="Second public event")
        HackathonParticipation.objects.create(user=self.user, event=second_event, is_public=True)
        HackathonSubmission.objects.create(owner=self.user, project=self.public_project, event=second_event, status="submitted")
        draft_event = HackathonEvent.objects.create(owner=self.user, name="Draft event")
        HackathonParticipation.objects.create(user=self.user, event=draft_event, is_public=True)
        HackathonSubmission.objects.create(owner=self.user, project=self.public_project, event=draft_event, status="draft")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["projects"]["count"], 1)
        self.assertEqual({row["event_name"] for row in response.data["projects"]["results"][0]["associations"]}, {"Visible event", "Second public event"})
        self.assertEqual(response.data["submissions"]["count"], 2)
        self.assertNotIn("Draft event", str(response.data["submissions"]))
